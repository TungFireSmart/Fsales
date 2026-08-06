-- =====================================================================
-- Migration v4.5 — bổ sung cột quan_ly_sdt (tách Người quản lý → tên + SĐT)
-- Cách chạy: python run_sql_file.py alter_table_khao_sat_v4_5.sql
-- =====================================================================

ALTER TABLE sale_lead_khao_sat
    ADD COLUMN IF NOT EXISTS quan_ly_sdt VARCHAR(30) DEFAULT NULL
        COMMENT 'SĐT người quản lý trực tiếp cơ sở';
