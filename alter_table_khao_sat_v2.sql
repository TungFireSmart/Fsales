-- =====================================================================
-- Migration v2 cho sale_lead_khao_sat
-- 1. Đổi nguon_nuoc (VARCHAR single) → nguon_nuoc_json (TEXT, multi-choice)
-- 2. Tách nguoi_quyet_dinh + nguoi_tiep_don thành 3 cột × 2 người
-- Cách chạy: python run_sql_file.py alter_table_khao_sat_v2.sql
-- =====================================================================

-- 1. Multi-choice cho nguồn nước (giữ cột cũ làm fallback)
ALTER TABLE sale_lead_khao_sat
    ADD COLUMN IF NOT EXISTS nguon_nuoc_json TEXT DEFAULT NULL
    COMMENT 'JSON array: ["duong_ong","be_chua","song_ho"]';

-- 2. Người ra quyết định — tách 3 cột
ALTER TABLE sale_lead_khao_sat
    ADD COLUMN IF NOT EXISTS qd_ten        VARCHAR(120) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS qd_chuc_vu    VARCHAR(120) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS qd_sdt        VARCHAR(30)  DEFAULT NULL;

-- 3. Người tiếp đón — tách 3 cột
ALTER TABLE sale_lead_khao_sat
    ADD COLUMN IF NOT EXISTS td_ten        VARCHAR(120) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS td_chuc_vu    VARCHAR(120) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS td_sdt        VARCHAR(30)  DEFAULT NULL;

-- 4. Lưu file_id Google Drive cho từng tài liệu KH upload
-- (đè lên tai_lieu_json — thêm cấu trúc: { "gp_xay_dung": { "checked": true, "drive_id": "..." } })
-- KHÔNG cần ALTER, chỉ thay đổi cấu trúc JSON trong cùng cột.
