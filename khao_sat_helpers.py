# -*- coding: utf-8 -*-
"""Tab Khảo sát hiện trường — UI v5 (PC01-PC04 ready).

Dùng UI/khao_sat_form.py (Designer-style) cho phần tĩnh.
Tự build phần động: 2 table (HT sẵn có, Khối nhà, Khu vực), 10 checklist tài liệu, upload BKL.
"""
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QDateEdit,
)
from UI.khao_sat_form import Ui_KhaoSatForm
import khao_sat_data as KSD
import pccc_rules as R

# Re-export cho compat
ap_du_lieu = KSD.ap_du_lieu
luu_khao_sat = KSD.luu_khao_sat
xuat_bien_ban = KSD.xuat_bien_ban
thu_thap = KSD.thu_thap

TAI_LIEU_KEYS = [
    ("gp_xay_dung", "Giấy phép xây dựng"),
    ("gcn_qsdd", "GCN quyền sử dụng đất"),
    ("bv_thiet_ke_pccc", "Bản vẽ thiết kế PCCC"),
    ("bv_hoan_cong", "Bản vẽ hoàn công"),
    ("bb_nghiem_thu_pccc", "Biên bản nghiệm thu PCCC"),
    ("qd_tham_duyet", "Quyết định thẩm duyệt PCCC trước đó"),
    ("so_theo_doi_pccc", "Sổ theo dõi PCCC"),
    ("bb_kiem_tra_ca", "Biên bản kiểm tra của Công an PCCC"),
    ("hd_su_dung", "Hướng dẫn sử dụng thiết bị PCCC"),
    ("bh_chay_no", "Hợp đồng bảo hiểm cháy nổ"),
]


def build_tab_khao_sat(self):
    """Build tab Khảo sát: setupUi từ Designer + bổ sung phần động."""
    # Wrap UI form trong QScrollArea (form rất dài, ~70 widget)
    tab = QWidget()
    outer = QVBoxLayout(tab)
    outer.setContentsMargins(0, 0, 0, 0)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.Shape.NoFrame)
    outer.addWidget(scroll)
    inner = QWidget()
    scroll.setWidget(inner)

    # Áp dụng UI từ Designer
    ui = Ui_KhaoSatForm()
    ui.setupUi(inner)
    self._ks_ui = ui

    # Expose toàn bộ ks_* widget + placeholder lên self
    for attr in dir(ui):
        if attr.startswith("ks_") or attr.startswith("placeholder_"):
            setattr(self, attr, getattr(ui, attr))

    # === Populate cbo cong_nang (26 công năng từ R.CONG_NANG_LIST) ===
    for cn in R.CONG_NANG_LIST:
        self.ks_cong_nang.addItem(f"{cn['muc']:>2}. {cn['t']}", cn["k"])
        self.ks_cong_nang.setItemData(
            self.ks_cong_nang.count() - 1, cn["t"], Qt.ItemDataRole.ToolTipRole)
    # Set width đủ cho text dài nhất
    fm = QFontMetrics(self.ks_cong_nang.font())
    max_w = max(
        fm.horizontalAdvance(self.ks_cong_nang.itemText(k))
        for k in range(self.ks_cong_nang.count()))
    self.ks_cong_nang.view().setMinimumWidth(max_w + 60)
    self.ks_cong_nang.view().setTextElideMode(Qt.TextElideMode.ElideNone)

    # === Compat: 3 checkbox nguồn nước → dict cho data layer ===
    self.ks_nguon_nuoc_checks = {
        "duong_ong": ui.ks_nn_duong_ong,
        "be_chua": ui.ks_nn_be_chua,
        "song_ho": ui.ks_nn_song_ho,
    }

    # === Init giá trị mặc định ===
    self.ks_ngay_khao_sat.setDate(QDate.currentDate())
    if getattr(self, "user", None):
        self.ks_nguoi_khao_sat.setText(self.user)
    # Pre-fill kh_cty + kh_mst từ ttkh_initial nếu có (mở từ form lead)
    if getattr(self, "_ttkh_initial", None):
        t = self._ttkh_initial
        if t.get("cty"):
            self.ks_kh_cty.setText(str(t["cty"]))
        if t.get("mst"):
            self.ks_kh_mst.setText(str(t["mst"]))
        if t.get("ten"):
            self.ks_ten_cong_trinh.setText(str(t["ten"]))
        if t.get("dia_chi"):
            self.ks_dia_chi.setText(str(t["dia_chi"]))

    # === Phần động ===
    _build_table_ht(self, ui.placeholder_ht)
    _build_upload_bkl(self, ui.placeholder_bkl)
    _build_checklist_tai_lieu(self, ui.placeholder_tai_lieu)
    _build_table_khoi_nha(self, ui.placeholder_khoi_nha)
    _build_table_khu_vuc(self, ui.placeholder_khu_vuc)

    # === Bind nút action ===
    self.ks_but_luu.clicked.connect(lambda: KSD.luu_khao_sat(self))
    self.ks_but_xuat.clicked.connect(lambda: KSD.xuat_bien_ban(self))
    # PC01-04: stub cho M11-M13
    self.ks_but_pc01.clicked.connect(lambda: _xuat_pc_stub(self, "PC01"))
    self.ks_but_pc02.clicked.connect(lambda: _xuat_pc_stub(self, "PC02"))
    self.ks_but_pc03.clicked.connect(lambda: _xuat_pc_stub(self, "PC03"))
    self.ks_but_pc04.clicked.connect(lambda: _xuat_pc_stub(self, "PC04"))

    # === Enable/disable Group G theo checkbox "Có nhiều khối" ===
    self.ks_co_nhieu_khoi.toggled.connect(
        lambda v: _toggle_group_G(self, v))
    _toggle_group_G(self, False)  # default: ẩn

    # === Chèn tab vào vị trí #2 (sau Thiết bị bắt buộc) ===
    self.tabs.insertTab(1, tab, "② Khảo sát hiện trường")


# =====================================================================
# Phần động 1: Bảng hệ thống PCCC sẵn có
# =====================================================================
def _build_table_ht(self, layout):
    self.ks_tb_ht_san_co = QTableWidget(0, 3)
    self.ks_tb_ht_san_co.setHorizontalHeaderLabels(
        ["Hệ thống", "Tình trạng", "Hãng / Model"])
    hdr = self.ks_tb_ht_san_co.horizontalHeader()
    hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
    hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
    self.ks_tb_ht_san_co.setColumnWidth(0, 220)
    self.ks_tb_ht_san_co.setColumnWidth(2, 240)
    self.ks_tb_ht_san_co.verticalHeader().setDefaultSectionSize(28)
    self.ks_tb_ht_san_co.setMinimumHeight(200)
    # 6 hệ thống mặc định
    for name in ["Báo cháy tự động", "Sprinkler tự động",
                 "Họng nước chữa cháy", "Bình chữa cháy",
                 "Đèn EXIT + sự cố", "Cửa ngăn cháy"]:
        KSD.add_ht_row(self, name, "", "", read_only_name=True)
    layout.addWidget(self.ks_tb_ht_san_co)

    btn_w = QHBoxLayout()
    btn_add = QPushButton("➕ Thêm hệ thống khác")
    btn_add.clicked.connect(
        lambda: KSD.add_ht_row(self, "", "", "", read_only_name=False))
    btn_del = QPushButton("🗑 Xóa dòng đang chọn")
    btn_del.clicked.connect(lambda: KSD.del_ht_row(self))
    btn_w.addWidget(btn_add)
    btn_w.addWidget(btn_del)
    btn_w.addStretch()
    layout.addLayout(btn_w)


# =====================================================================
# Phần động 2: Upload bảng khối lượng
# =====================================================================
def _build_upload_bkl(self, layout):
    lbl = QLabel("<b>Bảng khối lượng KH cung cấp (nếu có):</b>")
    btn = QPushButton("📎 Upload bảng khối lượng")
    btn.setMaximumWidth(240)
    btn.clicked.connect(lambda: _upload_bkl(self))
    self.ks_bkl_status = QLabel("")
    self.ks_bkl_status.setStyleSheet("color: #555; font-style: italic;")
    self.ks_bkl_drive_info = ""
    layout.addWidget(lbl)
    layout.addWidget(btn)
    layout.addWidget(self.ks_bkl_status, 1)


def _upload_bkl(self):
    if not getattr(self, "lead_id", None):
        QMessageBox.warning(
            self, "Chưa có lead",
            "Chức năng upload chỉ dùng được khi mở từ form Update lead.")
        return
    file_path, _ = QFileDialog.getOpenFileName(
        self, "Chọn file bảng khối lượng", "",
        "Excel/PDF (*.xlsx *.xls *.pdf);;Tất cả (*.*)")
    if not file_path:
        return
    try:
        import file_handle
        info = file_handle.upload_file_to_lead_folder(
            self.lead_id, file_path, doc_key="bang_khoi_luong")
    except Exception as e:
        QMessageBox.critical(self, "Lỗi upload", str(e))
        return
    if not info:
        QMessageBox.warning(self, "Upload thất bại",
                            "Không upload được lên Drive.")
        return
    self.ks_bkl_drive_info = info
    fname = info.split("|")[0]
    self.ks_bkl_status.setText(f"✓ {fname[:60]}")
    self.ks_bkl_status.setStyleSheet("color: #059669; font-style: italic;")


# =====================================================================
# Phần động 3: Checklist 10 tài liệu
# =====================================================================
def _build_checklist_tai_lieu(self, layout):
    from PyQt6.QtWidgets import QHBoxLayout, QCheckBox, QPushButton, QLabel
    self.ks_tai_lieu_checks = {}
    self.ks_tai_lieu_drive = {}
    self.ks_tai_lieu_btns = {}
    self.ks_tai_lieu_labels = {}
    for key, label in TAI_LIEU_KEYS:
        row = QHBoxLayout()
        cb = QCheckBox(label)
        cb.setMinimumWidth(340)
        self.ks_tai_lieu_checks[key] = cb
        btn = QPushButton("Upload")
        btn.setMaximumWidth(120)
        btn.clicked.connect(
            lambda _, k=key, lbl=label: KSD.upload_tai_lieu(self, k, lbl))
        self.ks_tai_lieu_btns[key] = btn
        status = QLabel("")
        status.setStyleSheet("color: #555; font-style: italic;")
        self.ks_tai_lieu_labels[key] = status
        row.addWidget(cb)
        row.addWidget(btn)
        row.addWidget(status, 1)
        layout.addLayout(row)


def _build_table_khoi_nha(self, layout):
    from PyQt6.QtWidgets import (QTableWidget, QHeaderView, QHBoxLayout,
                                  QPushButton)
    self.ks_tb_khoi_nha = QTableWidget(0, 7)
    self.ks_tb_khoi_nha.setHorizontalHeaderLabels([
        "Ten khoi", "DTXD (m2)", "Tang noi",
        "Tang ham", "Bac CL", "Cong nang", "So loi thoat"])
    hdr = self.ks_tb_khoi_nha.horizontalHeader()
    hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
    hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
    self.ks_tb_khoi_nha.setColumnWidth(0, 140)
    self.ks_tb_khoi_nha.setColumnWidth(1, 100)
    self.ks_tb_khoi_nha.setColumnWidth(2, 80)
    self.ks_tb_khoi_nha.setColumnWidth(3, 80)
    self.ks_tb_khoi_nha.setColumnWidth(4, 70)
    self.ks_tb_khoi_nha.setColumnWidth(6, 100)
    self.ks_tb_khoi_nha.verticalHeader().setDefaultSectionSize(28)
    self.ks_tb_khoi_nha.setMinimumHeight(150)
    layout.addWidget(self.ks_tb_khoi_nha)
    btn_w = QHBoxLayout()
    btn_add = QPushButton("Them khoi nha")
    btn_add.clicked.connect(lambda: KSD.add_khoi_nha_row(self))
    btn_del = QPushButton("Xoa khoi nha")
    btn_del.clicked.connect(lambda: KSD.del_khoi_nha_row(self))
    btn_w.addWidget(btn_add)
    btn_w.addWidget(btn_del)
    btn_w.addStretch()
    layout.addLayout(btn_w)


def _build_table_khu_vuc(self, layout):
    from PyQt6.QtWidgets import (QTableWidget, QHeaderView, QHBoxLayout,
                                  QPushButton)
    self.ks_tb_khu_vuc = QTableWidget(0, 3)
    self.ks_tb_khu_vuc.setHorizontalHeaderLabels([
        "Ten khu vuc", "DT su dung (m2)",
        "Day chuyen CN / vat tu de chay"])
    hdr = self.ks_tb_khu_vuc.horizontalHeader()
    hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
    hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
    self.ks_tb_khu_vuc.setColumnWidth(0, 200)
    self.ks_tb_khu_vuc.setColumnWidth(1, 120)
    self.ks_tb_khu_vuc.verticalHeader().setDefaultSectionSize(28)
    self.ks_tb_khu_vuc.setMinimumHeight(120)
    layout.addWidget(self.ks_tb_khu_vuc)
    btn_w = QHBoxLayout()
    btn_add = QPushButton("Them khu vuc")
    btn_add.clicked.connect(lambda: KSD.add_khu_vuc_row(self))
    btn_del = QPushButton("Xoa khu vuc")
    btn_del.clicked.connect(lambda: KSD.del_khu_vuc_row(self))
    btn_w.addWidget(btn_add)
    btn_w.addWidget(btn_del)
    btn_w.addStretch()
    layout.addLayout(btn_w)


def _toggle_group_G(self, on):
    for w in (self.ks_tb_khoi_nha, self.ks_tb_khu_vuc):
        w.setVisible(on)


def _xuat_pc_stub(self, ma):
    """Xuất 1 trong 4 mẫu PC01/02/03/04 — Word docx."""
    from PyQt6.QtWidgets import QFileDialog, QMessageBox
    import mau_pccc
    try:
        data = KSD.thu_thap(self)
    except Exception as e:
        QMessageBox.critical(self, f"Loi doc data {ma}", str(e))
        return
    ten_ct = (data.get("kh_cty") or data.get("ten_cong_trinh")
              or "cong_trinh")[:50]
    default_name = f"{ma}_{ten_ct}.docx"
    path, _ = QFileDialog.getSaveFileName(
        self, f"Luu {ma}", default_name, "Word Files (*.docx)")
    if not path:
        return
    try:
        nguoi = getattr(self, "user", "") or ""
        if ma == "PC01":
            mau_pccc.xuat_pc01(data, path, nguoi_dung_dau=nguoi)
        elif ma == "PC02":
            mau_pccc.xuat_pc02(data, path, nguoi_kiem_tra=nguoi,
                                chuc_vu="Cán bộ PCCC cơ sở")
        elif ma == "PC03":
            mau_pccc.xuat_pc03(data, path)
        elif ma == "PC04":
            mau_pccc.xuat_pc04(data, path, nguoi_dung_dau=nguoi)
    except Exception as e:
        QMessageBox.critical(self, f"Loi xuat {ma}", str(e))
        return
    # Đính kèm lead folder Drive nếu có lead_id
    upload_msg = ""
    if getattr(self, "lead_id", None):
        try:
            import file_handle
            info = file_handle.upload_file_to_lead_folder(
                self.lead_id, path, doc_key=ma.lower())
            if info:
                upload_msg = f"<br>Da dinh kem vao Lead #{self.lead_id}."
        except Exception as e:
            upload_msg = f"<br>Loi upload Drive: {e}"
    QMessageBox.information(
        self, f"Xuat {ma} thanh cong",
        f"Da xuat: <b>{path}</b>{upload_msg}")
