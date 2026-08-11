#!/usr/bin/env python3
"""
Cổng kiểm cho BƯỚC 0 của `docs/RUNBOOK-PHAT-HANH-OPENCLAW.md`.

VÌ SAO CÓ FILE NÀY (11/8/2026)
------------------------------
Bản runbook đầu tiên viết cổng 0 bằng lệnh `cmd.exe`:
    git status --short | find /c /v ""
    git status --short | findstr /V /C:".venv/" /C:".idea/"
OpenClaw chạy và vỡ ngay:
    FIND: Parameter format not correct
    '/\' is not recognized as an internal or external command
Nguyên nhân: `find /c /v ""` và `findstr /C:"..."` là cú pháp riêng của cmd.exe,
hễ chạy qua PowerShell hoặc qua một lớp bọc có đổi cách thoát dấu nháy là hỏng.

🔴 BÀI HỌC: cổng kiểm cho agent tự chạy thì **không được** phụ thuộc vào shell.
Viết bằng Python — chạy đâu cũng như nhau, không có dấu nháy để hỏng.

DÙNG
----
    .venv\\Scripts\\python.exe kiem_tra_truoc_commit.py

Đọc dòng cuối cùng:
    ✅ SAN SANG COMMIT  → làm tiếp mục 0.4 của runbook
    ❌ DUNG             → dừng, báo anh Tùng, KHÔNG commit

Mã thoát: 0 = sẵn sàng · 1 = phải dừng.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Commit gần nhất được kỳ vọng. Khác đi nghĩa là đã có người commit trong lúc này
# ⇒ tình hình đổi, runbook không còn đúng nữa.
COMMIT_KY_VONG = "2f67523"
NHANH_KY_VONG = "main"

# Không bao giờ được đưa vào git. `.env` và `fsales_config.json` chứa credential
# CSDL sản xuất; `dist/` + `*.exe` từng làm repo Fsales_update phình lên 1,5 GB.
MAU_CAM = [
    ".venv/", "dist/", "build/", ".idea/", "__pycache__",
    ".exe", ".env", "fsales_config.json", "tools/",
    "token_drive.pickle", "google_drive_credential.json", "login.txt",
]

GOC = Path(__file__).resolve().parent
_loi = []


def bao(ok, mo_ta, chi_tiet=""):
    print(f"  {'✅' if ok else '❌'} {mo_ta}")
    if chi_tiet:
        for d in str(chi_tiet).rstrip().splitlines():
            print(f"       {d}")
    if not ok:
        _loi.append(mo_ta)
    return ok


def git(*args, index_tam=None):
    """Chạy git, trả (ma_thoat, stdout+stderr). Không qua shell ⇒ không lo dấu nháy."""
    moi_truong = os.environ.copy()
    if index_tam:
        moi_truong["GIT_INDEX_FILE"] = str(index_tam)
    kq = subprocess.run(
        ["git", *args], cwd=str(GOC), capture_output=True,
        text=True, encoding="utf-8", errors="replace", env=moi_truong,
    )
    return kq.returncode, (kq.stdout or "") + (kq.stderr or "")


def main():
    print("=" * 62)
    print("  KIEM TRA TRUOC KHI COMMIT — buoc 0 cua runbook phat hanh")
    print("=" * 62)

    # --- 1. Đúng repo, đúng nhánh ---------------------------------------
    print("\n[1] Repo va nhanh")
    ma, goc = git("rev-parse", "--show-toplevel")
    goc = goc.strip()
    bao(ma == 0 and goc != "", "Day la mot repo git", goc)
    ma, nhanh = git("rev-parse", "--abbrev-ref", "HEAD")
    nhanh = nhanh.strip()
    bao(nhanh == NHANH_KY_VONG, f"Dang o nhanh '{NHANH_KY_VONG}'", f"thuc te: {nhanh}")

    # --- 2. Commit gần nhất ---------------------------------------------
    print("\n[2] Commit gan nhat")
    ma, ra = git("log", "-1", "--format=%h %ad %s", "--date=short")
    ra = ra.strip()
    bao(ra.startswith(COMMIT_KY_VONG),
        f"Commit gan nhat van la {COMMIT_KY_VONG}", ra)
    if not ra.startswith(COMMIT_KY_VONG):
        print("       ⚠️  Da co nguoi commit trong luc nay. DUNG, bao anh Tung.")

    # --- 3. Khoá git còn sót --------------------------------------------
    print("\n[3] Khoa git con sot (.git/index.lock)")
    khoa = GOC / ".git" / "index.lock"
    if not khoa.exists():
        bao(True, "Khong co index.lock")
    else:
        co = khoa.stat().st_size
        tuoi = (time.time() - khoa.stat().st_mtime) / 60
        print(f"  ⚠️  CO index.lock: {co} byte, tao cach day {tuoi:.0f} phut")
        an_toan = (co == 0 and tuoi > 60)
        if an_toan:
            print("       Day la tan du cua tien trinh git chet do (0 byte, qua cu).")
            print("       Kiem tasklist khong co git.exe, dong PyCharm, roi xoa:")
            print(f"       del \"{khoa}\"")
        else:
            print("       KHONG duoc xoa: file khac 0 byte hoac vua moi tao.")
            print("       Co the git dang ghi that. DUNG, bao anh Tung.")
        bao(False, "Phai go index.lock roi chay lai script nay")

    # --- 4. .gitignore giữ được main.spec -------------------------------
    print("\n[4] .gitignore")
    ma, ra = git("check-ignore", "-v", "--no-index", "main.spec")
    bao("!main.spec" in ra,
        "main.spec KHONG bi ignore (dong phu dinh con tac dung)", ra.strip())
    if "*.spec" in ra and "!main.spec" not in ra:
        print("       ⚠️  .gitignore khong ho tro chu thich cuoi dong.")
        print("       Dong `!main.spec   # ...` bi hieu la ten file co ca chu thich.")

    # --- 5. git add -A sẽ kéo vào những gì ------------------------------
    print("\n[5] `git add -A` se dua nhung gi vao commit")
    print("    (chay tren mot BAN SAO cua vung cho — khong dung index that)")
    chi_muc = GOC / ".git" / "index"
    tam = Path(tempfile.gettempdir()) / "fsales-index-thu"
    dong_add = []
    try:
        shutil.copyfile(chi_muc, tam)
        ma, ra = git("add", "-A", "--dry-run", index_tam=tam)
        if ma != 0:
            bao(False, "Chay duoc `git add -A --dry-run`", ra.strip())
        else:
            dong_add = [d for d in ra.splitlines() if d.strip()]
            print(f"    -> {len(dong_add)} thao tac:")
            for d in dong_add:
                print(f"       {d}")
            print("    Luu y: KHONG co dong 'remove' la DUNG — ~11.000 lenh xoa")
            print("    .venv/, AI/, __pycache__ da nam san trong vung cho tu 6/8.")
            nguy_hiem = [d for d in dong_add
                         if any(m.lower() in d.lower() for m in MAU_CAM)]
            bao(not nguy_hiem,
                "Khong keo vao file nao thuoc danh sach cam",
                "\n".join(nguy_hiem) if nguy_hiem else "")
            if nguy_hiem:
                print("       🔴 .env / fsales_config.json chua mat khau CSDL san xuat.")
                print("       🔴 dist/ + *.exe ~600 MB se phinh lich su git vinh vien.")
    finally:
        for f in (tam, Path(str(tam) + ".lock")):
            try:
                f.unlink()
            except OSError:
                pass

    # --- 6. Có file thông điệp commit không -----------------------------
    print("\n[6] File thong diep commit")
    td = GOC / "docs" / "thong-diep-commit.txt"
    bao(td.exists(), f"Co {td.relative_to(GOC)}",
        "" if td.exists() else "Thieu file nay thi buoc 0.4 khong chay duoc")

    # --- KẾT LUẬN --------------------------------------------------------
    print("\n" + "=" * 62)
    if _loi:
        print("  ❌ DUNG — khong commit. Cac muc chua dat:")
        for e in _loi:
            print(f"     · {e}")
        print("\n  Chep nguyen van output nay gui anh Tung.")
        print("=" * 62)
        return 1
    print("  ✅ SAN SANG COMMIT")
    print("     Lam tiep muc 0.4 cua docs/RUNBOOK-PHAT-HANH-OPENCLAW.md")
    print("=" * 62)
    return 0


if __name__ == "__main__":
    sys.exit(main())
