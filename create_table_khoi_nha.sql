-- =====================================================================
-- Bảng sale_lead_khoi_nha: từng khối nhà của cơ sở (PC01 mục II.2)
-- 1 lead có 0..n khối nhà. Nếu cơ sở 1 khối → auto sync với schema chính.
-- Cách chạy: python run_sql_file.py create_table_khoi_nha.sql
-- =====================================================================

CREATE TABLE IF NOT EXISTS sale_lead_khoi_nha (
    id              INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    sale_lead_id    INT          NOT NULL COMMENT 'FK → sale_lead.id',
    stt             INT          DEFAULT 0    COMMENT 'Số thứ tự khối nhà trong cơ sở',
    ten_khoi        VARCHAR(120) DEFAULT NULL COMMENT 'Tên khối nhà (VD: Khối A, Khu hành chính)',
    dt_xay_dung     DECIMAL(12,2) DEFAULT 0   COMMENT 'Diện tích xây dựng (m²)',
    so_tang_noi     INT          DEFAULT 0    COMMENT 'Số tầng nổi',
    so_tang_ham     INT          DEFAULT 0    COMMENT 'Số tầng hầm',
    bac_chiu_lua    VARCHAR(5)   DEFAULT NULL COMMENT 'Bậc chịu lửa (I, II, III, IV, V)',
    cong_nang       VARCHAR(255) DEFAULT NULL COMMENT 'Công năng sử dụng khối nhà',
    so_loi_thoat    INT          DEFAULT 0    COMMENT 'Số lối thoát nạn',
    ghi_chu         TEXT         DEFAULT NULL COMMENT 'Ghi chú khác',
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_lead (sale_lead_id),
    CONSTRAINT fk_khoi_nha_lead
        FOREIGN KEY (sale_lead_id) REFERENCES sale_lead(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Khối nhà trong cơ sở (PC01 mục II.2)';

-- Bảng phụ: từng KHU VỰC NGOÀI NHÀ (PC01 mục II.2, đoạn 3)
CREATE TABLE IF NOT EXISTS sale_lead_khu_vuc (
    id              INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    sale_lead_id    INT          NOT NULL,
    stt             INT          DEFAULT 0,
    ten_khu_vuc     VARCHAR(255) DEFAULT NULL COMMENT 'Tên khu vực ngoài nhà',
    dt_su_dung      DECIMAL(12,2) DEFAULT 0   COMMENT 'Diện tích sử dụng (m²)',
    day_chuyen_cn   TEXT         DEFAULT NULL COMMENT 'Dây chuyền công nghệ + vật tư dễ cháy nổ',
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_lead (sale_lead_id),
    CONSTRAINT fk_khu_vuc_lead
        FOREIGN KEY (sale_lead_id) REFERENCES sale_lead(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='Khu vực ngoài nhà (PC01 mục II.2)';
