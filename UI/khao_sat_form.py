# -*- coding: utf-8 -*-
"""
UI Khảo sát hiện trường — Designer-style class (re-designed cho PC01-PC04).

Schema mới: 7 GROUP (A-G), tổng ~70 widget input, layout đồng bộ kích thước.
SSOT: tab Khảo sát là nguồn duy nhất cho mọi thông tin công trình + KH.

Cấu trúc:
  A. Thông tin chung công trình + cơ sở
  B. Quy mô + Kỹ thuật + Giao thông CC
  C. Hạ tầng kỹ thuật + Hệ thống PCCC sẵn có
  D. Pháp lý + Văn bản + Tài liệu KH
  E. Thương mại + Đánh giá sales
  F. Khảo sát + Đội PCCC cơ sở
  G. Khối nhà + Khu vực ngoài nhà (multi-block)

Placeholders: ks_placeholder_ht, ks_placeholder_bkl, ks_placeholder_tai_lieu,
              ks_placeholder_khoi_nha, ks_placeholder_khu_vuc
(các bảng động + 10 checklist tài liệu build trong khao_sat_helpers.py)
"""
from PyQt6 import QtCore, QtGui, QtWidgets


_STYLE = """
/* Background tổng — kem nhạt dịu mắt */
QWidget#KhaoSatForm { background: #fdfcf7; }

/* Input cơ bản — rõ ràng, dễ nhận, có hover/focus */
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {
    min-height: 32px;
    max-height: 36px;
    padding: 3px 10px;
    font-size: 13px;
    border: 1.5px solid #d1d5db;
    border-radius: 5px;
    background: #ffffff;
    selection-background-color: #99f6e4;
    selection-color: #064e3b;
}
QLineEdit:hover, QComboBox:hover, QDateEdit:hover,
QSpinBox:hover, QDoubleSpinBox:hover {
    border: 1.5px solid #94a3b8;
    background: #f8fafc;
}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus,
QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1.5px solid #14b8a6;
    background: #f0fdfa;
}
QLineEdit[readOnly="true"], QSpinBox[readOnly="true"] {
    background: #f1f5f9;
    color: #475569;
}

/* Combobox dropdown */
QComboBox::drop-down {
    width: 24px;
    border: none;
    background: transparent;
}
QComboBox QAbstractItemView {
    border: 1px solid #cbd5e1;
    background: white;
    selection-background-color: #ccfbf1;
    selection-color: #064e3b;
    padding: 4px;
}

/* TextEdit — nhiều dòng */
QTextEdit {
    padding: 8px 10px;
    font-size: 13px;
    border: 1.5px solid #d1d5db;
    border-radius: 5px;
    background: #ffffff;
}
QTextEdit:focus { border: 1.5px solid #14b8a6; background: #f0fdfa; }

/* Checkbox */
QCheckBox {
    spacing: 10px;
    font-size: 13px;
    min-height: 28px;
    color: #334155;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1.5px solid #94a3b8;
    border-radius: 3px;
    background: white;
}
QCheckBox::indicator:hover { border: 1.5px solid #14b8a6; }
QCheckBox::indicator:checked {
    background: #14b8a6;
    border: 1.5px solid #0f766e;
    image: none;
}

/* GroupBox — màu pastel dịu */
QGroupBox {
    font-weight: 600;
    font-size: 13.5px;
    margin-top: 18px;
    padding-top: 24px;
    border: 1.5px solid #e2e8f0;
    border-radius: 8px;
    background: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 16px;
    margin-left: 10px;
    color: white;
    background: #14b8a6;
    border-radius: 5px;
    font-size: 13.5px;
}

/* Label thường */
QLabel { font-size: 13px; color: #334155; }

/* Button mềm */
QPushButton {
    min-height: 32px;
    padding: 5px 16px;
    font-size: 13px;
    border: 1.5px solid #cbd5e1;
    border-radius: 5px;
    background: #f8fafc;
    color: #1e293b;
}
QPushButton:hover {
    background: #e0f2fe;
    border: 1.5px solid #38bdf8;
}
QPushButton:pressed { background: #bae6fd; }

/* Table */
QTableWidget {
    font-size: 12.5px;
    gridline-color: #e5e7eb;
    background: white;
    border: 1.5px solid #d1d5db;
    border-radius: 5px;
    selection-background-color: #ccfbf1;
    selection-color: #064e3b;
}
QTableWidget::item:selected { background: #ccfbf1; color: #064e3b; }
QHeaderView::section {
    background: #f1f5f9;
    color: #334155;
    padding: 6px 8px;
    border: none;
    border-right: 1px solid #e5e7eb;
    border-bottom: 1.5px solid #cbd5e1;
    font-weight: 600;
    font-size: 12.5px;
}
"""


# Helper tiện ích tạo widget
def _lbl(text, required=False):
    """Label, có dấu * đỏ nếu required."""
    if required:
        lbl = QtWidgets.QLabel(f"{text} <span style='color:#dc2626;'>*</span>")
    else:
        lbl = QtWidgets.QLabel(text)
    lbl.setTextFormat(QtCore.Qt.TextFormat.RichText)
    return lbl


def _line(placeholder="", max_w=None):
    le = QtWidgets.QLineEdit()
    if placeholder:
        le.setPlaceholderText(placeholder)
    if max_w:
        le.setMaximumWidth(max_w)
    return le


def _spin(maximum=99999, value=0, suffix=""):
    sb = QtWidgets.QSpinBox()
    sb.setMaximum(maximum)
    sb.setValue(value)
    if suffix:
        sb.setSuffix(suffix)
    return sb


def _dspin(maximum=99999.0, value=0.0, decimals=1, suffix=""):
    sb = QtWidgets.QDoubleSpinBox()
    sb.setDecimals(decimals)
    sb.setMaximum(maximum)
    sb.setValue(value)
    if suffix:
        sb.setSuffix(suffix)
    return sb


def _combo(items=None):
    cb = QtWidgets.QComboBox()
    if items:
        for k, t in items:
            cb.addItem(t, k)
    return cb


def _grid_row(grid, row, *items, vstretch=None):
    """Thêm 1 row vào QGridLayout. items = list of (widget, colspan)."""
    col = 0
    for it in items:
        if isinstance(it, tuple):
            w, cs = it
        else:
            w, cs = it, 1
        grid.addWidget(w, row, col, 1, cs)
        col += cs


class Ui_KhaoSatForm(object):
    """Designer-style class. Public widget names: ks_*"""

    def setupUi(self, KhaoSatForm):
        KhaoSatForm.setObjectName("KhaoSatForm")
        KhaoSatForm.resize(1180, 2800)
        KhaoSatForm.setStyleSheet(_STYLE)

        self.rootLayout = QtWidgets.QVBoxLayout(KhaoSatForm)
        self.rootLayout.setContentsMargins(16, 16, 16, 16)
        self.rootLayout.setSpacing(12)

        self._build_group_A(KhaoSatForm)
        self._build_group_B(KhaoSatForm)
        self._build_group_C(KhaoSatForm)
        self._build_group_D(KhaoSatForm)
        self._build_group_E(KhaoSatForm)
        self._build_group_F(KhaoSatForm)
        self._build_group_G(KhaoSatForm)
        self._build_actions(KhaoSatForm)

        self._populate_combos()

    # =====================================================================
    # GROUP A — Thông tin chung công trình + cơ sở
    # =====================================================================
    def _build_group_A(self, parent):
        gb = QtWidgets.QGroupBox("A. Thông tin chung công trình + cơ sở",
                                 parent=parent)
        self.ks_gb_A = gb
        grid = QtWidgets.QGridLayout(gb)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setContentsMargins(14, 8, 14, 12)

        # Tỉ lệ cột: [Label1(2)] [Field1(5)] [Label2(2)] [Field2(3)]
        grid.setColumnStretch(1, 5)
        grid.setColumnStretch(3, 3)

        # Hàng 1: Tên công ty + MST
        self.ks_kh_cty = _line("Công ty CP / TNHH …")
        self.ks_kh_mst = _line("VD: 0123456789")
        _grid_row(grid, 0,
                  _lbl("Tên công ty", True), self.ks_kh_cty,
                  _lbl("MST"), self.ks_kh_mst)

        # Hàng 2: Tên công trình + Năm hoạt động
        self.ks_ten_cong_trinh = _line("Tên công trình / cơ sở")
        self.ks_nam_hoat_dong = _spin(2100, 0)
        self.ks_nam_hoat_dong.setMinimum(0)
        self.ks_nam_hoat_dong.setSpecialValueText("(chưa rõ)")
        _grid_row(grid, 1,
                  _lbl("Tên công trình", True), self.ks_ten_cong_trinh,
                  _lbl("Năm hoạt động"), self.ks_nam_hoat_dong)

        # Hàng 3: Địa chỉ
        self.ks_dia_chi = _line("Số nhà, đường, phường/xã, quận/huyện, tỉnh/TP")
        _grid_row(grid, 2,
                  (_lbl("Địa chỉ", True), 1), (self.ks_dia_chi, 3))

        # Hàng 4: Công năng sử dụng (combo dài)
        self.ks_cong_nang = _combo()  # populate động trong _populate_combos
        self.ks_cong_nang.setSizeAdjustPolicy(
            QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        _grid_row(grid, 3,
                  (_lbl("Công năng sử dụng", True), 1), (self.ks_cong_nang, 3))

        # Hàng 5: Ngành nghề / lĩnh vực hoạt động
        self.ks_nganh_nghe = _line(
            "VD: Sản xuất linh kiện điện tử / Văn phòng cho thuê / …")
        _grid_row(grid, 4,
                  (_lbl("Ngành nghề / lĩnh vực"), 1), (self.ks_nganh_nghe, 3))

        # Hàng 6: Hình thức sở hữu + Trạng thái
        self.ks_hinh_thuc_so_huu = _combo()
        self.ks_trang_thai = _combo()
        _grid_row(grid, 5,
                  _lbl("Hình thức sở hữu"), self.ks_hinh_thuc_so_huu,
                  _lbl("Trạng thái"), self.ks_trang_thai)

        # Hàng 7: Thành phần KT + Cơ quan cấp trên
        self.ks_thanh_phan_kt = _combo()
        self.ks_co_quan_cap_tren = _line("Tên cơ quan/tổ chức cấp trên (nếu có)")
        _grid_row(grid, 6,
                  _lbl("Thành phần kinh tế"), self.ks_thanh_phan_kt,
                  _lbl("Cơ quan cấp trên"), self.ks_co_quan_cap_tren)

        # Hàng 8: Người quản lý trực tiếp — Họ tên + SĐT
        self.ks_nguoi_quan_ly = _line("Họ tên người/tổ chức quản lý")
        self.ks_quan_ly_sdt = _line("Số điện thoại")
        _grid_row(grid, 7,
                  _lbl("Quản lý — Họ tên"), self.ks_nguoi_quan_ly,
                  _lbl("SĐT quản lý"), self.ks_quan_ly_sdt)

        # Hàng 9: Người đại diện pháp luật — Họ tên + SĐT
        self.ks_dai_dien_pl_ten = _line("Họ tên")
        self.ks_dai_dien_pl_sdt = _line("Số điện thoại")
        _grid_row(grid, 8,
                  _lbl("Người ĐDPL — Họ tên"), self.ks_dai_dien_pl_ten,
                  _lbl("SĐT ĐDPL"), self.ks_dai_dien_pl_sdt)

        # Hàng 10: 3 checkbox
        cb_row = QtWidgets.QHBoxLayout()
        self.ks_ct_doc_lap = QtWidgets.QCheckBox(
            "Công trình ĐỘC LẬP (không phải 1 phần của CT lớn hơn)")
        self.ks_ct_doc_lap.setChecked(True)
        self.ks_thuoc_dm_nguyhiem = QtWidgets.QCheckBox(
            "Thuộc DM cơ sở nguy hiểm cháy nổ")
        self.ks_thuoc_dm_thamduyet = QtWidgets.QCheckBox(
            "Thuộc DM phải thẩm duyệt PCCC")
        cb_row.addWidget(self.ks_ct_doc_lap)
        cb_row.addWidget(self.ks_thuoc_dm_nguyhiem)
        cb_row.addWidget(self.ks_thuoc_dm_thamduyet)
        cb_row.addStretch()
        grid.addLayout(cb_row, 9, 0, 1, 4)

        self.rootLayout.addWidget(gb)

    # =====================================================================
    # GROUP B — Quy mô + Kỹ thuật + Giao thông CC
    # =====================================================================
    def _build_group_B(self, parent):
        gb = QtWidgets.QGroupBox("B. Quy mô + Kỹ thuật + Giao thông CC",
                                 parent=parent)
        self.ks_gb_B = gb
        grid = QtWidgets.QGridLayout(gb)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setContentsMargins(14, 8, 14, 12)
        # 6 cột đều (label+field)*3
        for c in (1, 3, 5):
            grid.setColumnStretch(c, 1)

        # Hàng 1: DT sàn tổng + DTXD + Chiều cao PCCC
        self.ks_dt_san_tong = _dspin(9999999.0, suffix=" m²")
        self.ks_dt_xay_dung = _dspin(9999999.0, suffix=" m²")
        self.ks_cao_pccc = _dspin(9999.0, suffix=" m")
        _grid_row(grid, 0,
                  _lbl("DT sàn tổng", True), self.ks_dt_san_tong,
                  _lbl("DT xây dựng"), self.ks_dt_xay_dung,
                  _lbl("Chiều cao PCCC", True), self.ks_cao_pccc)

        # Hàng 2: Số tầng nổi + Số tầng hầm + Số phòng
        self.ks_so_tang_noi = _spin(999, 1)
        self.ks_so_tang_ham = _spin(99, 0)
        self.ks_so_phong = _spin(9999, 0)
        _grid_row(grid, 1,
                  _lbl("Số tầng nổi", True), self.ks_so_tang_noi,
                  _lbl("Số tầng hầm"), self.ks_so_tang_ham,
                  _lbl("Số phòng"), self.ks_so_phong)

        # Hàng 3: Chiều dài + Chiều rộng nhà + KC tới CT kế bên
        self.ks_dai_nha = _dspin(9999.0, suffix=" m")
        self.ks_rong_nha = _dspin(9999.0, suffix=" m")
        self.ks_kc_ct_ke_ben = _dspin(9999.0, suffix=" m")
        _grid_row(grid, 2,
                  _lbl("Chiều dài nhà"), self.ks_dai_nha,
                  _lbl("Chiều rộng nhà"), self.ks_rong_nha,
                  _lbl("KC tới CT kế bên"), self.ks_kc_ct_ke_ben)

        # Hàng 4: Bậc chịu lửa + Cấp NHC + Hạng nguy hiểm
        self.ks_bac_chiu_lua = _combo()
        self.ks_cap_nhc = _combo()
        self.ks_hang_nguy_hiem = _combo()
        _grid_row(grid, 3,
                  _lbl("Bậc chịu lửa", True), self.ks_bac_chiu_lua,
                  _lbl("Cấp NHC kết cấu", True), self.ks_cap_nhc,
                  _lbl("Hạng nguy hiểm", True), self.ks_hang_nguy_hiem)

        # Hàng 5: Số người dự kiến + Số cháu (mầm non)
        # Lưu label làm attribute để có thể setVisible theo công năng
        self.ks_so_nguoi_du_kien = _spin(999999, 0)
        self.ks_so_chau = _spin(99999, 0)
        self.ks_lbl_so_nguoi = _lbl("Số người dự kiến")
        self.ks_lbl_so_chau = _lbl("Số cháu (mầm non)")
        _grid_row(grid, 4,
                  self.ks_lbl_so_nguoi, self.ks_so_nguoi_du_kien,
                  self.ks_lbl_so_chau, self.ks_so_chau)

        # Hàng 6: Đường giao thông CC — Rộng + Cao thông thủy
        self.ks_dgt_rong = _dspin(99.0, decimals=2, suffix=" m")
        self.ks_dgt_cao = _dspin(99.0, decimals=2, suffix=" m")
        _grid_row(grid, 5,
                  _lbl("ĐGT xe CC — Rộng"), self.ks_dgt_rong,
                  _lbl("ĐGT xe CC — Cao thông thủy"), self.ks_dgt_cao)

        # Hàng 7: Bãi đỗ xe CC (text dài)
        self.ks_bai_do_xe_cc = _line(
            "VD: 2 bãi đỗ trong khuôn viên + 1 bãi đỗ ngoài đường …")
        _grid_row(grid, 6,
                  (_lbl("Bãi đỗ xe CC (vị trí)"), 1), (self.ks_bai_do_xe_cc, 5))

        # Hàng 8: Checkbox xe CC tiếp cận
        self.ks_xe_cc_tiep_can = QtWidgets.QCheckBox(
            "Đường giao thông xe cứu hỏa tiếp cận được tới cơ sở")
        self.ks_xe_cc_tiep_can.setChecked(True)
        grid.addWidget(self.ks_xe_cc_tiep_can, 7, 0, 1, 6)

        self.rootLayout.addWidget(gb)

    # =====================================================================
    # GROUP C — Hạ tầng kỹ thuật + Hệ thống PCCC sẵn có
    # =====================================================================
    def _build_group_C(self, parent):
        gb = QtWidgets.QGroupBox("C. Hạ tầng kỹ thuật + Hệ thống PCCC sẵn có",
                                 parent=parent)
        self.ks_gb_C = gb
        vbox = QtWidgets.QVBoxLayout(gb)
        vbox.setContentsMargins(14, 8, 14, 12)
        vbox.setSpacing(8)

        # ---- Sub form 1: Nguồn nước + điện ----
        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        for c in (1, 3):
            grid.setColumnStretch(c, 1)

        # Hàng 1: Nguồn cấp nước (3 checkbox)
        nn_w = QtWidgets.QWidget()
        nn_lay = QtWidgets.QHBoxLayout(nn_w)
        nn_lay.setContentsMargins(0, 0, 0, 0)
        self.ks_nn_duong_ong = QtWidgets.QCheckBox("Đường ống đô thị")
        self.ks_nn_be_chua = QtWidgets.QCheckBox("Bể chứa riêng")
        self.ks_nn_song_ho = QtWidgets.QCheckBox("Sông / hồ / ao")
        nn_lay.addWidget(self.ks_nn_duong_ong)
        nn_lay.addWidget(self.ks_nn_be_chua)
        nn_lay.addWidget(self.ks_nn_song_ho)
        nn_lay.addStretch()
        _grid_row(grid, 0,
                  (_lbl("Nguồn cấp nước"), 1), (nn_w, 3))

        # Hàng 2: Chi tiết nguồn nước
        self.ks_nguon_nuoc_chi_tiet = _line(
            "VD: áp lực 2 bar, đường ống D100 …")
        _grid_row(grid, 1,
                  (_lbl("Chi tiết nguồn nước"), 1),
                  (self.ks_nguon_nuoc_chi_tiet, 3))

        # Hàng 3: Số bể + Khối tích bể
        self.ks_so_be_cc = _spin(99, 0)
        self.ks_khoi_tich_be = _dspin(99999.0, suffix=" m³")
        _grid_row(grid, 2,
                  _lbl("Số bể CC"), self.ks_so_be_cc,
                  _lbl("Khối tích bể (tổng)"), self.ks_khoi_tich_be)

        # Hàng 4: Vị trí bể (text dài)
        self.ks_vi_tri_be = _line(
            "Vị trí bể + khả năng lấy nước bằng xe/máy bơm CC")
        _grid_row(grid, 3,
                  (_lbl("Vị trí bể"), 1), (self.ks_vi_tri_be, 3))

        # Hàng 5: Số trụ + Vị trí trụ
        self.ks_so_tru_cc = _spin(99, 0)
        self.ks_vi_tri_tru = _line("Vị trí trụ cấp nước CC")
        _grid_row(grid, 4,
                  _lbl("Số trụ cấp nước CC"), self.ks_so_tru_cc,
                  _lbl("Vị trí trụ"), self.ks_vi_tri_tru)

        # Hàng 6: Nguồn điện + có máy phát
        self.ks_nguon_dien = _combo()
        self.ks_co_may_phat = QtWidgets.QCheckBox(
            "Có máy phát điện dự phòng")
        _grid_row(grid, 5,
                  _lbl("Nguồn điện"), self.ks_nguon_dien,
                  (self.ks_co_may_phat, 2))

        # Hàng 7: Máy phát kVA + giờ chạy
        self.ks_mp_cong_suat = _dspin(99999.0, suffix=" kVA")
        self.ks_mp_thoi_gian = _dspin(999.0, suffix=" giờ")
        _grid_row(grid, 6,
                  _lbl("Công suất máy phát"), self.ks_mp_cong_suat,
                  _lbl("Thời gian chạy được"), self.ks_mp_thoi_gian)

        # Hàng 8: Truyền tin báo cháy + xe CC riêng
        cb_row = QtWidgets.QHBoxLayout()
        self.ks_truyen_tin_da_lap = QtWidgets.QCheckBox(
            "Đã lắp truyền tin báo cháy (NĐ 105/2025)")
        self.ks_co_xe_chua_chay = QtWidgets.QCheckBox(
            "Cơ sở có xe chữa cháy riêng")
        cb_row.addWidget(self.ks_truyen_tin_da_lap)
        cb_row.addWidget(self.ks_co_xe_chua_chay)
        cb_row.addStretch()
        grid.addLayout(cb_row, 7, 0, 1, 4)

        # Hàng 9: Mô tả phương tiện CC cơ giới
        self.ks_phuong_tien_cc = _line(
            "Số lượng, loại phương tiện CC cơ giới (nếu có)")
        _grid_row(grid, 8,
                  (_lbl("Phương tiện CC cơ giới"), 1),
                  (self.ks_phuong_tien_cc, 3))

        vbox.addLayout(grid)

        # ---- Sub block: Hệ thống PCCC sẵn có (table động) ----
        lbl_ht = QtWidgets.QLabel(
            "<b>Hệ thống PCCC sẵn có:</b> (Hệ thống / Tình trạng / Hãng-Model)")
        vbox.addWidget(lbl_ht)
        self.placeholder_ht = QtWidgets.QVBoxLayout()
        vbox.addLayout(self.placeholder_ht)

        # ---- Sub block: Upload bảng khối lượng ----
        self.placeholder_bkl = QtWidgets.QHBoxLayout()
        vbox.addLayout(self.placeholder_bkl)

        self.rootLayout.addWidget(gb)

    # =====================================================================
    # GROUP D — Pháp lý + Văn bản + Tài liệu KH
    # =====================================================================
    def _build_group_D(self, parent):
        gb = QtWidgets.QGroupBox("D. Pháp lý + Văn bản + Tài liệu KH",
                                 parent=parent)
        self.ks_gb_D = gb
        vbox = QtWidgets.QVBoxLayout(gb)
        vbox.setContentsMargins(14, 8, 14, 12)
        vbox.setSpacing(8)

        # ---- Sub form: Văn bản PCCC chi tiết ----
        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        for c in (1, 3, 5):
            grid.setColumnStretch(c, 1)

        # Hàng 1: VB thẩm duyệt — số + ngày + cơ quan
        self.ks_vb_thamduyet_so = _line("Số VB")
        self.ks_vb_thamduyet_ngay = QtWidgets.QDateEdit()
        self.ks_vb_thamduyet_ngay.setCalendarPopup(True)
        self.ks_vb_thamduyet_ngay.setDate(QtCore.QDate(2000, 1, 1))
        self.ks_vb_thamduyet_ngay.setSpecialValueText("(chưa có)")
        self.ks_vb_thamduyet_ngay.setMinimumDate(QtCore.QDate(2000, 1, 1))
        self.ks_vb_thamduyet_cq = _line("Cơ quan ban hành")
        _grid_row(grid, 0,
                  _lbl("VB Thẩm duyệt — Số"), self.ks_vb_thamduyet_so,
                  _lbl("Ngày"), self.ks_vb_thamduyet_ngay,
                  _lbl("Cơ quan"), self.ks_vb_thamduyet_cq)

        # Hàng 2: VB nghiệm thu — số + ngày + cơ quan
        self.ks_vb_nghiemthu_so = _line("Số VB")
        self.ks_vb_nghiemthu_ngay = QtWidgets.QDateEdit()
        self.ks_vb_nghiemthu_ngay.setCalendarPopup(True)
        self.ks_vb_nghiemthu_ngay.setDate(QtCore.QDate(2000, 1, 1))
        self.ks_vb_nghiemthu_ngay.setMinimumDate(QtCore.QDate(2000, 1, 1))
        self.ks_vb_nghiemthu_cq = _line("Cơ quan ban hành")
        _grid_row(grid, 1,
                  _lbl("VB Nghiệm thu — Số"), self.ks_vb_nghiemthu_so,
                  _lbl("Ngày"), self.ks_vb_nghiemthu_ngay,
                  _lbl("Cơ quan"), self.ks_vb_nghiemthu_cq)

        # Hàng 3: Bảo hiểm — công ty + số HĐ + hết hạn
        self.ks_bh_cong_ty = _line("VD: Bảo hiểm Bảo Việt")
        self.ks_bh_so_hd = _line("Số HĐ")
        self.ks_bh_ngay_het_han = QtWidgets.QDateEdit()
        self.ks_bh_ngay_het_han.setCalendarPopup(True)
        self.ks_bh_ngay_het_han.setDate(QtCore.QDate(2000, 1, 1))
        self.ks_bh_ngay_het_han.setMinimumDate(QtCore.QDate(2000, 1, 1))
        _grid_row(grid, 2,
                  _lbl("Bảo hiểm — Công ty"), self.ks_bh_cong_ty,
                  _lbl("Số HĐ"), self.ks_bh_so_hd,
                  _lbl("Hết hạn"), self.ks_bh_ngay_het_han)

        # Hàng 4: Hợp đồng bảo dưỡng PCCC
        bd_w = QtWidgets.QHBoxLayout()
        self.ks_hd_bao_duong = QtWidgets.QCheckBox("Có HĐ bảo dưỡng PCCC định kỳ")
        self.ks_hd_bao_duong_ncc = _line("Đơn vị cung cấp dịch vụ bảo dưỡng")
        bd_w.addWidget(self.ks_hd_bao_duong)
        bd_w.addWidget(self.ks_hd_bao_duong_ncc, 1)
        grid.addLayout(bd_w, 3, 0, 1, 6)

        vbox.addLayout(grid)

        # ---- Sub block: Checklist 10 tài liệu (build động) ----
        lbl_tl = QtWidgets.QLabel(
            "<b>Tài liệu khách hàng đã có:</b> tick + nhấn 📎 để upload")
        vbox.addWidget(lbl_tl)
        self.placeholder_tai_lieu = QtWidgets.QVBoxLayout()
        vbox.addLayout(self.placeholder_tai_lieu)

        # ---- Sub block: Lịch sử PCCC ----
        lbl_ls = QtWidgets.QLabel("<b>Lịch sử PCCC:</b>")
        vbox.addWidget(lbl_ls)
        self.ks_lich_su_pccc = QtWidgets.QTextEdit()
        self.ks_lich_su_pccc.setMaximumHeight(80)
        self.ks_lich_su_pccc.setPlaceholderText(
            "Cháy nổ trong quá khứ, kiểm tra/xử phạt PCCC trước đây, sơ hở "
            "đã được CA phát hiện…")
        vbox.addWidget(self.ks_lich_su_pccc)

        self.rootLayout.addWidget(gb)

    # =====================================================================
    # GROUP E — Thương mại + Đánh giá sales
    # =====================================================================
    def _build_group_E(self, parent):
        gb = QtWidgets.QGroupBox("E. Thương mại + Đánh giá sales",
                                 parent=parent)
        self.ks_gb_E = gb
        vbox = QtWidgets.QVBoxLayout(gb)
        vbox.setContentsMargins(14, 8, 14, 12)
        vbox.setSpacing(8)

        # ---- Sub form 1: Yêu cầu KH + ngân sách + deadline ----
        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(1, 3)
        grid.setColumnStretch(3, 2)

        self.ks_yc_kh = QtWidgets.QTextEdit()
        self.ks_yc_kh.setMaximumHeight(70)
        self.ks_yc_kh.setPlaceholderText("Yêu cầu / mong muốn của KH…")
        _grid_row(grid, 0,
                  (_lbl("Yêu cầu KH"), 1), (self.ks_yc_kh, 3))

        self.ks_ngan_sach = _combo()
        self.ks_deadline = _line("VD: trước 30/9, khai trương quý IV…")
        _grid_row(grid, 1,
                  _lbl("Ngân sách dự kiến"), self.ks_ngan_sach,
                  _lbl("Deadline"), self.ks_deadline)

        vbox.addLayout(grid)

        # ---- Sub block: Người ra quyết định (3 ô) ----
        lbl_qd = QtWidgets.QLabel("<b>Người ra quyết định mua:</b>")
        vbox.addWidget(lbl_qd)
        qd_w = QtWidgets.QHBoxLayout()
        self.ks_qd_ten = _line("Họ tên")
        self.ks_qd_chuc_vu = _line("Chức vụ")
        self.ks_qd_sdt = _line("SĐT")
        qd_w.addWidget(self.ks_qd_ten, 2)
        qd_w.addWidget(self.ks_qd_chuc_vu, 1)
        qd_w.addWidget(self.ks_qd_sdt, 1)
        vbox.addLayout(qd_w)

        # ---- Sub block: Liên hệ kỹ thuật (3 ô) ----
        lbl_lh = QtWidgets.QLabel("<b>Liên hệ kỹ thuật:</b>")
        vbox.addWidget(lbl_lh)
        lh_w = QtWidgets.QHBoxLayout()
        self.ks_lh_ten = _line("Họ tên")
        self.ks_lh_chuc_vu = _line("Chức vụ")
        self.ks_lh_sdt = _line("SĐT")
        lh_w.addWidget(self.ks_lh_ten, 2)
        lh_w.addWidget(self.ks_lh_chuc_vu, 1)
        lh_w.addWidget(self.ks_lh_sdt, 1)
        vbox.addLayout(lh_w)

        # ---- Sub block: Đối thủ ----
        dt_w = QtWidgets.QHBoxLayout()
        self.ks_doi_thu_da_bao_gia = QtWidgets.QCheckBox("Đối thủ đã báo giá")
        self.ks_doi_thu_ten = _line("Tên đối thủ (nếu biết)")
        dt_w.addWidget(self.ks_doi_thu_da_bao_gia)
        dt_w.addWidget(self.ks_doi_thu_ten, 1)
        vbox.addLayout(dt_w)

        # ---- Sub block: Đánh giá + Bước tiếp theo ----
        lbl_dgs = QtWidgets.QLabel("<b>Đánh giá sales:</b>")
        vbox.addWidget(lbl_dgs)
        self.ks_danh_gia_sales = QtWidgets.QTextEdit()
        self.ks_danh_gia_sales.setMaximumHeight(70)
        self.ks_danh_gia_sales.setPlaceholderText(
            "Đánh giá / nhận xét ban đầu về cơ hội")
        vbox.addWidget(self.ks_danh_gia_sales)

        lbl_btt = QtWidgets.QLabel("<b>Bước tiếp theo:</b>")
        vbox.addWidget(lbl_btt)
        self.ks_buoc_tiep_theo = QtWidgets.QTextEdit()
        self.ks_buoc_tiep_theo.setMaximumHeight(70)
        self.ks_buoc_tiep_theo.setPlaceholderText(
            "Gửi báo giá, hẹn demo, làm hồ sơ…")
        vbox.addWidget(self.ks_buoc_tiep_theo)

        self.rootLayout.addWidget(gb)

    # =====================================================================
    # GROUP F — Khảo sát + Đội PCCC cơ sở
    # =====================================================================
    def _build_group_F(self, parent):
        gb = QtWidgets.QGroupBox("F. Khảo sát + Đội PCCC cơ sở",
                                 parent=parent)
        self.ks_gb_F = gb
        vbox = QtWidgets.QVBoxLayout(gb)
        vbox.setContentsMargins(14, 8, 14, 12)
        vbox.setSpacing(8)

        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        for c in (1, 3):
            grid.setColumnStretch(c, 1)

        # Hàng 1: Ngày khảo sát + Người khảo sát
        self.ks_ngay_khao_sat = QtWidgets.QDateEdit()
        self.ks_ngay_khao_sat.setCalendarPopup(True)
        self.ks_ngay_khao_sat.setDate(QtCore.QDate.currentDate())
        self.ks_nguoi_khao_sat = _line("Tên người khảo sát (sales)")
        _grid_row(grid, 0,
                  _lbl("Ngày khảo sát"), self.ks_ngay_khao_sat,
                  _lbl("Người khảo sát"), self.ks_nguoi_khao_sat)

        vbox.addLayout(grid)

        # ---- Sub block: Người tiếp đón (3 ô) ----
        lbl_td = QtWidgets.QLabel("<b>Người tiếp đón từ phía KH:</b>")
        vbox.addWidget(lbl_td)
        td_w = QtWidgets.QHBoxLayout()
        self.ks_td_ten = _line("Họ tên")
        self.ks_td_chuc_vu = _line("Chức vụ")
        self.ks_td_sdt = _line("SĐT")
        td_w.addWidget(self.ks_td_ten, 2)
        td_w.addWidget(self.ks_td_chuc_vu, 1)
        td_w.addWidget(self.ks_td_sdt, 1)
        vbox.addLayout(td_w)

        # ---- Sub block: Đội PCCC cơ sở ----
        lbl_doi = QtWidgets.QLabel(
            "<b>Đội PCCC cơ sở</b> (NĐ 105/2025 — bắt buộc với cơ sở "
            "≥ 50 người):")
        vbox.addWidget(lbl_doi)

        grid2 = QtWidgets.QGridLayout()
        grid2.setHorizontalSpacing(12)
        grid2.setVerticalSpacing(8)
        for c in (1, 3):
            grid2.setColumnStretch(c, 1)

        self.ks_doi_tong = _spin(9999, 0)
        self.ks_so_nguoi_pccc = _spin(99999, 0)
        _grid_row(grid2, 0,
                  _lbl("Tổng đội viên"), self.ks_doi_tong,
                  _lbl("Tổng người phân công PCCC"), self.ks_so_nguoi_pccc)

        self.ks_doi_truong_ten = _line("Họ tên đội trưởng")
        self.ks_doi_truong_sdt = _line("SĐT đội trưởng")
        _grid_row(grid2, 1,
                  _lbl("Đội trưởng — Họ tên"), self.ks_doi_truong_ten,
                  _lbl("SĐT đội trưởng"), self.ks_doi_truong_sdt)

        vbox.addLayout(grid2)

        self.rootLayout.addWidget(gb)

    # =====================================================================
    # GROUP G — Khối nhà + Khu vực ngoài nhà (multi-block)
    # =====================================================================
    def _build_group_G(self, parent):
        gb = QtWidgets.QGroupBox(
            "G. Khối nhà + Khu vực ngoài nhà (cơ sở đa khối)",
            parent=parent)
        self.ks_gb_G = gb
        vbox = QtWidgets.QVBoxLayout(gb)
        vbox.setContentsMargins(14, 8, 14, 12)
        vbox.setSpacing(8)

        self.ks_co_nhieu_khoi = QtWidgets.QCheckBox(
            "Cơ sở có nhiều khối nhà / khu vực — kê khai chi tiết")
        vbox.addWidget(self.ks_co_nhieu_khoi)

        # Khối nhà
        lbl_kn = QtWidgets.QLabel("<b>Khối nhà trong cơ sở:</b>")
        vbox.addWidget(lbl_kn)
        self.placeholder_khoi_nha = QtWidgets.QVBoxLayout()
        vbox.addLayout(self.placeholder_khoi_nha)

        # Khu vực ngoài nhà
        lbl_kv = QtWidgets.QLabel(
            "<b>Khu vực NGOÀI nhà</b> (dây chuyền CN, kho vật tư dễ cháy):")
        vbox.addWidget(lbl_kv)
        self.placeholder_khu_vuc = QtWidgets.QVBoxLayout()
        vbox.addLayout(self.placeholder_khu_vuc)

        self.rootLayout.addWidget(gb)

    # =====================================================================
    # Action bar: Lưu + Xuất biên bản KS + Xuất 4 mẫu PC
    # =====================================================================
    def _build_actions(self, parent):
        btn_w = QtWidgets.QHBoxLayout()
        btn_w.setSpacing(8)

        self.ks_but_luu = QtWidgets.QPushButton("💾 Lưu khảo sát vào lead")
        self.ks_but_luu.setStyleSheet(
            "QPushButton { background:#0f766e; color:white; "
            "padding:10px 18px; font-weight:600; border-radius:6px; }"
            "QPushButton:hover { background:#0d8a80; }")

        self.ks_but_xuat = QtWidgets.QPushButton("📄 Xuất biên bản khảo sát")
        self.ks_but_xuat.setStyleSheet(
            "QPushButton { background:#1d4ed8; color:white; "
            "padding:10px 18px; font-weight:600; border-radius:6px; }"
            "QPushButton:hover { background:#1e40af; }")

        self.ks_but_pc01 = QtWidgets.QPushButton("📋 Xuất PC01")
        self.ks_but_pc02 = QtWidgets.QPushButton("📋 Xuất PC02")
        self.ks_but_pc03 = QtWidgets.QPushButton("📋 Xuất PC03")
        self.ks_but_pc04 = QtWidgets.QPushButton("📋 Xuất PC04")
        for b in (self.ks_but_pc01, self.ks_but_pc02,
                  self.ks_but_pc03, self.ks_but_pc04):
            b.setStyleSheet(
                "QPushButton { background:#475569; color:white; "
                "padding:10px 14px; font-weight:600; border-radius:6px; }"
                "QPushButton:hover { background:#334155; }")

        btn_w.addWidget(self.ks_but_luu)
        btn_w.addWidget(self.ks_but_xuat)
        btn_w.addSpacing(20)
        btn_w.addWidget(self.ks_but_pc01)
        btn_w.addWidget(self.ks_but_pc02)
        btn_w.addWidget(self.ks_but_pc03)
        btn_w.addWidget(self.ks_but_pc04)
        btn_w.addStretch()

        self.rootLayout.addLayout(btn_w)

    # =====================================================================
    # Populate combobox items
    # =====================================================================
    def _populate_combos(self):
        # Hình thức sở hữu
        for k, t in [("so_huu", "Sở hữu"),
                     ("thue", "Thuê"),
                     ("khac", "Khác")]:
            self.ks_hinh_thuc_so_huu.addItem(t, k)

        # Trạng thái
        for k, t in [("thiet_ke", "Đang thiết kế"),
                     ("thi_cong", "Đang thi công"),
                     ("van_hanh", "Đã đi vào vận hành")]:
            self.ks_trang_thai.addItem(t, k)

        # Thành phần kinh tế
        for k, t in [("", "(Chưa rõ)"),
                     ("nha_nuoc", "Nhà nước"),
                     ("tap_the", "Tập thể"),
                     ("tu_nhan", "Tư nhân"),
                     ("von_nuoc_ngoai", "Có vốn đầu tư nước ngoài")]:
            self.ks_thanh_phan_kt.addItem(t, k)

        # Bậc chịu lửa
        for b in ["I", "II", "III", "IV", "V"]:
            self.ks_bac_chiu_lua.addItem(f"Bậc {b}", b)
        self.ks_bac_chiu_lua.setCurrentIndex(1)  # II

        # Cấp NHC
        for s in ["S0", "S1", "S2", "S3"]:
            self.ks_cap_nhc.addItem(s, s)

        # Hạng nguy hiểm
        for h in ["A", "B", "C", "D", "E"]:
            self.ks_hang_nguy_hiem.addItem(f"Hạng {h}", h)
        self.ks_hang_nguy_hiem.setCurrentIndex(2)  # C

        # Nguồn điện
        for k, t in [("1_nguon", "1 nguồn (rủi ro)"),
                     ("2_nguon", "2 nguồn độc lập")]:
            self.ks_nguon_dien.addItem(t, k)

        # Ngân sách
        for k, t in [("", "Chưa rõ"),
                     ("<100tr", "Dưới 100 triệu"),
                     ("100-500tr", "100 – 500 triệu"),
                     ("500tr-2ty", "500tr – 2 tỷ"),
                     (">2ty", "Trên 2 tỷ")]:
            self.ks_ngan_sach.addItem(t, k)

        # Công năng — sẽ được populate từ ngoài (pccc_rules.CONG_NANG_LIST)
        # vì cần import R. Module gọi sẽ tự populate trong build_tab_khao_sat.
