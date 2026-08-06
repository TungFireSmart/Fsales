-- =====================================================================
-- Migration v4 cho sale_lead_khao_sat
-- Bổ sung field cho 4 mẫu PC01-PC04 (NĐ 105/2025) + chuyển SSOT về tab Khảo sát
-- Cách chạy: python run_sql_file.py alter_table_khao_sat_v4.sql
-- =====================================================================

-- ============== A. Mở rộng schema CHÍNH (di chuyển từ cột trái) ==============
ALTER TABLE sale_lead_khao_sat
    -- Công năng + quy mô (trước đây ở cột trái)
    ADD COLUMN IF NOT EXISTS cong_nang_k        VARCHAR(20)  DEFAULT NULL COMMENT 'Mã công năng (CN1, CN2…) — SSOT từ Khảo sát',
    ADD COLUMN IF NOT EXISTS dt_san_tong        DECIMAL(12,2) DEFAULT 0  COMMENT 'Tổng diện tích sàn (m²) — SSOT',
    ADD COLUMN IF NOT EXISTS cao_pccc           DECIMAL(8,2) DEFAULT 0  COMMENT 'Chiều cao PCCC (m) — SSOT',
    ADD COLUMN IF NOT EXISTS so_tang_noi        INT          DEFAULT 0  COMMENT 'Số tầng nổi — SSOT',
    ADD COLUMN IF NOT EXISTS so_tang_ham        INT          DEFAULT 0  COMMENT 'Số tầng hầm — SSOT',
    ADD COLUMN IF NOT EXISTS dai_nha            DECIMAL(8,2) DEFAULT 0  COMMENT 'Chiều dài nhà (m)',
    ADD COLUMN IF NOT EXISTS rong_nha           DECIMAL(8,2) DEFAULT 0  COMMENT 'Chiều rộng nhà (m)',
    ADD COLUMN IF NOT EXISTS so_phong           INT          DEFAULT 0  COMMENT 'Số phòng (gian)',
    ADD COLUMN IF NOT EXISTS so_nguoi           INT          DEFAULT 0  COMMENT 'Số người / chỗ ngồi',
    ADD COLUMN IF NOT EXISTS so_chau            INT          DEFAULT 0  COMMENT 'Số cháu (mầm non)';

-- ============== B. Group A mở rộng — PC01 mục I (Thông tin chung) ==============
ALTER TABLE sale_lead_khao_sat
    ADD COLUMN IF NOT EXISTS nam_hoat_dong      INT          DEFAULT NULL COMMENT 'Năm đưa vào hoạt động',
    ADD COLUMN IF NOT EXISTS nganh_nghe         VARCHAR(255) DEFAULT NULL COMMENT 'Ngành nghề, lĩnh vực hoạt động',
    ADD COLUMN IF NOT EXISTS nguoi_quan_ly      VARCHAR(255) DEFAULT NULL COMMENT 'Tên cơ quan/tổ chức/cá nhân trực tiếp quản lý',
    ADD COLUMN IF NOT EXISTS dai_dien_pl_ten    VARCHAR(120) DEFAULT NULL COMMENT 'Họ tên người đại diện pháp luật',
    ADD COLUMN IF NOT EXISTS dai_dien_pl_sdt    VARCHAR(30)  DEFAULT NULL COMMENT 'SĐT người đại diện pháp luật',
    ADD COLUMN IF NOT EXISTS co_quan_cap_tren   VARCHAR(255) DEFAULT NULL COMMENT 'Cơ quan/tổ chức cấp trên',
    ADD COLUMN IF NOT EXISTS thanh_phan_kt      VARCHAR(20)  DEFAULT NULL COMMENT 'nha_nuoc/tap_the/tu_nhan/von_nuoc_ngoai',
    ADD COLUMN IF NOT EXISTS thuoc_dm_nguyhiem  TINYINT(1)   DEFAULT 0    COMMENT 'Thuộc danh mục cơ sở nguy hiểm cháy nổ',
    ADD COLUMN IF NOT EXISTS thuoc_dm_thamduyet TINYINT(1)   DEFAULT 0    COMMENT 'Thuộc danh mục dự án phải thẩm duyệt PCCC';

-- ============== C. Group B mở rộng — PC01 mục II.2-II.3 (Quy mô + giao thông CC) ==============
ALTER TABLE sale_lead_khao_sat
    ADD COLUMN IF NOT EXISTS dt_xay_dung        DECIMAL(12,2) DEFAULT 0   COMMENT 'Diện tích xây dựng — khác dt_san_tong',
    ADD COLUMN IF NOT EXISTS dgt_rong           DECIMAL(5,2)  DEFAULT 0   COMMENT 'Đường giao thông xe CC — rộng (m)',
    ADD COLUMN IF NOT EXISTS dgt_cao            DECIMAL(5,2)  DEFAULT 0   COMMENT 'Đường giao thông xe CC — cao thông thủy (m)',
    ADD COLUMN IF NOT EXISTS bai_do_xe_cc       TEXT          DEFAULT NULL COMMENT 'Vị trí bãi đỗ xe CC bên trong + bên ngoài';

-- ============== D. Group C mở rộng — PC01 mục II.4 + II.5 (Nguồn nước + điện chi tiết) ==============
ALTER TABLE sale_lead_khao_sat
    -- Bể CC
    ADD COLUMN IF NOT EXISTS so_be_cc           INT           DEFAULT 0   COMMENT 'Số lượng bể chứa nước CC',
    ADD COLUMN IF NOT EXISTS khoi_tich_be       DECIMAL(8,2)  DEFAULT 0   COMMENT 'Khối tích bể chứa (m³)',
    ADD COLUMN IF NOT EXISTS vi_tri_be          TEXT          DEFAULT NULL COMMENT 'Vị trí bể chứa + khả năng lấy nước',
    -- Trụ CC
    ADD COLUMN IF NOT EXISTS so_tru_cc          INT           DEFAULT 0   COMMENT 'Số trụ cấp nước CC',
    ADD COLUMN IF NOT EXISTS vi_tri_tru         TEXT          DEFAULT NULL COMMENT 'Vị trí trụ cấp nước CC',
    -- Máy phát
    ADD COLUMN IF NOT EXISTS mp_cong_suat_kva   DECIMAL(8,2)  DEFAULT 0   COMMENT 'Công suất máy phát (kVA)',
    ADD COLUMN IF NOT EXISTS mp_thoi_gian_chay_h DECIMAL(5,2) DEFAULT 0   COMMENT 'Thời gian máy phát chạy được (giờ)',
    -- Truyền tin báo cháy (NĐ 105 mới)
    ADD COLUMN IF NOT EXISTS truyen_tin_da_lap  TINYINT(1)    DEFAULT 0   COMMENT 'Đã lắp truyền tin báo cháy chưa',
    -- Phương tiện CC cơ giới
    ADD COLUMN IF NOT EXISTS co_xe_chua_chay    TINYINT(1)    DEFAULT 0   COMMENT 'Cơ sở có xe chữa cháy riêng',
    ADD COLUMN IF NOT EXISTS phuong_tien_cc_text TEXT         DEFAULT NULL COMMENT 'Mô tả phương tiện CC cơ giới';

-- ============== E. Group D mở rộng — PC01 mục II.1 (Văn bản pháp lý PCCC) ==============
ALTER TABLE sale_lead_khao_sat
    -- Văn bản thẩm duyệt thiết kế PCCC
    ADD COLUMN IF NOT EXISTS vb_thamduyet_so    VARCHAR(100)  DEFAULT NULL COMMENT 'Số văn bản thẩm duyệt thiết kế PCCC',
    ADD COLUMN IF NOT EXISTS vb_thamduyet_ngay  DATE          DEFAULT NULL COMMENT 'Ngày văn bản thẩm duyệt',
    ADD COLUMN IF NOT EXISTS vb_thamduyet_cq    VARCHAR(255)  DEFAULT NULL COMMENT 'Cơ quan ban hành VB thẩm duyệt',
    -- Văn bản chấp thuận nghiệm thu PCCC
    ADD COLUMN IF NOT EXISTS vb_nghiemthu_so    VARCHAR(100)  DEFAULT NULL COMMENT 'Số văn bản nghiệm thu PCCC',
    ADD COLUMN IF NOT EXISTS vb_nghiemthu_ngay  DATE          DEFAULT NULL COMMENT 'Ngày văn bản nghiệm thu',
    ADD COLUMN IF NOT EXISTS vb_nghiemthu_cq    VARCHAR(255)  DEFAULT NULL COMMENT 'Cơ quan ban hành VB nghiệm thu',
    -- Bảo hiểm cháy nổ chi tiết
    ADD COLUMN IF NOT EXISTS bh_cong_ty         VARCHAR(255)  DEFAULT NULL COMMENT 'Công ty bảo hiểm cháy nổ',
    ADD COLUMN IF NOT EXISTS bh_so_hd           VARCHAR(100)  DEFAULT NULL COMMENT 'Số hợp đồng bảo hiểm',
    ADD COLUMN IF NOT EXISTS bh_ngay_het_han    DATE          DEFAULT NULL COMMENT 'Ngày hết hạn bảo hiểm',
    -- Hợp đồng bảo dưỡng PCCC
    ADD COLUMN IF NOT EXISTS hd_bao_duong       TINYINT(1)    DEFAULT 0    COMMENT 'Có HĐ bảo dưỡng PCCC định kỳ',
    ADD COLUMN IF NOT EXISTS hd_bao_duong_ncc   VARCHAR(255)  DEFAULT NULL COMMENT 'Đơn vị cung cấp dịch vụ bảo dưỡng';

-- ============== F. Group F mở rộng — PC01 mục II.6 (Đội PCCC cơ sở) ==============
ALTER TABLE sale_lead_khao_sat
    ADD COLUMN IF NOT EXISTS doi_tong_doi_vien  INT           DEFAULT 0   COMMENT 'Tổng số đội viên PCCC cơ sở',
    ADD COLUMN IF NOT EXISTS doi_truong_ten     VARCHAR(120)  DEFAULT NULL COMMENT 'Họ tên đội trưởng PCCC cơ sở',
    ADD COLUMN IF NOT EXISTS doi_truong_sdt     VARCHAR(30)   DEFAULT NULL COMMENT 'SĐT đội trưởng PCCC',
    ADD COLUMN IF NOT EXISTS so_nguoi_pccc      INT           DEFAULT 0   COMMENT 'Tổng người được phân công nhiệm vụ PCCC';
