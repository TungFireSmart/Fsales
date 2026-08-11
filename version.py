"""
Phiên bản ứng dụng — NGUỒN SỰ THẬT DUY NHẤT.

Trước 6/8/2026 số này nằm cứng trong main.py (`self.app_version = '3.0.21'`),
rất dễ quên bump khi phát hành ⇒ bộ cài mới nhưng app vẫn báo số cũ,
và auto-update so sánh sai nên tưởng "đã mới nhất".

QUY TRÌNH PHÁT HÀNH — xem docs/HUONG-DAN-PHAT-HANH.md
  1. Sửa APP_VERSION ở đây
  2. Sửa AppVersion trong file .iss của Inno Setup cho khớp
  3. Build .exe → build bộ cài → đẩy manifest.json lên repo Fsales_update
"""

APP_VERSION = "3.0.24"
