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
CREATE_NEW_CONSOLE = 0x00000010

# 🔴 BÀI HỌC 11/8/2026 — VÌ SAO KHÔNG DÙNG DETACHED_PROCESS
# Bản trước chạy .bat bằng DETACHED_PROCESS kèm chú thích "cố ý hiện console".
# Sai cờ: DETACHED_PROCESS nghĩa là tiến trình KHÔNG CÓ CONSOLE NÀO CẢ.
# Cờ để hiện cửa sổ console là CREATE_NEW_CONSOLE. Hậu quả dây chuyền đo được
# trên máy anh Tùng ngày 11/8/2026 (bản 3.0.22 → 3.0.23):
#   · `timeout /t 1` cần console ⇒ lỗi ngay ⇒ vòng chờ 60 nhịp xong trong vài ms
#     thay vì 60 giây ⇒ chạy bộ cài khi Fsales.exe còn sống, file còn bị khoá.
#   · Bộ cài PrivilegesRequired=admin cần hộp thoại UAC ⇒ không lên được.
#   · Thất bại thì .bat rơi vào `pause` ⇒ treo vĩnh viễn KHÔNG CÓ CỬA SỔ NÀO
#     để người dùng thấy. Triệu chứng: "bấm OK rồi không thấy gì xảy ra".
# Dấu vết để lại: %TEMP%\fsales-update\capnhat.bat còn nguyên (dòng cuối của nó
# là lệnh tự xoá) và KHÔNG có install.log (Inno tạo log ngay khi khởi động).

# 🔴 PHẢI KHỚP với AppId trong release/FsalesInstaller-*.iss
# (đã xác minh 6/8/2026: giống nhau qua cả 15 bản .iss từ 3.0.2 → 3.0.22).
# Đổi AppId trong .iss mà quên đổi ở đây ⇒ không đọc được thư mục cài
# đã đăng ký, updater lui về thư mục đang chạy.
APP_ID = "B210A5E9-4E37-4D65-A91F-56F3B05B7E09"
APP_EXE_NAME = "Fsales.exe"

# Mã thoát của Inno Setup — để báo lỗi cho ra hồn thay vì "mã lỗi 1223"
MA_LOI_INNO = {
    1: "Bộ cài bị lỗi khi khởi tạo.",
    2: "Người dùng bấm Huỷ trước khi cài.",
    3: "Lỗi nội bộ khi chuẩn bị cài.",
    5: "Người dùng bấm Huỷ giữa chừng.",
    6: "Tiến trình cài bị dừng bằng mã lệnh.",
    8: "Cần khởi động lại máy để cài tiếp.",
    1223: "Bạn đã từ chối cấp quyền Administrator (cửa sổ UAC). "
          "Bộ cài FSales bắt buộc phải chạy với quyền quản trị.",
}

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

    def _thu_muc_dang_chay(self):
        if getattr(sys, 'frozen', False):
            return os.path.dirname(os.path.abspath(sys.executable))
        return self.app_dir

    def _thu_muc_da_dang_ky(self):
        """
        Đọc thư mục cài ĐÃ ĐĂNG KÝ của Inno Setup từ Registry.

        VÌ SAO KHÔNG DÙNG THƯ MỤC ĐANG CHẠY:
        Trên máy nhân viên từng tồn tại các bản sao lạc (shortcut cũ
        `Fsales_2024`, `Fire_Smart` — xem ghi chú phát hành bản 3.0.10).
        Nếu người dùng lỡ mở một bản sao lạc rồi ta cài đè vào chính chỗ
        đó, hai bản sẽ mãi mãi tồn tại song song và bản "chính" không bao
        giờ được cập nhật.

        Registry gắn với AppId nên nó là chỗ DUY NHẤT biết đâu là bản cài
        chính thức. Cài vào đó, rồi mở lại đúng nó ⇒ mọi máy hội tụ về
        một bản, dù người dùng bấm vào shortcut nào.

        Không đọc được thì lui về thư mục đang chạy (hành vi an toàn cũ).
        """
        if os.name != 'nt':
            return None
        try:
            import winreg
        except ImportError:
            return None

        khoa = (r"SOFTWARE\Microsoft\Windows\CurrentVersion"
                r"\Uninstall\{" + APP_ID + r"}_is1")

        for goc, co in ((winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_64KEY),
                        (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_32KEY),
                        (winreg.HKEY_CURRENT_USER, 0)):
            try:
                with winreg.OpenKey(goc, khoa, 0, winreg.KEY_READ | co) as k:
                    duong_dan, _ = winreg.QueryValueEx(k, "InstallLocation")
                    duong_dan = (duong_dan or '').strip().rstrip('\\')
                    if duong_dan and os.path.isdir(duong_dan):
                        return duong_dan
            except OSError:
                continue
        return None

    def _thu_muc_cai(self):
        """Nơi sẽ cài: ưu tiên bản đã đăng ký, không có thì thư mục đang chạy."""
        return self._thu_muc_da_dang_ky() or self._thu_muc_dang_chay()

    def _duong_dan_exe(self):
        """
        Đường dẫn exe sẽ MỞ LẠI sau khi cài — phải nằm trong thư mục vừa
        cài, KHÔNG phải sys.executable. Mở lại sys.executable nghĩa là mở
        lại đúng bản sao lạc vừa bị bỏ qua ⇒ "cài xong vẫn chạy bản cũ".
        """
        thu_muc = self._thu_muc_cai()
        if not thu_muc:
            return ''
        ten = (os.path.basename(sys.executable)
               if getattr(sys, 'frozen', False) else APP_EXE_NAME)
        return os.path.join(thu_muc, ten)

    @staticmethod
    def _ps_chuoi(s: str) -> str:
        """Bọc chuỗi vào dấu nháy đơn kiểu PowerShell (nháy đơn nhân đôi để thoát)."""
        return "'" + str(s).replace("'", "''") + "'"

    def _viet_ps1(self, installer_path: str, thu_muc_cai: str, log: str) -> str:
        """
        Sinh file PowerShell chạy bộ cài VỚI QUYỀN ADMIN.

        VÌ SAO TÁCH RA FILE .ps1 RIÊNG THAY VÌ NHÉT VÀO .bat:
        Bộ cài có `PrivilegesRequired=admin`, phải xin UAC. Cách chắc chắn hiện
        được hộp thoại UAC là `Start-Process -Verb RunAs`. Nhưng nhét cả câu
        lệnh PowerShell vào một dòng `.bat` thì dấu nháy kép bị cmd.exe nuốt
        trước khi tới PowerShell — nguồn lỗi kinh điển. Ghi ra file .ps1 rồi
        gọi bằng `-File` là hết sạch chuyện thoát ký tự.

        Người dùng bấm "No" ở UAC ⇒ Start-Process ném ngoại lệ ⇒ trả 1223,
        khớp với bảng MA_LOI_INNO để .bat báo cho ra hồn.

        ⚠️ .bat gọi file này KHÔNG chạy với quyền admin. Cố ý: chỉ mỗi bộ cài
        được nâng quyền, còn lệnh mở lại app ở bước sau vẫn chạy quyền thường.
        Nếu nâng quyền cả .bat thì Fsales.exe mở lại sẽ chạy dưới quyền
        Administrator suốt phiên đó — không cần thiết và dễ sinh chuyện lạ.
        """
        doi_so = list(INNO_FLAGS) + [f'/DIR={thu_muc_cai}', f'/LOG={log}']
        ds = ", ".join(self._ps_chuoi(x) for x in doi_so)

        ps = [
            "$ErrorActionPreference = 'Stop'",
            f"$boCai = {self._ps_chuoi(installer_path)}",
            f"$doiSo = @({ds})",
            "try {",
            "    $p = Start-Process -FilePath $boCai -ArgumentList $doiSo "
            "-Verb RunAs -Wait -PassThru",
            "    exit $p.ExitCode",
            "} catch {",
            "    Write-Host $_.Exception.Message",
            "    exit 1223",
            "}",
        ]
        ps1_path = os.path.join(
            tempfile.gettempdir(), 'fsales-update', 'chaycai.ps1')
        with open(ps1_path, 'w', encoding='utf-8') as f:
            f.write("\r\n".join(ps))
        return ps1_path

    def launch_installer(self, installer_path: str):
        """
        Sinh .bat trung gian rồi chạy trong CỬA SỔ CONSOLE RIÊNG.

        .bat làm đúng thứ tự sống còn:
          1. chờ tiến trình app (theo PID) chết hẳn  ← bản 3.0.22 hỏng ở đây
          2. gọi .ps1 chạy bộ cài với quyền admin (UAC), chờ cài xong
          3. mở lại app từ đúng thư mục vừa cài

        🔴 KHÔNG dùng `timeout` trong vòng chờ. `timeout.exe` cần handle input
        của console; hễ console thiếu hoặc stdin bị chuyển hướng là nó chết ngay
        ("ERROR: Input redirection is not supported") và vòng chờ 60 giây co lại
        còn vài mili giây ⇒ chạy bộ cài khi Fsales.exe còn đang khoá file.
        `ping -n 2 127.0.0.1` đợi ~1 giây, có trên mọi máy Windows, không cần
        console. (Bài học 11/8/2026.)
        """
        if not installer_path or not os.path.exists(installer_path):
            raise FileNotFoundError(f'Không tìm thấy bộ cài: {installer_path}')

        thu_muc_cai = self._thu_muc_cai()
        exe = self._duong_dan_exe()
        pid = os.getpid()
        log = os.path.join(tempfile.gettempdir(), 'fsales-update', 'install.log')

        ps1 = self._viet_ps1(installer_path, thu_muc_cai, log)
        bat_path = os.path.join(tempfile.gettempdir(), 'fsales-update', 'capnhat.bat')

        dong = [
            '@echo off',
            'title Cap nhat FSales',
            'echo.',
            'echo   ===================================',
            'echo   DANG CAP NHAT FSALES - VUI LONG DOI',
            'echo   ===================================',
            'echo.',
            'echo   Se hien cua so xin quyen Administrator.',
            'echo   Hay bam "Yes" thi ban moi duoc cai.',
            'echo.',
            '',
            f'rem 1) Cho tien trinh FSales (PID {pid}) thoat han',
            'set /a _dem=0',
            ':cho',
            f'tasklist /FI "PID eq {pid}" 2>nul | find "{pid}" >nul',
            'if errorlevel 1 goto thoat_xong',
            'set /a _dem+=1',
            'if %_dem% GEQ 60 goto thoat_xong',
            'ping -n 2 127.0.0.1 >nul',
            'goto cho',
            ':thoat_xong',
            '',
            'echo   Dang cai dat...',
            'rem 2) Chay bo cai voi quyen admin, cai vao THU MUC DA DANG KY',
            f'powershell -NoProfile -ExecutionPolicy Bypass -File "{ps1}"',
            'set _kq=%ERRORLEVEL%',
            '',
            'rem 3) Mo lai app tu chinh thu muc vua cai',
            'if "%_kq%"=="0" goto ok',
            '',
            'echo.',
            'echo   *** CAP NHAT THAT BAI - ma loi %_kq% ***',
            'if "%_kq%"=="1223" echo   Ban da bam "No" o cua so quyen Administrator.',
            'if "%_kq%"=="5" echo   Ban da bam Huy giua chung.',
            f'echo   Nhat ky chi tiet: {log}',
            'echo.',
            'echo   Phan mem cu van dung duoc binh thuong.',
            'pause',
            'goto het',
            '',
            ':ok',
        ]
        if exe:
            dong += [
                f'if exist "{exe}" (',
                f'  start "" "{exe}"',
                ') else (',
                f'  echo   Khong tim thay "{exe}" sau khi cai.',
                '  pause',
                ')',
            ]
        dong += ['', ':het', 'del "%~f0" >nul 2>&1']

        # Ghi ANSI-an-toan: .bat chi chua ky tu khong dau nen khong lo
        # lech bang ma (cmd.exe mac dinh khong doc UTF-8).
        with open(bat_path, 'w', encoding='ascii', errors='replace') as f:
            f.write("\r\n".join(dong))

        # 🔴 CREATE_NEW_CONSOLE, KHONG PHAI DETACHED_PROCESS.
        # Bo cai doi quyen Administrator nen Windows se hien hop thoai UAC;
        # con .bat thi can console that de `ping`, `pause`, `echo` chay dung.
        # DETACHED_PROCESS = khong co console nao ca ⇒ ca hai deu gay.
        # (Xem khoi chu thich dau file — bai hoc 11/8/2026.)
        subprocess.Popen(
            ['cmd.exe', '/c', bat_path],
            close_fds=True,
            creationflags=CREATE_NEW_CONSOLE,
        )
        return bat_path
