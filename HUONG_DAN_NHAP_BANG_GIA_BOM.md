# Hướng dẫn nhập bảng giá bơm chữa cháy vào DB Fsales

## 🎯 Mục tiêu

Nhập danh mục bơm chữa cháy (Affetti / Pentax / Wilo / Grundfos...) từ file PDF hoặc Excel của nhà cung cấp vào **bảng `gia_tong_hop`** trong DB MySQL Fsales, đồng thời cập nhật **`bom_catalog.json`** để app Tư vấn PCCC có thể gợi ý model phù hợp với Q-H tính toán.

---

## 📋 Schema bảng `gia_tong_hop`

```sql
ten_san_pham   TEXT        -- Tên đầy đủ (phải chứa Q-H-kW theo quy ước, xem mục Quy ước)
model          VARCHAR     -- Mã model nhà sản xuất (vd "AFT40-200/7.5")
nhan_hieu      VARCHAR     -- Hãng (chữ HOA: AFFETTI / PENTAX / WILO...)
xuat_xu        VARCHAR     -- Quốc gia ("Việt Nam", "Italy", "Đức"...)
don_vi         VARCHAR     -- Đơn vị tính ("Cụm" cho bơm chính; "Bộ" cho bơm bù áp)
gia_dau_vao    BIGINT      -- Giá vốn = giá NCC báo (VNĐ, số nguyên không phẩy)
gia_ban_le     BIGINT      -- Giá bán lẻ = gia_dau_vao × 1.5 (markup 150%)
vat            INT         -- % VAT (mặc định 8)
nhan_cong      INT         -- Phí nhân công lắp đặt (mặc định 0 cho bơm,
                           --   sales sẽ nhập riêng theo dự án)
```

### ⚠️ Quy ước giá QUAN TRỌNG

- `gia_dau_vao` (cột "giá đầu vào" / giá vốn) = **giá NCC báo trong PDF/Excel** (chưa VAT)
- `gia_ban_le` = `gia_dau_vao × 1.5` (lãi 50%, làm tròn integer)
- Cả 2 đều bắt buộc — không bỏ trống `gia_dau_vao`

---

## 📝 Quy ước đặt tên `ten_san_pham`

App Tư vấn PCCC parse tên SP để biết Q-H-kW. **Đặt tên theo đúng format này**:

```
<Loại nhóm> <HÃNG> <model> <kW>kW Q=<min>-<max> m³/h H=<min>-<max> m
```

### Ví dụ chuẩn (Affetti):

| Loại | Tên đầy đủ |
|---|---|
| Liền trục 2900 RPM | `Cụm bơm điện liền trục 2900 RPM AFFETTI AFT40-200/7.5 7.5kW Q=9-42 m³/h H=40.0-57.7 m` |
| Rời trục 2900 RPM | `Cụm bơm điện rời trục 2900 RPM AFFETTI AF80-250/45 45.0kW Q=96-227 m³/h H=58.8-80.0 m` |
| Diesel 3000 RPM | `Cụm bơm diesel 3000 RPM AFFETTI AF40-200/7.5 9.0kW Q=9-42 m³/h H=40.0-57.7 m` |
| Bù áp | `Bơm bù áp AFFETTI AV4-13 2.2kW Q=1.2-7.2 m³/h H=29.0-85.0 m` |
| Đa tầng inox | `Bơm điện đa tầng AFFETTI AVS5-24 4.0kW Q=2.5-8.5 m³/h H=75.0-156.0 m` |

**Loại nhóm hợp lệ:**
- `Cụm bơm điện liền trục 2900 RPM` (≤ 37kW, motor + đầu bơm liền)
- `Cụm bơm điện rời trục 2900 RPM` (≥ 45kW, dùng khớp nối)
- `Cụm bơm diesel 3000 RPM` (bơm dự phòng chạy dầu)
- `Bơm bù áp` (jockey pump, công suất nhỏ)
- `Bơm điện đa tầng` (multistage pump)

---

## 📊 Cấu trúc bảng giá nhà cung cấp (Affetti — file PDF)

File PDF có **5 mục La Mã** (I, II, III, IV, V), mỗi mục là 1 loại nhóm. Mỗi dòng dữ liệu có 6 cột:

```
STT | Công suất (HP/kW) | Model động cơ | Model đầu bơm | Q range | H range | Giá
```

**Ví dụ dòng PDF:**
```
1  10HP/7.5KW  TP132S2-2  AFT40-200/7.5  9 - 42  57.7 - 40  8,500,000
```

→ Parse thành:
- model: `AFT40-200/7.5`
- kw: `7.5` (lấy từ phần sau "/")
- q_min=9, q_max=42 (m³/h)
- h_min=40, h_max=57.7 (m) — Q tăng → H giảm nên min/max đảo
- gia: 8500000

**Diesel có thêm prefix** (Kiểu khiêng tay / 12V acquy / 24V acquy) trước model động cơ — bỏ qua khi parse.

---

## 🔄 Quy trình thực hiện

### Bước 1 — Đọc file PDF

Dùng `pypdf` hoặc tương đương đọc text từ PDF. Cần regex:

```regex
(AFT\S+|AF\S+|AVS\S+|AV\S+)\s+([\d.,]+)\s*[-–]\s*([\d.,]+)\s+([\d.,]+)\s*[-–]\s*([\d.,]+)\s+([\d.,]+)
```

Group 1 = model, 2-3 = Q range, 4-5 = H range, 6 = giá.

Lấy kW theo thứ tự ưu tiên:
1. Số sau dấu `/` trong model (vd `AFT40-200/7.5` → 7.5)
2. Match `(\d+\.?\d*)\s*[Kk][Ww]` trong context 100 ký tự trước model

### Bước 2 — Tách section

Tách content thành 5 section bằng regex matching:
- `I MÁY BƠM ĐIỆN LIỀN TRỤC` → `Cụm bơm điện liền trục 2900 RPM`
- `II MÁY BƠM ĐIỆN RỜI TRỤC` → `Cụm bơm điện rời trục 2900 RPM`
- `III MÁY BƠM DIESEL` → `Cụm bơm diesel 3000 RPM`
- `IV MÁY BƠM BÙ ÁP` → `Bơm bù áp`
- `V MÁY BƠM ĐIỆN ĐA TẦNG` → `Bơm điện đa tầng`

### Bước 3 — Sinh SQL INSERT

Với mỗi model parsed, sinh dòng INSERT (lưu ý có **CẢ 2 cột giá**):

```sql
INSERT INTO gia_tong_hop
  (ten_san_pham, model, nhan_hieu, xuat_xu, don_vi,
   gia_dau_vao, gia_ban_le, vat, nhan_cong)
VALUES (
  '<ten_dung_quy_uoc>',
  '<model>',
  'AFFETTI',
  'Việt Nam',
  'Cụm',           -- 'Bộ' cho bù áp
  <gia_NCC>,       -- giá NCC báo trong PDF (chưa VAT)
  <gia_NCC * 1.5>, -- gia_ban_le = giá NCC × 1.5, làm tròn int
  8,
  0
);
```

**Lưu ý SQL:**
- Escape dấu nháy đơn trong tên: `'` → `''`
- KHÔNG có dấu phẩy ngăn cách trong số (8500000, không phải 8,500,000)
- `gia_ban_le = round(gia_dau_vao × 1.5)` — markup 150%
- Chữ "Cụm" dùng cho 4 loại bơm chính; chỉ "Bơm bù áp" dùng "Bộ"

**Ví dụ thực tế** (AFFETTI AFT40-200/7.5, giá NCC = 8.500.000):
```sql
INSERT INTO gia_tong_hop (ten_san_pham, model, nhan_hieu, xuat_xu, don_vi,
                          gia_dau_vao, gia_ban_le, vat, nhan_cong)
VALUES ('Cụm bơm điện liền trục 2900 RPM AFFETTI AFT40-200/7.5 7.5kW Q=9-42 m³/h H=40.0-57.7 m',
        'AFT40-200/7.5', 'AFFETTI', 'Việt Nam', 'Cụm',
        8500000, 12750000, 8, 0);
```

### Bước 4 — Cập nhật `bom_catalog.json`

File đã có sẵn ở `D:\Fsales_PCCC\bom_catalog.json`. Cấu trúc:

```json
{
  "_meta": {
    "hang": "AFFETTI",
    "nguon": "HCL Group",
    "ngay": "01/07/2025"
  },
  "lien_truc_2900": [
    {
      "model": "AFT40-200/7.5",
      "kw": 7.5,
      "q_min": 9.0,
      "q_max": 42.0,
      "h_min": 40.0,
      "h_max": 57.7,
      "gia": 8500000
    },
    ...
  ],
  "roi_truc_2900": [...],
  "diesel_3000": [...],
  "bu_ap": [...],
  "da_tang": [...]
}
```

**Khi thêm hãng mới (Pentax, Wilo...):**
- Nếu chưa có file riêng cho hãng đó → tạo `bom_catalog_<hang>.json` (vd `bom_catalog_pentax.json`)
- Hoặc merge vào file chính dưới key prefix tên hãng: `pentax_lien_truc_2900`, `pentax_roi_truc_2900`, ...
- Cập nhật `_meta` để app biết hãng

### Bước 5 — Chạy SQL vào DB

```bash
mysql -h <host> -u <user> -p <db_name> < insert_bom_<hang>_<YYYYMMDD>.sql
```

### Bước 6 — Verify

Sau khi nhập:

```sql
-- Đếm số SP đã nhập
SELECT COUNT(*), nhan_hieu FROM gia_tong_hop
WHERE ten_san_pham LIKE '%bơm%' GROUP BY nhan_hieu;

-- Xem 5 SP mẫu
SELECT ten_san_pham, model, gia_ban_le FROM gia_tong_hop
WHERE nhan_hieu = 'AFFETTI' LIMIT 5;
```

Mở app Tư vấn PCCC → tab Báo giá → click dòng "Cụm bơm..." → nhấn "Đổi model" → dialog phải hiện:
- 💡 **Top 3 gợi ý** (từ `bom_catalog.json` — theo Q-H-N tính từ TCVN 7336)
- Danh sách SP từ catalog Fsales (đã import bằng SQL)

---

## ⚠️ Lưu ý khi xử lý

1. **Giá đã loại VAT** — không cộng VAT vào `gia_ban_le`
2. **Một số diesel model có 2 giá** (khiêng tay vs 12V/24V acquy) — giữ cả 2 dòng, phân biệt qua `model` không đổi nhưng tên `ten_san_pham` thêm hậu tố `(khiêng tay)` / `(12V acquy)` / `(24V acquy)`
3. **kW < 1 hoặc > 300** → cảnh báo, có thể parse lỗi
4. **H_min/H_max** trong PDF có thể đảo (vì Q tăng → H giảm) — luôn `h_min = min(h1,h2)`, `h_max = max(h1,h2)`
5. **Bỏ qua dòng STT trùng** — nếu cùng `model` + `gia` đã có thì không insert lại

---

## 📂 File tham chiếu trên repo

| File | Mục đích |
|---|---|
| `D:\Fsales_PCCC\bom_catalog.json` | JSON metadata Affetti đã có sẵn (56 model) — xem làm mẫu |
| `D:\Fsales_PCCC\insert_bom_affetti_20260617.sql` | SQL Affetti đã có sẵn — xem format INSERT mẫu |
| `D:\Fsales_PCCC\import_bom_catalog.py` | Tool Python parse PDF/Excel (đã có sẵn — có thể chạy hoặc đọc tham khảo logic) |
| `D:\Fsales_PCCC\pccc_rules.py` (hàm `goi_y_bom`) | App đọc `bom_catalog.json` để gợi ý top 3 model |
| `D:\Fsales_PCCC\tu_van_pccc.py` (hàm `_doi_model_dialog`) | UI hiển thị gợi ý + danh sách catalog Fsales |

---

## ✅ Checklist trước khi nộp kết quả

- [ ] File SQL sinh ra có syntax-clean (mỗi INSERT 1 dòng, kết thúc bằng `;`)
- [ ] Số INSERT = số dòng dữ liệu trong PDF (Affetti = 56)
- [ ] Tên SP đúng format quy ước (chứa kW, Q range, H range)
- [ ] `model` chính xác (copy nguyên ký tự + dấu trong PDF)
- [ ] `nhan_hieu` ĐỒNG NHẤT một tên hãng chữ HOA (không lẫn lộn AFFETTI / Affetti / affetti)
- [ ] `bom_catalog.json` valid JSON, cấu trúc đúng key (`lien_truc_2900`, `roi_truc_2900`, `diesel_3000`, `bu_ap`, `da_tang`)
- [ ] `q_min ≤ q_max`, `h_min ≤ h_max`
- [ ] Test query app: mở Tư vấn PCCC → click "Đổi model" cho cụm bơm → thấy SP mới
