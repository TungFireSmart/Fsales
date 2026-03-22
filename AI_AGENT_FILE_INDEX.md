# AI_AGENT_FILE_INDEX.md

## A) Entry points

- `main.py` — app bootstrap + login + màn hình quản lý lead.
- `order_handle.py` — xử lý đơn hàng (chốt đơn, lưu đơn, xuất kho).
- `quotation.py` — xử lý báo giá.
- `lead_handle.py` — xử lý lead.

## B) UI layer

- `UI/*.ui` — nguồn giao diện gốc (Qt Designer).
- `UI/*.py` — code generate từ `.ui`.
- `don_hang.py` (root) — file giao diện generate; coi là UI-only.

## C) Business/DB helpers

- `misc.py` — SQL helper + common utilities.
- `file_handle.py` — upload/download file liên quan lead (Google Drive).
- `stock_handle.py` — nghiệp vụ kho.
- `stock_logic.py`, `stock_ui_utils.py` — phụ trợ kho.

## D) AI integration

- `AI/` — các module AI (chat window, planner, safe executor, ontology,...)
- `openclaw_bridge_server.py` — cầu nối OpenClaw.

## E) Packaging / artifacts (không phải nơi ưu tiên sửa)

- `.venv/`
- `build/`
- `dist/`
- `installer/`
- `__pycache__/`

## F) File ưu tiên đọc khi làm chức năng trả lại hàng

1. `order_handle.py`
2. `stock_handle.py`
3. `misc.py`
4. `UI/don_hang.ui`
5. `UI/don_hang.py`
6. `don_hang.py` (root, đối chiếu generate state)

## G) Điểm dễ nhầm cần tránh

- Có 2 file tên `don_hang.py`:
  - `D:\Fsales_PCCC\don_hang.py`
  - `D:\Fsales_PCCC\UI\don_hang.py`
- Cả hai đều là code giao diện generate, **không phải business logic chính**.
- Nếu thấy khác nhau giữa 2 bản, ưu tiên lấy `UI/don_hang.ui` làm nguồn để regenerate thống nhất.
