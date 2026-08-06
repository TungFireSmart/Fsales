-- =====================================================================
-- Migration v3 cho sale_lead_khao_sat
-- 1. Tách Liên hệ kỹ thuật → 3 cột (lh_ten, lh_chuc_vu, lh_sdt)
-- 2. Thêm bkl_drive_info để lưu file bảng khối lượng đã upload
-- 3. Thêm kh_cty + kh_mst (snapshot tại thời điểm khảo sát)
-- Cách chạy: python run_sql_file.py alter_table_khao_sat_v3.sql
-- =====================================================================

ALTER TABLE sale_lead_khao_sat
    ADD COLUMN IF NOT EXISTS lh_ten        VARCHAR(120) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS lh_chuc_vu    VARCHAR(120) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS lh_sdt        VARCHAR(30)  DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS bkl_drive_info TEXT        DEFAULT NULL
        COMMENT 'Format: tenfile|file_id|mime — file bảng khối lượng KH cung cấp',
    ADD COLUMN IF NOT EXISTS kh_cty        VARCHAR(255) DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS kh_mst        VARCHAR(30)  DEFAULT NULL;
