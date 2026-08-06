"""
Tự động cập nhật FSales.

=====================================================================
 VÌ SAO VIẾT LẠI (6/8/2026)
=====================================================================
Anh Tùng báo hai triệu chứng:
  (a) tải bản mới xong vẫn phải cài lại bằng tay
  (b) đôi khi cài xong máy vẫn chạy bản cũ

Bản cũ có 5 lỗi dẫn tới đúng hai triệu chứng đó:

1. 🔴 CHẠY BỘ CÀI TRONG KHI APP CÒN SỐNG.
   `Popen(installer)` rồi `QApplication.quit()` ngay lập tức. Nhưng quit()
   không tức thời, và Windows vẫn KHOÁ `Fsale.exe` đang chạy. Inno Setup
   không ghi đè được file bị khoá ⇒ hoặc báo lỗi, hoặc cài thiếu.

2. 🔴 KHÔNG TRUYỀN /DIR.
   Bộ cài dùng thư mục mặc định của nó. Nếu máy nhân viên trước đây cài ở
   chỗ khác thì sinh ra HAI bản song song, shortcut cũ vẫn trỏ bản cũ.
   ⇒ Đây là nguyên nhân số một của "cài xong vẫn chạy bản cũ".

3. 🔴 KHÔNG CHẠY IM LẶNG.
   Không có `/SILENT`, nên bộ cài hiện wizard bắt bấm Next từng bước.
   ⇒ Đây là "vẫn phải cài đặt lại".

4. 🔴 TẢI ĐỒNG BỘ TRÊN LUỒNG GIAO DIỆN.
   `resp.read()` nuốt trọn ~70 MB vào RAM ngay trên luồng Qt chính.
   App đơ toàn bộ thời gian tải, người dùng tưởng treo nên tắt đi
   ⇒ file tải dở, bộ cài hỏng.

5. 🔴 KHÔNG KIỂM TRA TÍNH TOÀN VẸN.
   Không so kích thước, không so sha256. Tải thiếu vẫn đem đi chạy.

=====================================================================
 CÁCH LÀM MỚI
=====================================================================
  tải theo từng khối (có tiến trình, chạy luồng nền)
    → kiểm tra size + sha256 nếu manifest có khai báo
    → sinh một file .bat trung gian
    → app THOÁT
    → .bat chờ tiến trình app chết hẳn
    → chạy bộ cài /SILENT /DIR="đúng thư mục đang chạy"
    → mở lại app

MANIFEST hỗ trợ (2 khoá cuối là tuỳ chọn nhưng NÊN có):
{
  "version": "3.0.22",
  "installer_url": "https://.../FsaleSetup.exe",
  "notes": "...",
  "sha256": "abc123...",
  "size": 69753922
}
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from urllib.error import URLError, HTTPError

from PyQt6.QtCore import QRunnable, QObject, pyqtSignal

CREATE_NO_WINDOW = 0x08000000
DETACHED_PROCESS = 0x00000008

# Cờ Inno Setup:
#   /SILENT            chỉ hiện thanh tiến trình, không bắt bấm Next
#   /SUPPRESSMSGBOXES  không chặn bằng hộp thoại khi chạy im lặng
#   /NORESTART         không tự khởi động lại Windows
#   /CLOSEAPPLICATIONS   đóng ứng dụng đang khoá file
#   /NORESTARTAPPLICATIONS  không để Inno tự mở lại — .bat của ta lo việc đó
#
# ⚠️ Đúng tên cờ theo tài liệu Inno Setup 6. Truyền cờ lạ (ví dụ
# "/RESTARTAPPLICATIONS=no") sẽ làm bộ cài báo lỗi tham số rồi dừng.
INNO_FLAGS = [
    "/SILENT",
    "/SUPPRESSMSGBOXES",
    "/NORESTART",
    "/CLOSEAPPLICATIONS",
    "/NORESTARTAPPLICATIONS",
]


def _parse_version(v: str):
    parts = []
    for p in str(v).strip().split('.'):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def is_newer(remote_version: str, current_version: str) -> bool:
    return _parse_version(remote_version) > _parse_version(current_version)


# =====================================================================
#  TẢI Ở LUỒNG NỀN
# =====================================================================

class UpdateDownloadSignals(QObject):
    progress = pyqtSignal(int, int)   # đã tải, tổng cộng (byte)
    done = pyqtSignal(str)            # đường dẫn file bộ cài
    error = pyqtSignal(str)


class UpdateDownloadWorker(QRunnable):
    """
    Tải bộ cài mà KHÔNG làm đơ giao diện.
    Dùng với QThreadPool.globalInstance().start(worker) — cùng khuôn
    với login_worker.py vốn có sẵn trong dự án.
    """

    def __init__(self, updater, info: dict):
        super().__init__()
        self.updater = updater
        self.info = info
        self.signals = UpdateDownloadSignals()

    def run(self):
        try:
            path = self.updater.download_installer(
                self.info['installer_url'],
                expected_sha256=self.info.get('sha256'),
                expected_size=self.info.get('size'),
                progress_cb=lambda d, t: self.signals.progress.emit(d, t),
            )
            self.signals.done.emit(path)
        except Exception as e:
            self.signals.error.emit(str(e))


# =====================================================================
#  UPDATER
# =====================================================================

class AutoUpdater:
    def __init__(self, app_dir: str, current_version: str):
        self.app_dir = app_dir
        self.current_version = current_version
        p1 = os.path.join(app_dir, 'update_config.json')
        p2 = os.path.join(app_dir, '_internal', 'update_config.json')
        self.config_path = p1 if os.path.exists(p1) else p2

    # ---------------- manifest ----------------

    def _load_config(self):
        if not os.path.exists(self.config_path):
            return None
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _fetch_manifest(self, manifest_url: str):
        # Chống cache: GitHub raw có CDN, hay trả manifest cũ vài phút.
        # Đây cũng là một lý do khiến app "không thấy bản mới".
        sep = '&' if '?' in manifest_url else '?'
        url = f"{manifest_url}{sep}_t={int(time.time())}"
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'FSales-Updater/2.0',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
            },
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read().decode('utf-8-sig', errors='ignore')
        return json.loads(data)

    def get_manifest_info(self):
        cfg = self._load_config()
        if not cfg:
            return None

        manifest_url = (cfg.get('manifest_url') or '').strip()
        if not manifest_url:
            return None

        try:
            manifest = self._fetch_manifest(manifest_url)
        except (URLError, HTTPError, TimeoutError, json.JSONDecodeError):
            return None
        except Exception:
            return None

        remote_version = str(manifest.get('version', '')).strip()
        installer_url = str(manifest.get('installer_url', '')).strip()
        if not remote_version or not installer_url:
            return None

        return {
            'version': remote_version,
            'installer_url': installer_url,
            'notes': str(manifest.get('notes', '')).strip(),
            'sha256': str(manifest.get('sha256', '')).strip().lower() or None,
            'size': int(manifest.get('size') or 0) or None,
        }

    def check(self):
        info = self.get_manifest_info()
        if not info:
            return None
        if not is_newer(info['version'], self.current_version):
            return None
        return info

    # ---------------- tải ----------------

    def download_installer(self, installer_url: str, expected_sha256=None,
                           expected_size=None, progress_cb=None):
        """
        Tải theo từng khối 1 MB, báo tiến trình, kiểm tra toàn vẹn.
        Tải vào file .part rồi mới đổi tên — nửa chừng bị ngắt thì không
        để lại file .exe hỏng khiến lần sau tưởng đã tải xong.
        """
        thu_muc = os.path.join(tempfile.gettempdir(), 'fsales-update')
        os.makedirs(thu_muc, exist_ok=True)
        dich = os.path.join(thu_muc, 'FsaleSetup.exe')
        tam = dich + '.part'

        req = urllib.request.Request(
            installer_url, headers={'User-Agent': 'FSales-Updater/2.0'})

        h = hashlib.sha256()
        da_tai = 0
        with urllib.request.urlopen(req, timeout=30) as resp:
            tong = int(resp.headers.get('Content-Length') or expected_size or 0)
            with open(tam, 'wb') as f:
                while True:
                    khoi = resp.read(1024 * 1024)
                    if not khoi:
                        break
                    f.write(khoi)
                    h.update(khoi)
                    da_tai += len(khoi)
                    if progress_cb:
                        progress_cb(da_tai, tong)

        # --- kiểm tra toàn vẹn ---
        if expected_size and da_tai != int(expected_size):
            os.remove(tam)
            raise IOError(
                f"File tải về không đủ: {da_tai} byte, cần {expected_size} byte")

        if expected_sha256:
            thuc_te = h.hexdigest()
            if thuc_te.lower() != expected_sha256.lower():
                os.remove(tam)
                raise IOError("File tải về sai mã kiểm tra sha256 — có thể hỏng "
                              "hoặc bị can thiệp giữa đường")

        if da_tai < 1024 * 1024:
            os.remove(tam)
            raise IOError(f"File tải về quá nhỏ ({da_tai} byte), chắc chắn hỏng")

        if os.path.exists(dich):
            os.remove(dich)
        os.rename(tam, dich)
        return dich

    # ---------------- cài ----------------

    def _thu_muc_cai(self):
        """
        Thư mục đang chạy app — truyền cho /DIR để bộ cài ĐÈ LÊN ĐÚNG CHỖ,
        thay vì đẻ ra bản thứ hai ở thư mục mặc định.
        """
        if getattr(sys, 'frozen', False):
            return os.path.dirname(os.path.abspath(sys.executable))
        return self.app_dir

    def _duong_dan_exe(self):
        if getattr(sys, 'frozen', False):
            return os.path.abspath(sys.executable)
        return ''

    def launch_installer(self, installer_path: str):
        """
        Sinh .bat trung gian rồi chạy tách rời.

        .bat làm đúng thứ tự sống còn:
          1. chờ tiến trình app (theo PID) chết hẳn  ← bản cũ THIẾU bước này
          2. chạy bộ cài im lặng, đè đúng thư mục
          3. mở lại app
        """
        if not installer_path or not os.path.exists(installer_path):
            raise FileNotFoundError(f'Không tìm thấy bộ cài: {installer_path}')

        thu_muc_cai = self._thu_muc_cai()
        exe = self._duong_dan_exe()
        pid = os.getpid()
        log = os.path.join(tempfile.gettempdir(), 'fsales-update', 'install.log')

        co = " ".join(INNO_FLAGS)
        bat_path = os.path.join(tempfile.gettempdir(), 'fsales-update', 'capnhat.bat')

        dong = [
            '@echo off',
            'chcp 65001 >nul',
            'echo Dang cap nhat FSales, vui long doi...',
            '',
            f'rem 1) Cho tien trinh FSales (PID {pid}) thoat han',
            'set /a _dem=0',
            ':cho',
            f'tasklist /FI "PID eq {pid}" 2>nul | find "{pid}" >nul',
            'if errorlevel 1 goto thoat_xong',
            'set /a _dem+=1',
            'if %_dem% GEQ 60 goto thoat_xong',
            'timeout /t 1 /nobreak >nul',
            'goto cho',
            ':thoat_xong',
            '',
            'rem 2) Chay bo cai im lang, DE LEN DUNG thu muc dang chay',
            f'"{installer_path}" {co} /DIR="{thu_muc_cai}" /LOG="{log}"',
            'set _kq=%ERRORLEVEL%',
            '',
            'rem 3) Mo lai app',
        ]
        if exe:
            dong += [
                'if "%_kq%"=="0" (',
                f'  start "" "{exe}"',
                ') else (',
                '  echo Cai dat that bai, ma loi %_kq%. Xem log: ' + log,
                '  pause',
                ')',
            ]
        dong += ['', 'del "%~f0" >nul 2>&1']

        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write("\r\n".join(dong))

        subprocess.Popen(
            ['cmd.exe', '/c', bat_path],
            close_fds=True,
            creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW,
        )
        return bat_path
