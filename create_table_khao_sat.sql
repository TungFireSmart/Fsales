-- =====================================================================
-- Bảng sale_lead_khao_sat — lưu dữ liệu khảo sát hiện trường
-- 1 lead = 1 row khảo sát (PRIMARY KEY = lead_id)
-- Cách chạy 1 lần:
--   python run_sql_file.py create_table_khao_sat.sql
-- =====================================================================

CREATE TABLE IF NOT EXISTS sale_lead_khao_sat (
    lead_id              INT          PRIMARY KEY,

    -- A. Thông tin chung công trình
    ten_cong_trinh       VARCHAR(255) DEFAULT NULL,
    dia_chi              TEXT         DEFAULT NULL,
    hinh_thuc_so_huu     VARCHAR(50)  DEFAULT NULL,  -- so_huu / thue / khac
    trang_thai           VARCHAR(50)  DEFAULT NULL,  -- thiet_ke / thi_cong / van_hanh
    ct_doc_lap           TINYINT(1)   DEFAULT NULL,  -- 1=độc lập, 0=một phần CT lớn
    cong_nang_k          VARCHAR(50)  DEFAULT NULL,

    -- B. Quy mô + kỹ thuật
    dt_san_tong          DOUBLE       DEFAULT NULL,
    so_tang_noi          INT          DEFAULT NULL,
    so_tang_ham          INT          DEFAULT NULL,
    cao_pccc             DOUBLE       DEFAULT NULL,
    bac_chiu_lua         VARCHAR(10)  DEFAULT NULL,  -- I/II/III/IV/V
    cap_nhc              VARCHAR(10)  DEFAULT NULL,  -- S0/S1/S2/S3
    hang_nguy_hiem       VARCHAR(10)  DEFAULT NULL,  -- A/B/C/D/E
    so_nguoi_du_kien     INT          DEFAULT NULL,
    kc_ct_ke_ben         DOUBLE       DEFAULT NULL,  -- m
    xe_cc_tiep_can       TINYINT(1)   DEFAULT NULL,

    -- C. Hạ tầng + hệ thống PCCC sẵn có
    nguon_nuoc           VARCHAR(50)  DEFAULT NULL,
    nguon_nuoc_chi_tiet  TEXT         DEFAULT NULL,
    nguon_dien           VARCHAR(50)  DEFAULT NULL,  -- 1_nguon / 2_nguon
    co_may_phat          TINYINT(1)   DEFAULT NULL,
    he_thong_sn_json     TEXT         DEFAULT NULL,  -- JSON 6 hệ × {da_co, tinh_trang, hang}

    -- D. Pháp lý + tài liệu
    tai_lieu_json        TEXT         DEFAULT NULL,  -- JSON checklist 10 loại
    lich_su_pccc         TEXT         DEFAULT NULL,

    -- E. Thương mại + đánh giá
    yc_kh                TEXT         DEFAULT NULL,
    ngan_sach            VARCHAR(50)  DEFAULT NULL,
    deadline             VARCHAR(100) DEFAULT NULL,
    nguoi_quyet_dinh     VARCHAR(255) DEFAULT NULL,
    lien_he_ky_thuat     VARCHAR(255) DEFAULT NULL,
    doi_thu_da_bao_gia   TINYINT(1)   DEFAULT NULL,
    doi_thu_ten          VARCHAR(255) DEFAULT NULL,
    danh_gia_sales       TEXT         DEFAULT NULL,
    buoc_tiep_theo       TEXT         DEFAULT NULL,

    -- Footer
    ngay_khao_sat        DATE         DEFAULT NULL,
    nguoi_khao_sat       VARCHAR(100) DEFAULT NULL,
    nguoi_tiep_don       VARCHAR(255) DEFAULT NULL,

    -- Audit
    created_at           DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at           DATETIME     DEFAULT CURRENT_TIMESTAMP
                         ON UPDATE CURRENT_TIMESTAMP,

    -- Foreign key (sale_lead.lead_id) — ON DELETE CASCADE để xóa lead → xóa khảo sát
    CONSTRAINT fk_klsks_lead FOREIGN KEY (lead_id)
        REFERENCES sale_lead(lead_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
