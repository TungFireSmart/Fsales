"""
tu_van_pccc.py — Module Tư vấn & Báo giá PCCC tích hợp vào Fsales.

Mở từ nút "Tư vấn PCCC" trên sidebar chính. Cho phép sales:
    1. Nhập thông tin công trình + khách hàng
    2. Xem thiết bị/hệ thống PCCC BẮT BUỘC theo QCVN 10:2025/BCA
    3. Quản lý gian phòng để tính chính xác số đầu báo (TCVN 7568-14)
    4. Tính số đèn thoát nạn (TCVN 13456)
    5. Tự sinh báo giá: chọn model từ bảng giá Fsales (gia_tong_hop)
    6. Xuất Excel theo template công ty (bao_gia_mau.xlsx)
    7. Sinh nội dung tư vấn cho sales

KHÔNG lưu báo giá vào DB (theo yêu cầu) — chỉ xuất file Excel.
"""

import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIntValidator, QDoubleValidator, QFontMetrics
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QTabWidget, QGridLayout,
    QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QFileDialog,
    QMessageBox, QHeaderView, QAbstractItemView, QSplitter, QTextEdit,
    QSpinBox, QDoubleSpinBox, QSizePolicy, QScrollArea
)

import misc
from ui_theme import apply_ui_v2

import pccc_rules as R
from tu_van_pccc_excel import xuat_bao_gia_pccc, goi_y_ten_file
from UI.tu_van_pccc import Ui_TuVanPCCC_Window


# =====================================================================
# Helpers
# =====================================================================
def _fmt_money(n) -> str:
    """Format số kiểu Việt Nam: 1.234.567"""
    try:
        return f"{int(round(float(n))):,}".replace(",", ".")
    except (ValueError, TypeError):
        return "0"


def _make_spinbox(value=0, max_v=999_999_999) -> QSpinBox:
    sb = QSpinBox()
    sb.setRange(0, max_v)
    sb.setValue(int(value))
    sb.setMinimumHeight(28)
    return sb


def _make_dspin(value=0.0, max_v=9_999_999.0, dec=1) -> QDoubleSpinBox:
    sb = QDoubleSpinBox()
    sb.setRange(0, max_v)
    sb.setDecimals(dec)
    sb.setValue(float(value))
    sb.setMinimumHeight(28)
    return sb


# =====================================================================
# CỬA SỔ CHÍNH
# =====================================================================
class TuVanPCCC(QMainWindow):
    """Cửa sổ Tư vấn & Báo giá PCCC."""

    def __init__(self, user: str = "", user_phone: str = ""):
        super().__init__()
        self.user = user or "Phí Ngọc Tùng"
        self.user_phone = user_phone or "0934630366"

        self.setWindowTitle("Tư vấn & Báo giá PCCC — QCVN 10:2025/BCA")
        self.resize(1380, 820)

        # --- DATA ---
        self.catalog = []        # toàn bộ bảng giá đã đọc từ gia_tong_hop
        self.rooms = []          # [{ten, func, dt, loai}, ...]
        self.dt_khoi = 60.0
        self.dt_nhiet = 20.0
        self.thoat_nan = {
            "kc_sc": 15, "kc_exit": 30,
            "so_loi_ra_ngoai": 0, "so_cau_thang": 0,
            "so_loi_ra_phong": 0, "dai_hanh_lang": 0.0, "so_chieu_nghi": 0,
        }
        self.last_result = None  # kết quả phan_tich() gần nhất
        self.last_result_raw = None  # bản gốc trước khi apply optional_wants
        self.optional_wants = set()  # tập nhóm user chọn "Muốn trang bị"
        self.bg_rows = []        # danh sách báo giá hiện tại
        self.bg_group = 'khong_day'   # nhóm hệ báo cháy: khong_day | co_day | cuc_bo
        self._dt_user_modified = False
        self._hl_user_modified = False
        # Thông số cấp nước CC (TCVN 2622)
        self.bac_chiu_lua = "II"
        self.hang_sx = "C"
        self.he_so_hong = 1
        self.nguon_nuoc = "duong_ong"
        self.hong_per_floor = 0  # tính từ D, R bằng tinh_so_hong_nuoc

        # --- UI: load từ Qt Designer file (UI/tu_van_pccc.ui → UI/tu_van_pccc.py) ---
        self.uic = Ui_TuVanPCCC_Window()
        self.uic.setupUi(self)
        self._init_ui()
        apply_ui_v2(self)

        # --- Load bảng giá ---
        self._nap_bang_gia()

    # ---------------- INIT UI (sau setupUi) ----------------
    def _init_ui(self):
        """Bind widget alias + populate dữ liệu động + connect signals."""
        u = self.uic
        # ----- Alias widgets cho tương thích với code render hiện có -----
        self.cbo_cong_nang = u.cbo_cong_nang
        self.spin_dt = u.spin_dt
        self.spin_cao = u.spin_cao
        self.spin_tang = u.spin_tang
        self.spin_ham = u.spin_ham
        self.spin_so_phong = u.spin_so_phong
        self.spin_nguoi = u.spin_nguoi
        self.spin_chau = u.spin_chau
        self.lbl_nguoi = u.lbl_nguoi
        self.lbl_chau = u.lbl_chau
        # Hai field thêm bằng code: chiều dài + chiều rộng nhà
        # (bắt buộc khi công trình cần sprinkler/họng nước)
        self.spin_dai = _make_dspin(0)
        self.spin_rong = _make_dspin(0)
        u.form_ct.addRow("Chiều dài nhà (m):", self.spin_dai)
        u.form_ct.addRow("Chiều rộng nhà (m):", self.spin_rong)
        self.kh_ten = u.kh_ten
        self.kh_dc = u.kh_dc
        self.kh_dt = u.kh_dt
        self.kh_vv = u.kh_vv
        self.but_run = u.but_run
        self.lbl_status = u.lbl_status
        self.tabs = u.tabs
        # Tab 1
        self.lbl_summary = u.lbl_summary
        self.tb_thiet_bi = u.tb_thiet_bi
        self.lbl_note = u.lbl_note
        # Tab 2
        self.sp_dt_khoi = u.sp_dt_khoi
        self.sp_dt_nhiet = u.sp_dt_nhiet
        self.bk_n = u.bk_n
        self.bk_dt = u.bk_dt
        self.bk_func = u.bk_func
        self.bk_pre = u.bk_pre
        self.tb_rooms = u.tb_rooms
        self.lbl_phong_tong = u.lbl_phong_tong
        # Tab 3
        self.tn_kc_sc = u.tn_kc_sc
        self.tn_kc_exit = u.tn_kc_exit
        self.tn_loi_ra_ngoai = u.tn_loi_ra_ngoai
        self.tn_cau_thang = u.tn_cau_thang
        self.tn_loi_ra_phong = u.tn_loi_ra_phong
        self.tn_dai_hl = u.tn_dai_hl
        # Thêm field "Chiều rộng hành lang" programmatically
        self.tn_rong_hl = QDoubleSpinBox()
        self.tn_rong_hl.setRange(0.5, 99.0)
        self.tn_rong_hl.setDecimals(1)
        self.tn_rong_hl.setSuffix(" m")
        self.tn_rong_hl.setValue(3.0)
        self.tn_rong_hl.setToolTip(
            "Chiều rộng hành lang (mặc định 3m). "
            "Dùng để tính DT hành lang trừ vào DT phòng.")
        _form_tn = self.tn_dai_hl.parent().layout() if self.tn_dai_hl.parent() else None
        if _form_tn and hasattr(_form_tn, "addRow"):
            _form_tn.addRow("Chiều rộng hành lang:", self.tn_rong_hl)
        self.tn_chieu_nghi = u.tn_chieu_nghi
        self.lbl_tn_result = u.lbl_tn_result
        # Tab 4
        self.lbl_bg_info = u.lbl_bg_info
        self.but_doi_model = u.but_doi_model
        self.but_them_dong = u.but_them_dong
        self.but_xoa_dong = u.but_xoa_dong
        self.tb_bg = u.tb_bg
        self.lbl_tong = u.lbl_tong
        # Tab 5
        self.txt_tu_van = u.txt_tu_van

        # Tab thêm bằng code: "④ Cấp nước CC" — chèn trước Báo giá
        self._build_tab_cap_nuoc()
        # Tab thêm bằng code: "⑦ Hồ sơ pháp lý" — NĐ 105/2025
        self._build_tab_ho_so_phap_ly()

        # ----- Populate cbo_cong_nang (26 công năng từ R.CONG_NANG_LIST) -----
        self.cbo_cong_nang.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
        for cn in R.CONG_NANG_LIST:
            self.cbo_cong_nang.addItem(f"{cn['muc']:>2}. {cn['t']}", cn["k"])
            self.cbo_cong_nang.setItemData(
                self.cbo_cong_nang.count() - 1, cn["t"], Qt.ItemDataRole.ToolTipRole)
        fm = QFontMetrics(self.cbo_cong_nang.font())
        max_w = max(fm.horizontalAdvance(self.cbo_cong_nang.itemText(k))
                    for k in range(self.cbo_cong_nang.count()))
        self.cbo_cong_nang.view().setMinimumWidth(max_w + 60)
        self.cbo_cong_nang.view().setTextElideMode(Qt.TextElideMode.ElideNone)
        self.cbo_cong_nang.setToolTip(self.cbo_cong_nang.currentText())
        self.cbo_cong_nang.currentIndexChanged.connect(self._on_cong_nang_changed)
        self.cbo_cong_nang.currentIndexChanged.connect(
            lambda _i: self.cbo_cong_nang.setToolTip(self.cbo_cong_nang.currentText()))

        # ----- Populate bk_func (15 công năng phòng từ R.ROOM_FUNCS) -----
        for f in R.ROOM_FUNCS:
            self.bk_func.addItem(f["t"], f["k"])

        # ----- Connect nút Phân tích -----
        self.but_run.clicked.connect(self._on_run)

        # ----- Tab 1: setup tableWidget -----
        self.tb_thiet_bi.setColumnCount(5)
        self.tb_thiet_bi.setHorizontalHeaderLabels(
            ["#", "Hệ thống / thiết bị", "Yêu cầu", "Điều kiện áp dụng", "Căn cứ"])
        h = self.tb_thiet_bi.horizontalHeader()
        # Col 1 (Hệ thống/thiết bị): đặt rộng 625px (gấp 2.5x mặc định ~250px)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tb_thiet_bi.setColumnWidth(0, 40)
        self.tb_thiet_bi.setColumnWidth(1, 500)
        self.tb_thiet_bi.setColumnWidth(2, 200)
        self.tb_thiet_bi.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tb_thiet_bi.setWordWrap(True)
        # cellPressed fire ngay khi mouse-down — chắc chắn nhận event hơn
        # cellClicked (vốn chỉ fire sau release trên cùng cell)
        self.tb_thiet_bi.cellPressed.connect(self._on_thiet_bi_clicked)

        # ----- Tab 2: cov + bulk + tableWidget -----
        self.sp_dt_khoi.valueChanged.connect(self._on_cov_changed)
        self.sp_dt_nhiet.valueChanged.connect(self._on_cov_changed)
        u.but_bulk_add.clicked.connect(self._bulk_add_rooms)
        u.but_gen_rooms.clicked.connect(self._gen_rooms_from_count)
        u.but_add_room.clicked.connect(self._add_one_room)

        self.tb_rooms.setColumnCount(7)
        self.tb_rooms.setHorizontalHeaderLabels(
            ["#", "Tên phòng", "Công năng", "Diện tích (m²)", "Loại đầu báo",
             "SL đầu báo", ""])
        self.tb_rooms.setColumnWidth(0, 40)
        self.tb_rooms.setColumnWidth(2, 280)   # Công năng — đủ rộng cho text
        self.tb_rooms.setColumnWidth(3, 110)
        self.tb_rooms.setColumnWidth(4, 130)
        self.tb_rooms.setColumnWidth(5, 110)
        self.tb_rooms.setColumnWidth(6, 60)
        h2 = self.tb_rooms.horizontalHeader()
        h2.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # ----- Tab 3: connect thoát nạn signals -----
        for s in (self.tn_kc_sc, self.tn_kc_exit, self.tn_loi_ra_ngoai,
                  self.tn_cau_thang, self.tn_loi_ra_phong, self.tn_dai_hl,
                  self.tn_chieu_nghi, self.tn_rong_hl):
            s.valueChanged.connect(self._on_tn_changed)

        # ----- Tab 4: setup tb_bg — đồng bộ độ rộng cột với Fsales quotation form
        # Fsales: [300, 90, 90, 60, 80, 130, 90] cho 7 cột sản phẩm
        # + thêm Stt (50) ở đầu và Thành tiền (130) ở cuối
        # 10 cột: Stt, Mô tả, Model, Nhãn hiệu, ĐV, SL, Đơn giá, Nhân công, Thuế, Thành tiền
        self.tb_bg.setColumnCount(10)
        self.tb_bg.setHorizontalHeaderLabels([
            "Stt", "Mô tả sản phẩm", "Model", "Nhãn hiệu", "ĐV tính",
            "Số lượng", "Đơn giá", "Nhân công", "Thuế", "Thành tiền"])
        widths = [50, 300, 90, 90, 60, 70, 110, 100, 110, 130]
        for i, ww in enumerate(widths):
            self.tb_bg.setColumnWidth(i, ww)
        self.tb_bg.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self.tb_bg.verticalHeader().setVisible(False)
        self.tb_bg.verticalHeader().setDefaultSectionSize(28)
        self.tb_bg.setWordWrap(False)
        self.tb_bg.setAlternatingRowColors(True)
        self.tb_bg.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.SelectedClicked)
        self.tb_bg.itemChanged.connect(self._on_bg_item_changed)
        self.tb_bg.cellDoubleClicked.connect(self._on_bg_double_click)

        # Combobox chọn nhóm hệ báo cháy (chèn vào toolbar của tab Báo giá)
        self.cbo_bg_group = QComboBox()
        for key in ("khong_day", "co_day", "cuc_bo"):
            self.cbo_bg_group.addItem(R.BAO_CHAY_GROUP_LABELS[key], key)
        self.cbo_bg_group.setToolTip(
            "Nhóm hệ báo cháy: tất cả thiết bị báo cháy + truyền tin sẽ "
            "thuộc cùng 1 nhóm (không trộn lẫn)")
        self.cbo_bg_group.setMinimumHeight(28)
        # Tìm layout chứa lbl_bg_info để chèn combobox vào ngay sau
        bar = self.lbl_bg_info.parent().layout()
        if bar is not None:
            # Tìm index của lbl_bg_info, chèn label + cbo_bg_group ngay sau
            for idx in range(bar.count()):
                if bar.itemAt(idx).widget() is self.lbl_bg_info:
                    bar.insertWidget(idx + 1, QLabel("Nhóm BC:"))
                    bar.insertWidget(idx + 2, self.cbo_bg_group)
                    break
        self.cbo_bg_group.currentIndexChanged.connect(self._on_bg_group_changed)

        self.but_doi_model.clicked.connect(self._doi_model_dialog)
        self.but_them_dong.clicked.connect(self._them_dong_bg)
        self.but_xoa_dong.clicked.connect(self._xoa_dong_bg)
        u.but_xuat_excel.clicked.connect(self._xuat_excel)
        u.but_in_pdf.clicked.connect(self._in_pdf)

        # Init: ẩn/hiện field nguoi/chau theo công năng đầu tiên
        self._on_cong_nang_changed()

        # ----- Auto re-run khi đổi input + auto-fill DT/HL + reset border đỏ -----
        for sp in (self.spin_dt, self.spin_cao, self.spin_dai, self.spin_rong,
                   self.spin_tang, self.spin_ham, self.spin_so_phong,
                   self.spin_nguoi, self.spin_chau):
            sp.editingFinished.connect(self._on_input_changed)
        self.cbo_cong_nang.currentIndexChanged.connect(
            lambda _i: self._on_input_changed())
        # Auto-fill DT
        for sp in (self.spin_dai, self.spin_rong, self.spin_tang, self.spin_ham):
            sp.editingFinished.connect(self._auto_fill_dt)
        self.spin_dt.editingFinished.connect(self._on_dt_edited_by_user)
        # Auto-fill HL
        for sp in (self.spin_dai, self.spin_tang, self.spin_ham, self.spin_so_phong):
            sp.editingFinished.connect(self._auto_fill_hl_dai)
        self.cbo_cong_nang.currentIndexChanged.connect(
            lambda _i: self._auto_fill_hl_dai())
        # Reset border đỏ khi user gõ vào field thiếu
        for w in (self.cbo_cong_nang, self.spin_dt, self.spin_cao,
                  self.spin_dai, self.spin_rong, self.spin_tang,
                  self.spin_nguoi, self.spin_chau):
            if hasattr(w, "editingFinished"):
                w.editingFinished.connect(lambda w=w: w.setStyleSheet(""))
            elif hasattr(w, "currentIndexChanged"):
                w.currentIndexChanged.connect(lambda _i, w=w: w.setStyleSheet(""))

    # ---------------- TAB CẤP NƯỚC CC ----------------
    def _build_tab_cap_nuoc(self):
        """Tạo tab 'Cấp nước CC' bằng code, chèn trước tab Báo giá.
        Wrap nội dung trong QScrollArea vì phần thuyết minh có thể dài."""
        tab = QWidget()
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        outer.addWidget(scroll)

        inner = QWidget()
        scroll.setWidget(inner)
        v = QVBoxLayout(inner)
        v.setContentsMargins(10, 10, 10, 10)

        gb = QGroupBox("Thông số cấp nước chữa cháy (QCVN 10:2025/BCA + QCVN 06:2022)")
        form = QFormLayout(gb)

        # Bậc chịu lửa
        self.cbo_bac_chiu_lua = QComboBox()
        for b in R.BAC_CHIU_LUA:
            self.cbo_bac_chiu_lua.addItem(f"Bậc {b}", b)
        self.cbo_bac_chiu_lua.setCurrentIndex(1)  # mặc định II
        form.addRow("Bậc chịu lửa:", self.cbo_bac_chiu_lua)

        # Hạng sản xuất (chỉ enable cho công năng SX/kho)
        self.cbo_hang_sx = QComboBox()
        for h in R.HANG_SX:
            self.cbo_hang_sx.addItem(f"Hạng {h}", h)
        self.cbo_hang_sx.setCurrentIndex(2)  # mặc định C
        form.addRow("Hạng sản xuất:", self.cbo_hang_sx)

        # Cấp nguy hiểm cháy của kết cấu (QCVN 06:2022, dùng cho Bảng H.6)
        self.cbo_cap_nhc = QComboBox()
        self.cbo_cap_nhc.addItem("S0 - Không nguy hiểm cháy (kết cấu không cháy)", "S0")
        self.cbo_cap_nhc.addItem("S1 - Nguy hiểm cháy thấp", "S1")
        self.cbo_cap_nhc.addItem("S2 - Nguy hiểm cháy trung bình", "S2")
        self.cbo_cap_nhc.addItem("S3 - Nguy hiểm cháy cao", "S3")
        self.cbo_cap_nhc.setCurrentIndex(0)
        self.cbo_cap_nhc.setToolTip(
            "QCVN 06:2022 — Cấp NHC kết cấu (S0/S1/S2/S3). "
            "Chỉ áp dụng cho nhà SX/kho (Bảng H.6 QCVN 10:2025).")
        form.addRow("Cấp nguy hiểm KC:", self.cbo_cap_nhc)

        # Hệ số họng/điểm — read-only, tự tính
        self.spin_he_so_hong = QSpinBox()
        self.spin_he_so_hong.setRange(1, 3)
        self.spin_he_so_hong.setValue(1)
        self.spin_he_so_hong.setReadOnly(True)
        self.spin_he_so_hong.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.spin_he_so_hong.setStyleSheet("background:#f3f4f6; color:#374151;")
        self.spin_he_so_hong.setToolTip(
            "Hệ số họng/điểm tự tính theo QCVN 10:2025 Bảng H.5/H.6 — không sửa được.")
        form.addRow("Hệ số họng/điểm (auto):", self.spin_he_so_hong)

        # Chiều dài hành lang trên 1 tầng
        self.spin_hl_dai = QDoubleSpinBox()
        self.spin_hl_dai.setRange(0.0, 9999.0)
        self.spin_hl_dai.setDecimals(1)
        self.spin_hl_dai.setSuffix(" m")
        self.spin_hl_dai.setValue(0.0)
        self.spin_hl_dai.setToolTip(
            "QCVN 10:2025 Bảng H.5 mục 1 + H.2.18. "
            "Mặc định auto theo công năng (chung cư=D/3, công cộng=D).")
        form.addRow("Chiều dài hành lang trên 1 tầng:", self.spin_hl_dai)

        # Nguồn cấp nước
        self.cbo_nguon_nuoc = QComboBox()
        self.cbo_nguon_nuoc.addItem("Đường ống đô thị", "duong_ong")
        self.cbo_nguon_nuoc.addItem("Bể chứa riêng", "be_chua")
        self.cbo_nguon_nuoc.addItem("Sông / hồ / ao", "song_ho")
        form.addRow("Nguồn cấp nước:", self.cbo_nguon_nuoc)

        v.addWidget(gb)

        # Kết quả tính
        self.lbl_cap_nuoc_result = QLabel(
            "Bấm <b>⚡ Phân tích</b> để tính số họng nước.")
        self.lbl_cap_nuoc_result.setStyleSheet(
            "padding:12px; background:#eff6ff; border-radius:6px;")
        self.lbl_cap_nuoc_result.setWordWrap(True)
        v.addWidget(self.lbl_cap_nuoc_result)

        v.addStretch()

        # Chèn tab vào tabs, trước tab Báo giá (index 3)
        bg_index = self.tabs.indexOf(self.tab_bao_gia) if hasattr(self, "tab_bao_gia") else 3
        try:
            bg_index = self.tabs.indexOf(self.uic.tab_bao_gia)
        except Exception:
            bg_index = 3
        self.tabs.insertTab(bg_index, tab, "④ Cấp nước CC")
        # Đánh số lại các tab sau
        self.tabs.setTabText(bg_index + 1, "⑤ Báo giá")
        self.tabs.setTabText(bg_index + 2, "⑥ Nội dung tư vấn")

        # Wire signals — cập nhật state khi user đổi giá trị
        self.cbo_bac_chiu_lua.currentIndexChanged.connect(self._on_cap_nuoc_changed)
        self.cbo_hang_sx.currentIndexChanged.connect(self._on_cap_nuoc_changed)
        self.cbo_cap_nhc.currentIndexChanged.connect(self._on_cap_nuoc_changed)
        # spin_he_so_hong: read-only, không cần signal
        self.spin_hl_dai.editingFinished.connect(self._on_cap_nuoc_changed)
        self.spin_hl_dai.editingFinished.connect(self._on_hl_edited_by_user)
        self.cbo_nguon_nuoc.currentIndexChanged.connect(self._on_cap_nuoc_changed)

    def _on_cap_nuoc_changed(self):
        """Cập nhật state khi user đổi giá trị trên tab Cấp nước CC."""
        self.bac_chiu_lua = self.cbo_bac_chiu_lua.currentData()
        self.hang_sx = self.cbo_hang_sx.currentData()
        self.cap_nhc_kc = self.cbo_cap_nhc.currentData()
        # he_so_hong read-only, tự sync trong _render_cap_nuoc
        self.hl_dai = float(self.spin_hl_dai.value())
        self.nguon_nuoc = self.cbo_nguon_nuoc.currentData()
        # Enable/disable hạng SX + cấp NHC theo công năng (SX/kho)
        cn = self._current_cong_nang()
        is_sx = bool(cn and cn["k"] in R.CN_SAN_XUAT_KHO)
        self.cbo_hang_sx.setEnabled(is_sx)
        self.cbo_cap_nhc.setEnabled(is_sx)
        # Re-render nếu đã phân tích
        if self.last_result:
            self._render_cap_nuoc()
            self._render_bao_gia()

    def _render_cap_nuoc(self):
        """Hiển thị kết quả tính số họng + ống trục chính + sprinkler."""
        i = self._get_input()
        cn = self._current_cong_nang()
        if not cn or i["dai"] <= 0 or i["rong"] <= 0:
            self.lbl_cap_nuoc_result.setText(
                "⚠ Cần nhập đầy đủ <b>Chiều dài</b>, <b>Chiều rộng</b> ở cột trái.")
            return

        floors = max(1, int(i["tang"]) + int(i["ham"]))
        tang_total = int(i["tang"]) + int(i["ham"])
        hl_dai = float(self.spin_hl_dai.value())

        # Auto-gợi ý hệ số họng/điểm theo QCVN 10:2025 Bảng H.5/H.6
        goi_y = R.goi_y_he_so_hong_per_diem(
            cn["k"], i["dai"], i["rong"],
            cao_pccc=float(i["cao"]),
            tang_total=tang_total,
            nguoi=int(i.get("nguoi") or 0),
            hanh_lang_dai=hl_dai,
            bac_chiu_lua=getattr(self, "bac_chiu_lua", "II"),
            hang_nguy_hiem=getattr(self, "hang_sx", "C"),
            cap_nhc_kc=getattr(self, "cap_nhc_kc", "S0"))
        # LUÔN sync hệ số họng theo bảng (read-only)
        self.he_so_hong = int(goi_y["he_so"])
        self.spin_he_so_hong.blockSignals(True)
        self.spin_he_so_hong.setValue(self.he_so_hong)
        self.spin_he_so_hong.blockSignals(False)
        self.q_per_jet = float(goi_y.get("q_per_jet", 2.5))

        # Tính số họng theo hình học
        kq = R.tinh_so_hong_nuoc(i["dai"], i["rong"], floors, self.he_so_hong)
        self.hong_per_floor = kq["n_per_floor"]

        # Chọn DN cuộn vòi
        dn, dn_basis = R.chon_dn_hong(i["cao"], self.he_so_hong, cn["k"],
                                      self.q_per_jet)

        html = (
            f"<h4 style='color:#0f766e;margin:0'>💧 HỆ THỐNG HỌNG NƯỚC "
            f"({goi_y['source']})</h4>"
            f"<b>Kích thước nhà:</b> {i['dai']:.1f}m × {i['rong']:.1f}m × {floors} tầng<br>"
            f"<b>Trường hợp:</b> {kq['case']}<br>"
            f"<b>Công thức:</b> {kq['formula']}<br>"
            f"<b>Họng/điểm × Lưu lượng tia:</b> "
            f"<b>{self.he_so_hong} × {self.q_per_jet:g} L/s</b><br>"
            f"<i>Căn cứ: {goi_y['basis']}</i><br>"
            f"<b>Đường kính cuộn vòi:</b> {dn.upper()} <i>({dn_basis})</i><br>"
            f"<b>📊 TỔNG SỐ HỌNG: {kq['total']} bộ</b>"
        )
        warnings_all = list(kq["warnings"]) + list(goi_y["ghi_chu"])
        if warnings_all:
            html += "<br>" + "<br>".join(warnings_all)

        # Phần ống trục chính họng nước
        has_sprk = False
        if self.last_result:
            has_sprk = any(x["nhom"] == "chua_chay" and x["req"]
                           for x in self.last_result["items"])
        is_nha_o = (cn["k"] == "chung_cu")
        kq_ong = R.tinh_chieu_dai_ong_truc_chinh(
            D=i["dai"], R=i["rong"], cao_pccc=i["cao"], floors=floors,
            n_hong=kq["total"], he_so_hong_per_diem=self.he_so_hong,
            is_nha_o=is_nha_o, hanh_lang_dai=hl_dai,
            has_sprinkler=has_sprk)
        dn_truc = "DN80" if dn == "dn65" else "DN65"
        html += (
            f"<br><br><h4 style='color:#0f766e;margin:0'>"
            f"🔧 ỐNG TRỤC CHÍNH (QCVN 10:2025 H.2.11 + H.2.16)</h4>"
            f"<b>Số trục đứng:</b> {kq_ong['n_truc']} "
            f"({'có dùng họng kép' if kq_ong['cho_phep_hong_kep'] else 'không họng kép'})<br>"
            f"<b>Chiều cao trục đứng:</b> {kq_ong['H_truc_dung']:.1f}m<br>"
            f"<b>Mạng vòng:</b> "
            f"{'CÓ' if kq_ong['can_mach_vong'] else 'KHÔNG cần'}<br>"
            f"<b>Đường kính ống trục chính:</b> {dn_truc}<br>"
            f"<b>📐 Chi tiết cách tính:</b><br>"
            + "<br>".join("&nbsp;&nbsp;" + g for g in kq_ong["ghi_chu"])
        )

        # Phần sprinkler
        if has_sprk:
            sprk = R.tinh_sprinkler(i["dt"], cn["k"], self.rooms)
            html += (
                f"<br><br><h4 style='color:#0f766e;margin:0'>"
                f"💦 HỆ THỐNG SPRINKLER (TCVN 7336)</h4>"
                f"<b>Nhóm nguy cơ:</b> Nhóm {sprk['nhom']} "
                f"<i>(TCVN 7336 Phụ lục A)</i><br>"
                f"<b>Khoảng cách tối đa giữa sprk:</b> "
                f"{3 if sprk['nhom'] in ('4.1','4.2') else 4} m "
                f"<i>(Bảng 1)</i><br>"
                f"<b>Cường độ phun:</b> {sprk['cd_phun']} L/s·m²<br>"
                f"<b>Lưu lượng tính toán:</b> {sprk['luu_luong']} L/s<br>"
                f"<b>Thời gian phun:</b> {sprk['t_phun']} phút<br>"
                f"<b>📊 TỔNG SỐ ĐẦU PHUN:</b> {sprk['cong_thuc']}<br>"
                f"<b>💧 Bể nước:</b> {sprk['the_tich_be']} m³"
            )
            if i["dai"] > 0 and i["cao"] > 0:
                kq_sprk = R.tinh_chieu_dai_ong_sprinkler(
                    n_sprk_total=sprk["n_sprk"],
                    dt_per_sprk=sprk["dt_per_sprk"],
                    D=i["dai"], R=i["rong"],
                    cao_pccc=i["cao"], floors=floors,
                    sprk_per_nhanh=5)
                # Gộp DN nhánh + phân phối
                from collections import defaultdict as _dd
                _all = _dd(float)
                for dn_c, L in kq_sprk['L_per_dn'].items():
                    _all[dn_c] += L
                for dn_c, L in kq_sprk.get('L_pp_per_dn', {}).items():
                    _all[dn_c] += L
                pipe_summary = ", ".join(
                    f"{dn_c.upper()}={_all[dn_c]:.0f}m"
                    for dn_c in sorted(_all.keys(),
                                       key=lambda x: int(x.replace("dn", ""))))
                html += (
                    f"<br><br><h4 style='color:#0f766e;margin:0'>"
                    f"🔧 ỐNG SPRINKLER (TCVN 7336 Bảng B.3)</h4>"
                    f"<b>Trục đứng:</b> {kq_sprk['dn_truc_label']} × "
                    f"{kq_sprk['L_truc']:.0f}m<br>"
                    f"<b>Ống nhánh + phân phối (taper):</b> {pipe_summary}<br>"
                    f"<b>Số cụm van điều khiển:</b> {kq_sprk['n_zone']} cụm<br>"
                    f"<b>📐 Chi tiết cách tính:</b><br>"
                    + "<br>".join("&nbsp;&nbsp;" + g
                                  for g in kq_sprk["ghi_chu"])
                )

        # ---- Block tinh cum bom (TCVN 7336 B.3.8 + B.3.9) ----
        try:
            i_for_bom = dict(i)
            i_for_bom["cong_nang_k"] = cn["k"]
            i_for_bom["he_so_hong_per_diem"] = self.he_so_hong
            i_for_bom["q_per_jet"] = self.q_per_jet
            i_for_bom["hong_per_floor"] = self.hong_per_floor
            i_for_bom["hanh_lang_dai"] = hl_dai
            items_for_bom = (self.last_result["items"]
                             if self.last_result else [])
            slots_all = R.build_slots(items_for_bom, i_for_bom)
        except Exception:
            slots_all = []
        bom_slot = next(
            (s for s in slots_all
             if s.get("loai") == "cum_bom" and "bom_info" in s),
            None)
        if bom_slot:
            b = bom_slot["bom_info"]
            html += (
                "<br><br><h4 style='color:#7c2d12;margin:0'>"
                "⚙ CỤM BƠM CHỮA CHÁY (TCVN 7336 B.3.8 + B.3.9)</h4>"
                + "<b>Khuyến nghị: Q ≥ " + str(b["Q_ls"])
                + " L/s (" + str(b["Q_m3h"])
                + " m³/h), H ≥ " + str(b["H_m"]) + " m</b><br>"
                + b["thuyet_minh"]
                + "<br><i>Sales chọn model thực tế (Pentax/Ebara/Wilo/...) "
                "qua nút <b>'Đổi model'</b> ở tab Báo giá với Q-H ≥ giá trị trên.</i>"
            )

        self.lbl_cap_nuoc_result.setText(html)

    # ---------------- HELPERS ----------------
    def _on_input_changed(self):
        """Auto re-run sau khi user đổi input — chỉ khi đã phân tích lần đầu."""
        if self.last_result:
            self._on_run()

    def _auto_fill_dt(self):
        """Tự fill DT sàn = D × R × số tầng nếu user chưa sửa tay."""
        if self._dt_user_modified:
            return
        D = float(self.spin_dai.value())
        R_ = float(self.spin_rong.value())
        floors = int(self.spin_tang.value()) + int(self.spin_ham.value())
        if D > 0 and R_ > 0 and floors > 0:
            dt = D * R_ * floors
            self.spin_dt.blockSignals(True)
            self.spin_dt.setValue(dt)
            self.spin_dt.blockSignals(False)

    def _on_dt_edited_by_user(self):
        self._dt_user_modified = True

    def _auto_fill_hl_dai(self):
        """Tự fill chiều dài hành lang theo công năng (auto_hl_dai)."""
        if self._hl_user_modified:
            return
        cn = self._current_cong_nang()
        if cn is None:
            return
        D = float(self.spin_dai.value())
        if D <= 0:
            return
        so_phong = int(self.spin_so_phong.value() or 0)
        floors = int(self.spin_tang.value()) + int(self.spin_ham.value())
        hl_new = R.auto_hl_dai(cn["k"], D, so_phong, max(1, floors))
        if hasattr(self, "spin_hl_dai"):
            self.spin_hl_dai.blockSignals(True)
            self.spin_hl_dai.setValue(hl_new)
            self.spin_hl_dai.blockSignals(False)
            self.hl_dai = hl_new

    def _on_hl_edited_by_user(self):
        self._hl_user_modified = True

    def _validate_inputs(self) -> list:
        """Quét các field bắt buộc. Trả list (widget, label) thiếu."""
        missing = []
        cn = self._current_cong_nang()
        if cn is None:
            missing.append((self.cbo_cong_nang, "Công năng sử dụng"))
        if float(self.spin_dai.value()) <= 0:
            missing.append((self.spin_dai, "Chiều dài nhà"))
        if float(self.spin_rong.value()) <= 0:
            missing.append((self.spin_rong, "Chiều rộng nhà"))
        if float(self.spin_cao.value()) <= 0:
            missing.append((self.spin_cao, "Chiều cao PCCC"))
        if int(self.spin_tang.value()) < 1:
            missing.append((self.spin_tang, "Số tầng nổi"))
        if cn:
            if cn.get("nguoi") and int(self.spin_nguoi.value()) < 1:
                missing.append((self.spin_nguoi, "Số người / chỗ ngồi"))
            if cn.get("chau") and int(self.spin_chau.value()) < 1:
                missing.append((self.spin_chau, "Số cháu"))
        return missing

    def _highlight_missing(self, missing):
        """Tô border đỏ các widget thiếu, reset các widget khác."""
        err_style = "border: 2px solid #ef4444; background-color: #fef2f2;"
        all_widgets = (
            self.cbo_cong_nang, self.spin_dai, self.spin_rong, self.spin_cao,
            self.spin_tang, self.spin_ham, self.spin_dt, self.spin_so_phong,
            self.spin_nguoi, self.spin_chau,
        )
        missing_widgets = {w for w, _ in missing}
        for w in all_widgets:
            if w in missing_widgets:
                w.setStyleSheet(err_style)
            else:
                w.setStyleSheet("")

    def _current_cong_nang(self) -> dict:
        k = self.cbo_cong_nang.currentData()
        return R.get_cong_nang(k)

    def _get_input(self) -> dict:
        return {
            "dt": float(self.spin_dt.value()),
            "cao": float(self.spin_cao.value()),
            "tang": int(self.spin_tang.value()),
            "ham": int(self.spin_ham.value()),
            "nguoi": int(self.spin_nguoi.value()),
            "chau": int(self.spin_chau.value()),
            "dai": float(self.spin_dai.value()),
            "rong": float(self.spin_rong.value()),
            "so_phong": int(self.spin_so_phong.value()),
            # so_cau_thang lấy từ tab Thoát nạn (mặc định 1 nếu chưa nhập)
            "so_cau_thang": int(self.tn_cau_thang.value()) or 1,
            # Thông số cấp nước CC (cho build_hong_nuoc_slots)
            "cong_nang_k": self._current_cong_nang()["k"]
                if self._current_cong_nang() else "",
            "he_so_hong_per_diem": getattr(self, "he_so_hong", 1),
            "q_per_jet": getattr(self, "q_per_jet", 2.5),
            "hong_per_floor": getattr(self, "hong_per_floor", 0),
            "hanh_lang_dai": getattr(self, "hl_dai", 0.0),
            "bac_chiu_lua": getattr(self, "bac_chiu_lua", "II"),
            "hang_sx": getattr(self, "hang_sx", "C"),
            "cap_nhc_kc": getattr(self, "cap_nhc_kc", "S0"),
            "nguon_nuoc": getattr(self, "nguon_nuoc", "duong_ong"),
            "binhPerFloor": 100,
            "binhReserve": 10,
        }

    def _on_cong_nang_changed(self):
        cn = self._current_cong_nang()
        if cn is None:
            return
        need_nguoi = cn.get("nguoi", False)
        need_chau = cn.get("chau", False)
        self.lbl_nguoi.setVisible(need_nguoi)
        self.spin_nguoi.setVisible(need_nguoi)
        self.lbl_chau.setVisible(need_chau)
        self.spin_chau.setVisible(need_chau)

    # ---------------- NẠP BẢNG GIÁ ----------------
    def _nap_bang_gia(self):
        """Đọc gia_tong_hop, phân loại nhom/loai từ tên SP."""
        try:
            rows = misc.sql_all(
                "SELECT ten_san_pham, model, nhan_hieu, xuat_xu, don_vi, "
                "gia_ban_le, vat, nhan_cong FROM gia_tong_hop",
                None, default=[]) or []
        except Exception as e:
            QMessageBox.warning(self, "Lỗi kết nối DB",
                                f"Không thể đọc bảng giá:\n{e}\n\nKiểm tra kết nối DB Fsales.")
            self.catalog = []
            self.lbl_status.setText("⚠️ Chưa nạp được bảng giá.")
            return

        catalog = []
        for r in rows:
            try:
                ten = str(r[0] or "").strip()
                if not ten:
                    continue
                cls = R.classify_nhom(ten)
                model = str(r[1] or "")

                # nhan_cong có thể là số hoặc text — parse an toàn
                try:
                    nhan_cong_unit = int(float(str(r[7]).replace(",", "")) or 0) if r[7] else 0
                except (ValueError, TypeError):
                    nhan_cong_unit = 0

                catalog.append({
                    "ten": ten,
                    "model": model,
                    "hieu": str(r[2] or ""),
                    "xuat_xu": str(r[3] or ""),
                    "dv": str(r[4] or ""),
                    "gia": int(r[5] or 0),   # gia_ban_le
                    "vat": int(r[6] or 8),
                    "nhan_cong_unit": nhan_cong_unit,  # đơn giá nhân công/SP
                    "nhom": cls["nhom"],
                    "loai": cls["loai"],
                    "bg_groups": R.bao_chay_groups_of(model),
                })
            except Exception as e:
                print(f"Bỏ qua SP lỗi: {e}")
                continue
        self.catalog = catalog
        self.lbl_status.setText(
            f"✅ Đã nạp <b>{len(catalog)}</b> sản phẩm từ bảng giá Fsales.")

    def _find_product(self, nhom: str, loai: str = None, group: str = None,
                      prefer: list = None) -> int:
        """Tìm SP đầu tiên khớp nhom/loai (+ bg_group nếu có).
        prefer: list keyword (lowercase) ưu tiên — SP nào match nhiều keyword
        nhất trong tên+model sẽ được chọn."""
        matches = []
        for idx, c in enumerate(self.catalog):
            if c["nhom"] != nhom:
                continue
            if loai is not None and c["loai"] != loai:
                continue
            if group is not None and c.get("bg_groups") and group not in c["bg_groups"]:
                continue
            matches.append(idx)
        if not matches:
            return -1
        if not prefer:
            return matches[0]
        def _score(i):
            c = self.catalog[i]
            s = (str(c.get("ten", "")) + " " + str(c.get("model", ""))).lower()
            return sum(1 for kw in prefer if kw in s)
        best = max(matches, key=_score)
        return best if _score(best) > 0 else matches[0]

    def _find_by_model(self, model: str) -> int:
        """Tìm SP theo model (normalized). Trả index hoặc -1."""
        target = R.normalize_model(model)
        if not target:
            return -1
        for idx, c in enumerate(self.catalog):
            if R.normalize_model(c["model"]) == target:
                return idx
        return -1

    def _sync_bg_group_combo(self):
        """Đồng bộ combobox group với self.bg_group (không trigger signal)."""
        if not hasattr(self, "cbo_bg_group"):
            return
        self.cbo_bg_group.blockSignals(True)
        for k in range(self.cbo_bg_group.count()):
            if self.cbo_bg_group.itemData(k) == self.bg_group:
                self.cbo_bg_group.setCurrentIndex(k)
                break
        self.cbo_bg_group.blockSignals(False)

    def _on_bg_group_changed(self, _idx: int):
        """User đổi nhóm hệ báo cháy từ combobox -> confirm + đổi cả hệ."""
        new_group = self.cbo_bg_group.currentData()
        if new_group == self.bg_group:
            return
        # Cảnh báo: nhóm cục bộ chỉ áp dụng cho công trình quy mô nhỏ
        if new_group == "cuc_bo" and self.last_result:
            if self.last_result["bcState"] != "doc_lap":
                ans = QMessageBox.question(
                    self, "Cảnh báo",
                    "Công trình này KHÔNG thuộc diện được dùng thiết bị báo cháy cục bộ "
                    "(quy mô lớn theo QCVN 10). Vẫn muốn chuyển?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No)
                if ans != QMessageBox.StandardButton.Yes:
                    self._sync_bg_group_combo()  # revert
                    return
        # Confirm đổi cả hệ
        label_new = R.BAO_CHAY_GROUP_LABELS[new_group]
        ans = QMessageBox.question(
            self, "Đổi nhóm hệ báo cháy",
            f"Sẽ thay thế TẤT CẢ thiết bị báo cháy + truyền tin sang nhóm "
            f"<b>{label_new}</b>. Tiếp tục?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes)
        if ans != QMessageBox.StandardButton.Yes:
            self._sync_bg_group_combo()
            return
        self.bg_group = new_group
        # Re-render báo giá với group mới
        if self.last_result:
            self._render_bao_gia()

    def _need_group(self, nhom: str) -> bool:
        """Có cần lọc theo bg_group cho nhóm này không?"""
        return nhom in ("bao_chay", "bao_chay_doc_lap", "truyen_tin")

    # ---------------- ĐỘNG CƠ CHÍNH ----------------
    def _on_run(self):
        if not self.catalog:
            QMessageBox.warning(self, "Chưa có bảng giá",
                                "Bảng giá Fsales rỗng — kiểm tra kết nối DB.")
            return

        # Validation: quét các field bắt buộc
        missing = self._validate_inputs()
        self._highlight_missing(missing)
        if missing:
            ds = "<br>".join(f"• <b>{lbl}</b>" for _, lbl in missing)
            QMessageBox.warning(
                self, "Thiếu thông tin bắt buộc",
                f"Vui lòng nhập đầy đủ các trường sau:<br><br>{ds}<br><br>"
                f"<i>Các field thiếu đã được tô đỏ ở cột trái.</i>")
            return

        cn = self._current_cong_nang()
        if cn is None:
            return

        # Safety net: auto-fill DT + HL nếu vẫn = 0
        self._auto_fill_dt()
        self._auto_fill_hl_dai()

        i = self._get_input()
        # Nếu chưa có phòng nhưng có "Số phòng" → tự sinh
        if not self.rooms and self.spin_so_phong.value() > 0:
            self._gen_rooms_from_count(silent=True)

        try:
            res = R.phan_tich(cn["k"], i)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi phân tích", str(e))
            return

        # Validate: công trình cần sprinkler hoặc họng nước → bắt buộc khai báo
        # chiều dài + chiều rộng nhà (cần để tính số lượng cuộn vòi, bố trí họng…)
        need_water = any(
            x["req"] and x["nhom"] in ("chua_chay", "hong_nuoc")
            for x in res["items"])
        if need_water and (i["dai"] <= 0 or i["rong"] <= 0):
            QMessageBox.warning(
                self, "Thiếu thông tin",
                "Công trình của Quý khách cần trang bị hệ thống chữa cháy tự động "
                "hoặc họng nước chữa cháy trong nhà. "
                "<br><br>Vui lòng nhập <b>Chiều dài nhà</b> và <b>Chiều rộng nhà</b> "
                "(> 0 m) ở cột trái để tính số lượng cuộn vòi & bố trí họng nước.")
            return

        self.last_result_raw = res
        self._apply_optional_wants_to_last_result()
        res = self.last_result
        # Tự chọn nhóm hệ báo cháy theo bcState:
        # doc_lap -> cục bộ; tu_dong -> giữ nguyên user-selected (mặc định không dây)
        if res["bcState"] == "doc_lap":
            self.bg_group = "cuc_bo"
        elif res["bcState"] == "tu_dong" and self.bg_group == "cuc_bo":
            # User trước đó chọn cục bộ nhưng giờ công trình đủ lớn -> reset về mặc định
            self.bg_group = "khong_day"
        self._sync_bg_group_combo()

        # Tự điền giá trị mặc định cho tab Thoát nạn (chỉ khi user chưa nhập)
        self._apply_thoat_nan_defaults(i)

        self._render_thiet_bi()
        if hasattr(self, "lbl_cap_nuoc_result"):
            self._render_cap_nuoc()
        self._render_bao_gia()
        self._render_tu_van()
        if hasattr(self, "lbl_phan_loai_nd105"):
            self._render_ho_so_phap_ly()
        self.tabs.setCurrentIndex(0)

    def _apply_thoat_nan_defaults(self, i: dict):
        """Áp giá trị mặc định cho các field thoát nạn nếu còn = 0.
        Quy ước:
          - lối ra ngoài = 2, cầu thang = 1
          - cửa phòng ra hành lang = số gian phòng
          - chiếu nghỉ cầu thang = số tầng (nổi + hầm)
          - tổng chiều dài hành lang = HL_trên_1_tầng × số_tầng (đồng bộ với
            tab Cấp nước CC, LUÔN sync chứ không chỉ khi = 0)
          - chiều rộng hành lang = 3m
        """
        so_phong = int(self.spin_so_phong.value() or 0)
        so_tang = int(i.get("tang", 0)) + int(i.get("ham", 0))
        floors = max(1, so_tang)
        hl_per_floor = float(self.spin_hl_dai.value()) \
            if hasattr(self, "spin_hl_dai") else 0.0
        hl_total = hl_per_floor * floors if hl_per_floor > 0 else 1.0

        defaults = [
            (self.tn_loi_ra_ngoai, 2),
            (self.tn_cau_thang, 1),
            (self.tn_loi_ra_phong, so_phong if so_phong > 0 else 1),
            (self.tn_chieu_nghi, so_tang if so_tang > 0 else 1),
            (self.tn_dai_hl, hl_total),
            (self.tn_rong_hl, 3.0),
        ]
        for w, default_v in defaults:
            if w.value() == 0:
                w.blockSignals(True)
                w.setValue(default_v)
                w.blockSignals(False)
        # LUÔN sync tn_dai_hl = HL_per_floor × floors (kể cả khi != 0)
        if hl_per_floor > 0:
            self.tn_dai_hl.blockSignals(True)
            self.tn_dai_hl.setValue(hl_total)
            self.tn_dai_hl.blockSignals(False)
        # Trigger _on_tn_changed 1 lần để cập nhật thoat_nan dict + lbl_tn_result
        self._on_tn_changed()

    # ---------------- RENDER TAB 1: THIẾT BỊ ----------------
    def _on_thiet_bi_clicked(self, row: int, col: int):
        """Click cột "Yêu cầu" (col 2) → toggle Muốn trang bị cho mục không bắt buộc."""
        if col != 2 or not self.last_result_raw:
            return
        items = self.last_result_raw["items"]
        if row < 0 or row >= len(items):
            return
        x = items[row]
        if x["req"] or x.get("mode") == "doc_lap":
            return  # mục bắt buộc — không toggle được
        nhom = x.get("nhom")
        if not nhom:
            return
        if nhom in self.optional_wants:
            self.optional_wants.discard(nhom)
        else:
            self.optional_wants.add(nhom)
        # Re-apply + re-render
        self._apply_optional_wants_to_last_result()
        self._render_thiet_bi()
        if hasattr(self, "lbl_cap_nuoc_result"):
            self._render_cap_nuoc()
        self._render_bao_gia()
        self._render_tu_van()
        # Force Qt repaint ngay lập tức (tránh chờ event loop)
        self.tb_thiet_bi.viewport().update()
        if hasattr(self, "tb_bg"):
            self.tb_bg.viewport().update()

    def _apply_optional_wants_to_last_result(self):
        """Copy raw → last_result và set req=True cho các nhóm user "muốn trang bị"."""
        if not self.last_result_raw:
            return
        import copy
        new_res = copy.deepcopy(self.last_result_raw)
        for x in new_res["items"]:
            if (not x["req"] and x.get("mode") != "doc_lap"
                    and x.get("nhom") in self.optional_wants):
                x["req"] = True
                x["dk"] = "[Muốn trang bị] " + x.get("dk", "")
        self.last_result = new_res

    def _render_thiet_bi(self):
        # Render từ bản RAW để cột Yêu cầu phản ánh đúng 'bắt buộc theo
        # quy định' vs 'muốn trang bị' thay vì gộp lại sau khi apply
        res = self.last_result_raw or self.last_result
        cn = res["cn"]
        i = res["i"]
        items = res["items"]

        self.lbl_summary.setText(
            f"<b>Công năng:</b> {cn['t']}  |  "
            f"<b>Diện tích:</b> {_fmt_money(i['dt'])} m²  |  "
            f"<b>Cao PCCC:</b> {i['cao']} m  |  "
            f"<b>Tầng nổi:</b> {i['tang']}  |  "
            f"<b>Tầng hầm:</b> {i['ham']}")

        self.tb_thiet_bi.setRowCount(len(items))
        for n, x in enumerate(items):
            self.tb_thiet_bi.setItem(n, 0, QTableWidgetItem(str(n + 1)))
            it_ht = QTableWidgetItem(x["ht"])
            f = it_ht.font(); f.setBold(True); it_ht.setFont(f)
            self.tb_thiet_bi.setItem(n, 1, it_ht)

            # Cột Yêu cầu: 4 trạng thái — Bắt buộc / Khuyến nghị / Muốn / Không
            from PyQt6.QtGui import QColor, QBrush
            want = x["nhom"] in self.optional_wants and not x["req"]
            if x.get("mode") == "doc_lap":
                yc = "BẮT BUỘC · tối thiểu: độc lập"
                bg = QColor("#a16207")
                fg = QColor("white")
            elif x["req"]:
                yc = "BẮT BUỘC"
                bg = QColor("#b91c1c")
                fg = QColor("white")
            elif x.get("mode") == "khuyen_nghi" and want:
                yc = "✓ Muốn trang bị (khuyến nghị · click để bỏ)"
                bg = QColor("#a7f3d0")
                fg = QColor("#065f46")
            elif x.get("mode") == "khuyen_nghi":
                yc = "⚠ KHUYẾN NGHỊ (click để chọn trang bị)"
                bg = QColor("#fde68a")    # vàng nhạt
                fg = QColor("#78350f")    # nâu đậm contrast
            elif want:
                yc = "✓ Muốn trang bị (click để bỏ)"
                bg = QColor("#a7f3d0")
                fg = QColor("#065f46")
            else:
                yc = "Không bắt buộc (click để chọn trang bị)"
                bg = QColor("#e5e7eb")
                fg = QColor("#374151")
            it_yc = QTableWidgetItem(yc)
            it_yc.setForeground(QBrush(fg))
            it_yc.setBackground(QBrush(bg))
            self.tb_thiet_bi.setItem(n, 2, it_yc)
            self.tb_thiet_bi.setItem(n, 3, QTableWidgetItem(x["dk"]))
            self.tb_thiet_bi.setItem(n, 4, QTableWidgetItem(x["can"]))
        self.tb_thiet_bi.resizeRowsToContents()

        notes = []
        if res["bcState"] == "doc_lap":
            notes.append(
                "ℹ️ <b>Về báo cháy:</b> công trình quy mô nhỏ — QCVN 10 cho phép dùng "
                "<b>thiết bị báo cháy độc lập</b> (gọn, chi phí thấp) thay cho hệ thống tự động. "
                "Khách hàng vẫn có thể chọn lắp hệ thống tự động nếu muốn mức bảo vệ cao hơn.")
        elif res["bcState"] == "khuyen_nghi":
            notes.append(
                "⚠️ <b>Khuyến nghị:</b> công trình DƯỚI NGƯỠNG bắt buộc báo cháy tự động "
                "nhưng thuộc diện 'cho phép trang bị thiết bị báo cháy độc lập' theo "
                "chú thích Bảng A.1 QCVN 10:2025. <b>Không bắt buộc</b> theo quy định, "
                "nhưng nên tư vấn KH lắp <b>thiết bị báo cháy độc lập</b> tăng an toàn — "
                "đặc biệt với công trình có trẻ em / người cao tuổi / người bệnh.")
        if res["bcState"] != "khong":
            notes.append(
                "ℹ️ <b>Truyền tin báo cháy</b> bắt buộc với mọi cơ sở thuộc diện quản lý PCCC "
                "(Phụ lục I NĐ 105) — kết nối đến CSDL PCCC. Hoàn thành chậm nhất <b>01/7/2027</b>.")
        notes.append(
            "⚠️ Đây là kết quả tra cứu sơ bộ theo QCVN 10:2025/BCA. Trường hợp đặc thù "
            "(tầng hầm, nhà dạng hở, bậc chịu lửa, hạng nguy hiểm cháy) cần kỹ sư thiết kế "
            "PCCC kiểm tra. Không thay thế hồ sơ thẩm duyệt của cơ quan có thẩm quyền.")
        self.lbl_note.setText("<br><br>".join(notes))

    # ---------------- TAB 2: GIAN PHÒNG ----------------
    def _on_cov_changed(self):
        self.dt_khoi = float(self.sp_dt_khoi.value() or 60)
        self.dt_nhiet = float(self.sp_dt_nhiet.value() or 20)
        self._render_rooms()

    def _default_room_func_current(self) -> str:
        cn = self._current_cong_nang()
        return R.default_room_func(cn["k"]) if cn else "van_phong"

    def _gen_rooms_from_count(self, silent: bool = False):
        n = int(self.spin_so_phong.value())
        dt = float(self.spin_dt.value())
        if n <= 0:
            if not silent:
                QMessageBox.information(self, "Thiếu dữ liệu",
                                        "Hãy nhập 'Số phòng' > 0 ở cột trái.")
            return
        # DT phòng = (DT_tổng − DT hành lang toàn nhà) / số phòng
        # DT hành lang = HL_dài/tầng × HL_rộng × số_tầng
        floors = max(1, int(self.spin_tang.value()) + int(self.spin_ham.value()))
        hl_dai_per_floor = float(self.spin_hl_dai.value()) \
            if hasattr(self, "spin_hl_dai") else 0.0
        hl_rong = float(self.tn_rong_hl.value()) \
            if hasattr(self, "tn_rong_hl") else 3.0
        dt_hl_total = hl_dai_per_floor * hl_rong * floors
        dt_phong_total = max(0.0, dt - dt_hl_total)
        fk = self._default_room_func_current()
        area = round(dt_phong_total / n, 1) if n else 0
        loai = R.def_loai_dau_bao(fk)
        self.rooms = [
            {"ten": f"P{j+1}", "func": fk, "dt": area, "loai": loai}
            for j in range(n)
        ]
        self._render_rooms()

    def _add_one_room(self):
        fk = "phong_ngu"
        self.rooms.append({"ten": f"P{len(self.rooms)+1}",
                           "func": fk, "dt": 20.0,
                           "loai": R.def_loai_dau_bao(fk)})
        self._render_rooms()

    def _bulk_add_rooms(self):
        n = int(self.bk_n.value())
        dt = float(self.bk_dt.value())
        fk = self.bk_func.currentData()
        pre = self.bk_pre.text().strip() or "P"
        base = len(self.rooms)
        loai = R.def_loai_dau_bao(fk)
        for j in range(1, n + 1):
            self.rooms.append({"ten": f"{pre}{base+j}",
                               "func": fk, "dt": dt, "loai": loai})
        self._render_rooms()

    def _render_rooms(self):
        rs = self.rooms
        self.tb_rooms.blockSignals(True)
        self.tb_rooms.setRowCount(len(rs))
        for n, r in enumerate(rs):
            self.tb_rooms.setItem(n, 0, QTableWidgetItem(str(n + 1)))
            # Tên phòng
            ed_ten = QLineEdit(r.get("ten", ""))
            ed_ten.textChanged.connect(
                lambda v, idx=n: self._upd_room(idx, "ten", v))
            self.tb_rooms.setCellWidget(n, 1, ed_ten)
            # Công năng — dropdown phải đủ rộng cho text dài, không elide
            cb = QComboBox()
            for f in R.ROOM_FUNCS:
                cb.addItem(f["t"], f["k"])
            idx = next((i for i, f in enumerate(R.ROOM_FUNCS) if f["k"] == r["func"]), 0)
            cb.setCurrentIndex(idx)
            # Cho phép dropdown rộng hơn ô cell, không cắt text
            fm_cb = QFontMetrics(cb.font())
            max_w = max(fm_cb.horizontalAdvance(cb.itemText(k))
                        for k in range(cb.count()))
            cb.view().setMinimumWidth(max_w + 50)
            cb.view().setTextElideMode(Qt.TextElideMode.ElideNone)
            cb.setToolTip(cb.currentText())
            cb.currentIndexChanged.connect(
                lambda _v, idx=n, w=cb: (self._upd_room(idx, "func", w.currentData()),
                                         w.setToolTip(w.currentText())))
            self.tb_rooms.setCellWidget(n, 2, cb)
            # Diện tích
            sp = _make_dspin(r.get("dt", 0), 9999, 1)
            sp.valueChanged.connect(
                lambda v, idx=n: self._upd_room(idx, "dt", v))
            self.tb_rooms.setCellWidget(n, 3, sp)
            # Loại đầu báo
            cb2 = QComboBox()
            cb2.addItem("Khói", "khoi")
            cb2.addItem("Nhiệt", "nhiet")
            cb2.setCurrentIndex(0 if r["loai"] == "khoi" else 1)
            cb2.currentIndexChanged.connect(
                lambda _v, idx=n, w=cb2: self._upd_room(idx, "loai", w.currentData()))
            self.tb_rooms.setCellWidget(n, 4, cb2)
            # SL đầu báo
            sl = R.sl_phong(r, self.dt_khoi, self.dt_nhiet)
            it_sl = QTableWidgetItem(str(sl))
            it_sl.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            f2 = it_sl.font()
            if f2.pointSize() <= 0:
                f2.setPointSize(10)
            f2.setBold(True)
            it_sl.setFont(f2)
            self.tb_rooms.setItem(n, 5, it_sl)
            # Nút xóa
            but = QPushButton("✕")
            but.setMaximumWidth(40)
            but.clicked.connect(lambda _c=False, idx=n: self._del_room(idx))
            self.tb_rooms.setCellWidget(n, 6, but)
        self.tb_rooms.blockSignals(False)

        tot = R.room_totals(rs, self.dt_khoi, self.dt_nhiet)
        self.lbl_phong_tong.setText(
            f"Tổng đầu báo <b>khói</b>: <b>{tot['khoi']}</b>  ·  "
            f"Tổng đầu báo <b>nhiệt</b>: <b>{tot['nhiet']}</b>  ·  "
            f"Số phòng: <b>{len(rs)}</b>")
        # Khi có dữ liệu phòng, render lại báo giá để cập nhật SL đầu báo
        if self.last_result:
            self._render_bao_gia()

    def _upd_room(self, idx: int, field: str, value):
        """Cập nhật field của 1 phòng. Khi đổi 'func' → tự đổi 'loai' đầu báo
        theo công năng phòng (TCVN 7568-14: khu hơi nước/bụi/bếp/gara → nhiệt)."""
        if not (0 <= idx < len(self.rooms)):
            return
        if field == "dt":
            value = float(value or 0)
        self.rooms[idx][field] = value

        if field == "func":
            # Tự đổi loại đầu báo theo công năng — cập nhật INLINE để tránh
            # recreate widget trong khi signal handler đang chạy
            new_loai = R.def_loai_dau_bao(value)
            self.rooms[idx]["loai"] = new_loai
            cb_loai = self.tb_rooms.cellWidget(idx, 4)
            if cb_loai is not None:
                cb_loai.blockSignals(True)
                cb_loai.setCurrentIndex(0 if new_loai == "khoi" else 1)
                cb_loai.blockSignals(False)

        # Cập nhật cell SL đầu báo của dòng này
        sl = R.sl_phong(self.rooms[idx], self.dt_khoi, self.dt_nhiet)
        sl_item = self.tb_rooms.item(idx, 5)
        if sl_item is not None:
            self.tb_rooms.blockSignals(True)
            sl_item.setText(str(sl))
            self.tb_rooms.blockSignals(False)

        # Cập nhật tổng dưới bảng + báo giá (nếu có)
        tot = R.room_totals(self.rooms, self.dt_khoi, self.dt_nhiet)
        self.lbl_phong_tong.setText(
            f"Tổng đầu báo <b>khói</b>: <b>{tot['khoi']}</b>  ·  "
            f"Tổng đầu báo <b>nhiệt</b>: <b>{tot['nhiet']}</b>  ·  "
            f"Số phòng: <b>{len(self.rooms)}</b>")
        if self.last_result:
            self._render_bao_gia()

    def _del_room(self, idx: int):
        if 0 <= idx < len(self.rooms):
            del self.rooms[idx]
            self._render_rooms()

    # ---------------- TAB 3: THOÁT NẠN ----------------
    def _on_tn_changed(self):
        self.thoat_nan = {
            "kc_sc": float(self.tn_kc_sc.value()),
            "kc_exit": float(self.tn_kc_exit.value()),
            "so_loi_ra_ngoai": int(self.tn_loi_ra_ngoai.value()),
            "so_cau_thang": int(self.tn_cau_thang.value()),
            "so_loi_ra_phong": int(self.tn_loi_ra_phong.value()),
            "dai_hanh_lang": float(self.tn_dai_hl.value()),
            "so_chieu_nghi": int(self.tn_chieu_nghi.value()),
        }
        n_exit, n_sc = self._tinh_den()
        floors = max(1, int(self.spin_tang.value()) + int(self.spin_ham.value()))
        self.lbl_tn_result.setText(
            f"<b>Số đèn EXIT:</b> {n_exit} bộ  "
            f"(= lối ra ngoài + cầu thang + cửa phòng dẫn ra hành lang"
            f" + đèn dọc hành lang theo khoảng cách {self.thoat_nan['kc_exit']} m)<br>"
            f"<b>Số đèn chiếu sáng sự cố:</b> {n_sc} bộ  "
            f"(= chiếu nghỉ cầu thang + đèn dọc hành lang theo khoảng cách {self.thoat_nan['kc_sc']} m)<br>"
            f"<b>Số tầng:</b> {floors}")
        if self.last_result:
            self._render_bao_gia()

    def _tinh_den(self):
        t = self.thoat_nan
        floors = max(1, int(self.spin_tang.value()) + int(self.spin_ham.value()))
        has_data = (t["so_loi_ra_ngoai"] or t["so_cau_thang"]
                    or t["dai_hanh_lang"] or t["so_loi_ra_phong"])
        if not has_data:
            return (floors, floors)  # mặc định 1 đèn EXIT + 1 đèn SC mỗi tầng

        # EXIT: lối ra ngoài + cầu thang + cửa phòng ra hành lang + đèn dọc HL
        from math import ceil
        n_exit = (t["so_loi_ra_ngoai"] + t["so_cau_thang"] + t["so_loi_ra_phong"]
                  + (ceil(t["dai_hanh_lang"] / t["kc_exit"]) if t["kc_exit"] > 0 else 0))
        # SC: chiếu nghỉ + đèn dọc HL
        n_sc = (t["so_chieu_nghi"]
                + (ceil(t["dai_hanh_lang"] / t["kc_sc"]) if t["kc_sc"] > 0 else 0))
        return (max(n_exit, floors), max(n_sc, floors))

    # ---------------- TAB 4: BÁO GIÁ ----------------
    def _render_bao_gia(self):
        res = self.last_result
        if not res:
            return
        items = res["items"]
        i = res["i"]
        tot_phong = R.room_totals(self.rooms, self.dt_khoi, self.dt_nhiet)
        slots = R.build_slots(items, i, tot_phong)

        # Override SL đèn theo tab thoát nạn
        n_exit, n_sc = self._tinh_den()
        for s in slots:
            if s["loai"] == "den_exit":
                s["sl"] = n_exit
            elif s["loai"] == "den_sc":
                s["sl"] = n_sc

        # Map slot → SP cụ thể từ catalog
        # Với báo cháy/truyền tin: filter theo bg_group (mặc định "khong_day")
        rows = []
        missing = []  # ghi nhận slot không tìm được SP để cảnh báo
        for s in slots:
            group = self.bg_group if self._need_group(s["nhom"]) else None

            # Slot CÓ GIÁ MẶC ĐỊNH (fixed=True) — KHÔNG tra catalog
            if s.get("fixed"):
                rows.append({
                    "label": s["label"], "nhom": s["nhom"], "loai": s["loai"],
                    "ci": -1, "sl": s["sl"],
                    "ten": s.get("fixed_ten", s["label"]),
                    "model": "(Ước tính)",
                    "hieu": "",
                    "dv": s.get("fixed_dv", "Bộ"),
                    "gia": int(s.get("fixed_gia", 0)),
                    "vat": 8,
                    "nhan_cong_unit": 0,
                    "parent_ht": s.get("parent_ht", ""),
                    "group": group,
                })
                continue

            # Đặc biệt: truyền tin pick model theo group (Fcom1 / Fcom2)
            if s["nhom"] == "truyen_tin":
                tt_model = R.truyen_tin_model_of(self.bg_group)
                idx = self._find_by_model(tt_model)
                if idx < 0:
                    idx = self._find_product("truyen_tin", group=group)
            # Đặc biệt: tủ trung tâm pick model mặc định theo group
            elif s["nhom"] == "bao_chay" and s["loai"] == "trung_tam":
                tt_model = R.default_trung_tam_model(self.bg_group)
                idx = self._find_by_model(tt_model) if tt_model else -1
                if idx < 0:
                    idx = self._find_product(s["nhom"], s["loai"], group=group)
            else:
                # Sprinkler ưu tiên SP K=5.6, 68°C
                prefer = None
                if s["nhom"] == "chua_chay" and s["loai"] in (
                        "sprinkler_up", "sprinkler_down"):
                    prefer = ["k=5.6", "k 5.6", "k5.6", "k 5,6", "k=5,6",
                              "5.6", "5,6", "68"]
                idx = self._find_product(s["nhom"], s["loai"],
                                         group=group, prefer=prefer)

            if idx < 0:
                # Không có SP phù hợp — vẫn show dòng để sales biết, ghi missing
                rows.append({"label": s["label"], "nhom": s["nhom"], "loai": s["loai"],
                             "ci": -1, "sl": s["sl"], "ten": s["label"], "model": "(THIẾU SP)",
                             "hieu": "", "dv": "", "gia": 0, "vat": 8,
                             "nhan_cong_unit": 0,
                             "parent_ht": s.get("parent_ht", ""),
                             "group": group})
                missing.append(f"{s['label']} (loai={s['loai'] or '-'})")
            else:
                c = self.catalog[idx]
                rows.append({"label": s["label"], "nhom": s["nhom"], "loai": s["loai"],
                             "ci": idx, "sl": s["sl"], "ten": c["ten"], "model": c["model"],
                             "hieu": c["hieu"], "dv": c["dv"], "gia": c["gia"], "vat": c["vat"],
                             "nhan_cong_unit": c.get("nhan_cong_unit", 0),
                             "parent_ht": s.get("parent_ht", ""),
                             "group": group})

        # Hệ báo cháy CÓ DÂY: mỗi tổ hợp chuông đèn cần thêm 1 còi đèn (FSBL-001)
        # + 1 nút ấn (FSM-001) — theo file "Lựa chọn thiết bị báo cháy.xlsx"
        if self.bg_group == "co_day":
            cd_idx = next((k for k, r in enumerate(rows)
                          if r["nhom"] == "bao_chay" and r["loai"] == "chuong_den"), -1)
            if cd_idx >= 0:
                qty = rows[cd_idx]["sl"]
                # Đổi label cho rõ hơn
                rows[cd_idx]["label"] = "Hộp tổ hợp đựng chuông đèn"
                # Thêm 2 dòng phía sau
                extra_models = [
                    ("Còi đèn báo cháy kết hợp", "FSBL-001"),
                    ("Nút ấn báo cháy", "FSM-001"),
                ]
                insert_at = cd_idx + 1
                for label, model in extra_models:
                    ci = self._find_by_model(model)
                    parent_ht = rows[cd_idx].get("parent_ht", "")
                    if ci >= 0:
                        c = self.catalog[ci]
                        rows.insert(insert_at, {
                            "label": label, "nhom": "bao_chay", "loai": None,
                            "ci": ci, "sl": qty, "ten": c["ten"],
                            "model": c["model"], "hieu": c["hieu"], "dv": c["dv"],
                            "gia": c["gia"], "vat": c["vat"],
                            "nhan_cong_unit": c.get("nhan_cong_unit", 0),
                            "parent_ht": parent_ht, "group": "co_day"})
                    else:
                        rows.insert(insert_at, {
                            "label": label, "nhom": "bao_chay", "loai": None,
                            "ci": -1, "sl": qty, "ten": label, "model": model,
                            "hieu": "", "dv": "", "gia": 0, "vat": 8,
                            "nhan_cong_unit": 0,
                            "parent_ht": parent_ht, "group": "co_day"})
                        missing.append(f"{label} ({model})")
                    insert_at += 1

        self.bg_rows = rows

        # Cảnh báo các SP thiếu trong bảng giá (gom với cảnh báo thiếu nhân công)
        warnings_html = []
        if missing:
            tên_nhóm = R.BAO_CHAY_GROUP_LABELS.get(self.bg_group, self.bg_group)
            warnings_html.append(
                f"<b>⚠ Thiếu sản phẩm</b> cho nhóm <b>{tên_nhóm}</b>:<br>• "
                + "<br>• ".join(missing))
        # Cảnh báo SP có sl>0 nhưng nhan_cong_unit=0
        missing_nc = getattr(self, "_missing_nc_pending", [])
        if missing_nc:
            uniq = sorted(set(missing_nc))
            warnings_html.append(
                "<b>⚠ Thiếu giá nhân công</b> cho các SP sau "
                "(cột <code>nhan_cong</code> trong <code>gia_tong_hop</code> = 0):<br>• "
                + "<br>• ".join(uniq))
        if warnings_html:
            QMessageBox.warning(
                self, "Cần bổ sung dữ liệu bảng giá Fsales",
                "<br><br>".join(warnings_html) +
                "<br><br><i>Vui lòng bổ sung vào DB Fsales (bảng <code>gia_tong_hop</code>) "
                "rồi mở lại cửa sổ Tư vấn PCCC. Trong khi chờ, anh có thể bấm "
                "'Đổi model' để chọn SP thay thế thủ công.</i>")
        self._missing_nc_pending = []  # reset sau khi đã cảnh báo

        # Chèn header rows trước mỗi nhóm parent_ht
        # rows từ slots đã đến từ build_slots theo thứ tự items → parent_ht giữ thứ tự
        grouped_rows = []
        seen_ht = None
        for r in rows:
            ph = r.get("parent_ht") or "(Khác)"
            if ph != seen_ht:
                grouped_rows.append({"is_header": True, "ten": ph})
                seen_ht = ph
            grouped_rows.append(r)
        self.bg_rows = grouped_rows

        # Render bảng — plain text cells, style giống Fsales quotation
        self.tb_bg.blockSignals(True)
        self.tb_bg.clearSpans()
        self.tb_bg.setRowCount(len(grouped_rows))
        for n, r in enumerate(grouped_rows):
            self._render_bg_row(n, r)
        self.tb_bg.blockSignals(False)
        self._renum_stt()

        self._recalc_bg()
        self.lbl_bg_info.setText(
            f"💡 Đã có <b>{len(rows)}</b> dòng. Double-click ô SL/Đơn giá để sửa. "
            f"Double-click cột Model (hoặc nút <b>Đổi model</b>) để đổi SP. "
            f"Bảng giá: {len(self.catalog)} SP từ Fsales.")

    def _render_bg_row(self, n: int, r: dict):
        """Render 1 dòng bảng báo giá. r có thể là header (is_header=True)
        hoặc dòng SP (10 cột)."""
        from PyQt6.QtGui import QColor, QBrush
        tb = self.tb_bg

        def _cell(text, *, edit=False, align_right=False, bold=False, bg=None, fg=None):
            it = QTableWidgetItem(text)
            flags = it.flags()
            if not edit:
                flags &= ~Qt.ItemFlag.ItemIsEditable
            it.setFlags(flags)
            if align_right:
                it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                it.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            if bold:
                f = it.font()
                if f.pointSize() <= 0:
                    f.setPointSize(10)
                f.setBold(True)
                it.setFont(f)
            if bg is not None:
                it.setBackground(QBrush(QColor(bg)))
            if fg is not None:
                it.setForeground(QBrush(QColor(fg)))
            return it

        # --- Dòng tiêu đề (section header) — gom nhóm theo hệ thống ---
        if r.get("is_header"):
            # Trộn các ô lại thành 1 ô duy nhất (span 10 cột)
            tb.setSpan(n, 0, 1, 10)
            tb.setItem(n, 0, _cell(
                "▾ " + r.get("ten", ""),
                bold=True, bg="#0f766e", fg="#ffffff"))
            tb.setRowHeight(n, 30)
            return

        # --- Dòng SP bình thường ---
        if tb.columnSpan(n, 0) > 1:
            tb.setSpan(n, 0, 1, 1)  # reset span nếu có

        # STT — sẽ được set lại bằng _renum_stt sau
        tb.setItem(n, 0, _cell("", align_right=True))
        # Mô tả: tên SP
        it_ten = _cell(r["ten"] or r["label"])
        it_ten.setToolTip(f"Vai trò: {r['label']}")
        tb.setItem(n, 1, it_ten)
        tb.setItem(n, 2, _cell(r["model"] or ""))
        tb.setItem(n, 3, _cell(r["hieu"] or ""))
        tb.setItem(n, 4, _cell(r["dv"] or "", align_right=True))
        # SL, Đơn giá, Nhân công — editable
        tb.setItem(n, 5, _cell(_fmt_money(r["sl"]), edit=True, align_right=True))
        tb.setItem(n, 6, _cell(_fmt_money(r["gia"]), edit=True, align_right=True))
        tb.setItem(n, 7, _cell(_fmt_money(r.get("nhan_cong_unit", 0)),
                               edit=True, align_right=True))
        # Thuế (tiền) = (sl × gia × vat%) + (sl × nhan_cong × 10%)
        sl = float(r["sl"])
        gia = float(r["gia"])
        nc_u = float(r.get("nhan_cong_unit", 0))
        tien_vt = sl * gia
        tien_nc = sl * nc_u
        thue = tien_vt * (float(r.get("vat", 8)) / 100.0) + tien_nc * 0.10
        tb.setItem(n, 8, _cell(_fmt_money(thue), align_right=True))
        # Thành tiền (bao gồm thuế + nhân công)
        tt = tien_vt + tien_nc + thue
        tb.setItem(n, 9, _cell(_fmt_money(tt), align_right=True, bold=True))

    def _renum_stt(self):
        """Đánh lại số thứ tự cho các dòng SP (bỏ qua header)."""
        self.tb_bg.blockSignals(True)
        stt = 0
        for n, r in enumerate(self.bg_rows):
            if r.get("is_header"):
                continue
            stt += 1
            it = self.tb_bg.item(n, 0)
            if it:
                it.setText(str(stt))
        self.tb_bg.blockSignals(False)

    def _upd_slot_product(self, idx: int, ci: int):
        """Đổi model cho 1 dòng — gọi từ dialog đổi model."""
        if not (0 <= idx < len(self.bg_rows)) or ci is None or ci < 0:
            return
        c = self.catalog[ci]
        r = self.bg_rows[idx]
        r["ci"] = ci
        r["ten"] = c["ten"]
        r["model"] = c["model"]
        r["hieu"] = c["hieu"]
        r["dv"] = c["dv"]
        r["gia"] = c["gia"]
        r["vat"] = c["vat"]
        # Re-render dòng đó
        self.tb_bg.blockSignals(True)
        self._render_bg_row(idx, r)
        self.tb_bg.blockSignals(False)
        self._recalc_bg()

    @staticmethod
    def _parse_money(text: str) -> float:
        """'1.234.567' -> 1234567.0 ; '10' -> 10.0"""
        if text is None:
            return 0.0
        s = str(text).strip().replace(".", "").replace(",", "").replace(" ", "")
        try:
            return float(s)
        except ValueError:
            return 0.0

    def _on_bg_item_changed(self, item: QTableWidgetItem):
        """User vừa sửa SL (col 5), Đơn giá (col 6), hoặc Nhân công (col 7).
        Reformat ô, tính lại thuế + thành tiền, gọi recalc tổng."""
        if item is None:
            return
        col = item.column()
        row = item.row()
        if not (0 <= row < len(self.bg_rows)):
            return
        r = self.bg_rows[row]
        if r.get("is_header"):
            return
        if col not in (5, 6, 7):
            return
        val = self._parse_money(item.text())
        if col == 5:
            r["sl"] = int(val)
        elif col == 6:
            r["gia"] = val
        elif col == 7:
            r["nhan_cong_unit"] = val

        # Reformat ô + tính lại thuế (col 8) + thành tiền (col 9)
        self.tb_bg.blockSignals(True)
        item.setText(_fmt_money(val))
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        sl = float(r["sl"])
        gia = float(r["gia"])
        nc_u = float(r.get("nhan_cong_unit", 0))
        tien_vt = sl * gia
        tien_nc = sl * nc_u
        thue = tien_vt * (float(r.get("vat", 8)) / 100.0) + tien_nc * 0.10
        tt = tien_vt + tien_nc + thue
        thue_it = self.tb_bg.item(row, 8)
        tt_it = self.tb_bg.item(row, 9)
        if thue_it:
            thue_it.setText(_fmt_money(thue))
        if tt_it:
            tt_it.setText(_fmt_money(tt))
        self.tb_bg.blockSignals(False)
        self._recalc_bg()

    def _on_bg_double_click(self, row: int, col: int):
        """Double-click cột Model (2) hoặc Mô tả (1) → mở dialog đổi model."""
        if 0 <= row < len(self.bg_rows) and self.bg_rows[row].get("is_header"):
            return
        if col in (1, 2, 3):
            self._doi_model_dialog(row)

    def _doi_model_dialog(self, row: int = None):
        """Dialog chọn model thay thế từ catalog (cùng nhóm PCCC)."""
        if row is None:
            row = self.tb_bg.currentRow()
        if not (0 <= row < len(self.bg_rows)):
            QMessageBox.information(self, "Chọn dòng",
                                    "Hãy chọn 1 dòng trước rồi bấm 'Đổi model'.")
            return
        r = self.bg_rows[row]
        # Cho phép chọn BẤT KỲ SP cùng nhom (không khống chế bg_group)
        # — sau khi user pick SP khác nhóm, app sẽ auto-switch toàn hệ báo cháy
        candidates = [(ci, c) for ci, c in enumerate(self.catalog)
                      if c["nhom"] == r["nhom"]]
        if not candidates:
            QMessageBox.information(self, "Không có model",
                                    f"Bảng giá Fsales không có SP nhóm '{r['nhom']}'.")
            return

        from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QListWidget, QListWidgetItem
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Đổi model — {r['label']}")
        dlg.resize(720, 460)
        lay = QVBoxLayout(dlg)
        lay.addWidget(QLabel(f"<b>Vai trò:</b> {r['label']}  ·  "
                             f"<b>Hiện tại:</b> {r['ten']} ({r['model'] or '—'})"))
        # Ô tìm kiếm
        ed = QLineEdit()
        ed.setPlaceholderText("🔎 Gõ để lọc theo tên / model / nhãn hiệu…")
        lay.addWidget(ed)
        lst = QListWidget()
        lay.addWidget(lst, 1)

        def _fill(filter_text=""):
            lst.clear()
            ft = filter_text.lower().strip()
            for ci, c in candidates:
                txt = f"{c['ten']}  |  {c['model']}  |  {c['hieu']}  |  {_fmt_money(c['gia'])} đ"
                if ft and ft not in txt.lower():
                    continue
                it = QListWidgetItem(txt)
                it.setData(Qt.ItemDataRole.UserRole, ci)
                if ci == r["ci"]:
                    f = it.font(); f.setBold(True); it.setFont(f)
                lst.addItem(it)

        _fill()
        ed.textChanged.connect(_fill)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                              | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(dlg.accept)
        bb.rejected.connect(dlg.reject)
        lay.addWidget(bb)
        lst.itemDoubleClicked.connect(lambda _i: dlg.accept())

        if dlg.exec() == QDialog.DialogCode.Accepted:
            it = lst.currentItem()
            if it is not None:
                ci = int(it.data(Qt.ItemDataRole.UserRole))
                c = self.catalog[ci]

                # Nếu SP mới thuộc nhóm báo cháy KHÁC nhóm hiện tại → auto-switch
                new_groups = c.get("bg_groups") or set()
                if (self._need_group(r["nhom"]) and new_groups
                        and self.bg_group not in new_groups):
                    new_group = next(iter(new_groups))
                    label_new = R.BAO_CHAY_GROUP_LABELS.get(new_group, new_group)
                    ans = QMessageBox.question(
                        self, "Đổi nhóm hệ báo cháy",
                        f"Model <b>{c['model']}</b> thuộc nhóm <b>{label_new}</b>, "
                        f"khác nhóm hiện tại. Sẽ thay thế TẤT CẢ thiết bị báo cháy "
                        f"+ truyền tin sang nhóm <b>{label_new}</b>. Tiếp tục?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes)
                    if ans != QMessageBox.StandardButton.Yes:
                        return
                    self.bg_group = new_group
                    self._sync_bg_group_combo()
                    if self.last_result:
                        self._render_bao_gia()
                    # Sau re-render bg_rows đã thay đổi, không cần _upd_slot_product
                    return

                self._upd_slot_product(row, ci)


    def _them_dong_bg(self):
        """Thêm 1 dòng trống — sales tự pick model. Đặt vào nhóm 'Khác/Tùy chọn'."""
        if not self.catalog:
            QMessageBox.information(self, "Chưa có bảng giá",
                                    "Bảng giá Fsales chưa nạp được — không thêm dòng được.")
            return
        c = self.catalog[0]
        # Kiểm tra đã có header "Khác / Tùy chọn thêm" chưa
        custom_ht = "Khác / Tùy chọn thêm"
        has_header = any(r.get("is_header") and r.get("ten") == custom_ht
                         for r in self.bg_rows)
        if not has_header:
            self.bg_rows.append({"is_header": True, "ten": custom_ht})
        r = {"label": "(Tùy chọn thêm)", "nhom": c["nhom"], "loai": c["loai"],
             "ci": 0, "sl": 1, "ten": c["ten"], "model": c["model"],
             "hieu": c["hieu"], "dv": c["dv"], "gia": c["gia"], "vat": c["vat"],
             "nhan_cong_unit": c.get("nhan_cong_unit", 0),
             "parent_ht": custom_ht}
        self.bg_rows.append(r)
        # Re-render toàn bảng để giữ thứ tự header/rows nhất quán
        self.tb_bg.blockSignals(True)
        self.tb_bg.clearSpans()
        self.tb_bg.setRowCount(len(self.bg_rows))
        for n, rr in enumerate(self.bg_rows):
            self._render_bg_row(n, rr)
        self.tb_bg.blockSignals(False)
        self._renum_stt()
        self._recalc_bg()

    def _xoa_dong_bg(self):
        """Xóa dòng đang chọn (không cho xóa header)."""
        row = self.tb_bg.currentRow()
        if row < 0 and self.tb_bg.rowCount() > 0:
            row = self.tb_bg.rowCount() - 1
        if not (0 <= row < len(self.bg_rows)):
            return
        if self.bg_rows[row].get("is_header"):
            QMessageBox.information(self, "Không thể xóa",
                                    "Không thể xóa dòng tiêu đề nhóm — chỉ xóa được dòng SP.")
            return
        del self.bg_rows[row]
        self.tb_bg.removeRow(row)
        self._renum_stt()
        self._recalc_bg()

    def _recalc_bg(self):
        """Tính lại tổng: bỏ qua header rows.
        Mỗi row: tiền_vt + tiền_nc + thuế. Tổng = SUM(tt) = cộng vt + cộng nc + tổng thuế."""
        total_vt = 0.0   # tổng tiền vật tư
        total_nc = 0.0   # tổng tiền nhân công
        total_thue = 0.0
        missing_nc = []
        for r in self.bg_rows:
            if r.get("is_header"):
                continue
            sl = float(r.get("sl") or 0)
            gia = float(r.get("gia") or 0)
            nc_u = float(r.get("nhan_cong_unit") or 0)
            vat_rate = float(r.get("vat", 8) or 8) / 100.0
            tien_vt = sl * gia
            tien_nc = sl * nc_u
            thue = tien_vt * vat_rate + tien_nc * 0.10
            total_vt += tien_vt
            total_nc += tien_nc
            total_thue += thue
            if sl > 0 and nc_u == 0 and r.get("ci", -1) >= 0:
                missing_nc.append(r.get("ten") or r.get("label") or "?")

        tong = total_vt + total_nc + total_thue
        self.lbl_tong.setText(
            f"Tiền vật tư: <b>{_fmt_money(total_vt)} đ</b>  ·  "
            f"Tiền nhân công: <b>{_fmt_money(total_nc)} đ</b>  ·  "
            f"Thuế: <b>{_fmt_money(total_thue)} đ</b>  ·  "
            f"<span style='color:#fbbf24'>TỔNG CỘNG: {_fmt_money(tong)} đ</span>")

        self._missing_nc_pending = missing_nc

    # ---------------- TAB 5: TƯ VẤN ----------------
    def _render_tu_van(self):
        res = self.last_result
        cn = res["cn"]
        i = res["i"]
        req = [x for x in res["items"] if x["req"]]
        kh = self.kh_ten.text().strip() or "Quý khách"
        ham_str = f" và {i['ham']} tầng hầm" if i["ham"] else ""

        lines = [
            "<h3>Mở đầu</h3>",
            f"<p>Kính gửi {kh}, căn cứ thông tin công trình (<b>{cn['t']}</b>, "
            f"tổng diện tích sàn {_fmt_money(i['dt'])} m², {i['tang']} tầng nổi{ham_str}, "
            f"chiều cao PCCC {i['cao']} m), đối chiếu QCVN 10:2025/BCA và Nghị định "
            f"105/2025/NĐ-CP, công trình thuộc diện phải trang bị các hệ thống PCCC sau.</p>",
        ]
        for x in req:
            lines.append(
                f"<h4>{x['ht']}</h4>"
                f"<p>Theo {x.get('can', x.get('dk', ''))}, công trình cần "
                f"<b>trang bị {x['ht'].lower()}</b> (điều kiện: {x['dk']}). "
                f"Đây là yêu cầu bắt buộc.</p>"
            )
        lines.append(
            f"<h3>Kết luận</h3>"
            f"<p>CÔNG TY CP DỊCH VỤ KỸ THUẬT PCCC VIỆT sẵn sàng khảo sát thực tế, "
            f"thiết kế và cung cấp trọn gói các hạng mục trên kèm hồ sơ nghiệm thu. "
            f"Báo giá chi tiết đính kèm. Mọi thắc mắc xin liên hệ "
            f"<b>{self.user} — {self.user_phone}</b>.</p>"
            f"<p style='color:#888; font-size:11px;'><i>Tài liệu hỗ trợ tư vấn, không "
            f"thay thế hồ sơ thiết kế & thẩm duyệt PCCC của cơ quan có thẩm quyền.</i></p>"
        )
        self.txt_tu_van.setHtml("".join(lines))

    def _xuat_excel(self):
        if not self.bg_rows:
            QMessageBox.information(self, "Chưa có dữ liệu",
                                    "Bấm Phân tích trước để sinh báo giá.")
            return
        ten_kh = self.kh_ten.text().strip() or "Khach hang"
        vv = self.kh_vv.text().strip() or "He thong PCCC"
        default_name = goi_y_ten_file(ten_kh, vv)
        path, _ = QFileDialog.getSaveFileName(
            self, "Lưu báo giá Excel", default_name, "Excel Files (*.xlsx)")
        if not path:
            return
        ttkh = {
            "ten": self.kh_ten.text().strip(),
            "dia_chi": self.kh_dc.text().strip(),
            "sdt": self.kh_dt.text().strip(),
            "vv": self.kh_vv.text().strip(),
        }
        try:
            out = xuat_bao_gia_pccc(
                bg_rows=self.bg_rows, ttkh=ttkh,
                nguoi_lap=self.user, sdt_nguoi_lap=self.user_phone,
                file_out=path)
            QMessageBox.information(self, "Thành công",
                                    f"Đã lưu báo giá:\n{out}")
        except Exception as e:
            QMessageBox.critical(self, "Lỗi xuất Excel", str(e))

    def _build_tab_ho_so_phap_ly(self):
        tab = QWidget()
        outer = QVBoxLayout(tab)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        outer.addWidget(scroll)
        inner = QWidget()
        scroll.setWidget(inner)
        v = QVBoxLayout(inner)
        v.setContentsMargins(10, 10, 10, 10)

        gb1 = QGroupBox("Phân loại theo NĐ 105/2025/NĐ-CP")
        l1 = QVBoxLayout(gb1)
        self.lbl_phan_loai_nd105 = QLabel("Bấm 'Phân tích' để xem phân loại.")
        self.lbl_phan_loai_nd105.setWordWrap(True)
        self.lbl_phan_loai_nd105.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_phan_loai_nd105.setOpenExternalLinks(True)
        l1.addWidget(self.lbl_phan_loai_nd105)
        v.addWidget(gb1)

        gb2 = QGroupBox("Danh sách hồ sơ PCCC (14 mục theo Điều 4 NĐ 105)")
        l2 = QVBoxLayout(gb2)
        self.lbl_ds_ho_so = QLabel("")
        self.lbl_ds_ho_so.setWordWrap(True)
        self.lbl_ds_ho_so.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_ds_ho_so.setOpenExternalLinks(True)
        l2.addWidget(self.lbl_ds_ho_so)
        v.addWidget(gb2)

        gb3 = QGroupBox("Lưu ý quan trọng")
        l3 = QVBoxLayout(gb3)
        lbl3 = QLabel(
            "<ul>"
            "<li>Hồ sơ phải lập khi đưa công trình vào hoạt động và lưu giữ suốt vòng đời.</li>"
            "<li>Báo cáo định kỳ 2 lần/năm (trước 15/6 và 15/12).</li>"
            "<li>Sổ theo dõi lưu tối thiểu 5 năm.</li>"
            "<li>Cơ quan kiểm tra định kỳ: Công an PCCC cấp huyện/tỉnh tuỳ theo phân loại.</li>"
            "<li>Cơ sở thuộc Phụ lục II Nhóm 1: bắt buộc mua bảo hiểm cháy nổ.</li>"
            "</ul>")
        lbl3.setWordWrap(True)
        lbl3.setTextFormat(Qt.TextFormat.RichText)
        l3.addWidget(lbl3)
        v.addWidget(gb3)

        v.addStretch()
        self.tabs.addTab(tab, "⑦ Hồ sơ pháp lý")

    def _render_ho_so_phap_ly(self):
        if not self.last_result:
            return
        res = self.last_result
        cn = res["cn"]
        i = res["i"]
        pl = R.tra_phu_luc_nd105(cn["k"], i)
        self._render_ho_so_phan_loai(cn, i, pl)
        self._render_ho_so_danh_sach(pl)

    def _render_ho_so_phan_loai(self, cn, i, pl):
        pl1_status = "THUỘC" if pl["thuoc_pl1"] else "Không thuộc"
        if pl["thuoc_pl2"]:
            pl2_status = "THUỘC NHÓM " + str(pl["nhom_pl2"])
        else:
            pl2_status = "Không thuộc"
        bh_txt = "CÓ (bắt buộc)" if pl["bao_hiem_chay_no_bat_buoc"] else "Không"
        parts = []
        parts.append("<b>Công trình:</b> " + cn["t"] + "<br>")
        parts.append("DT " + str(i["dt"]) + " m², " + str(i["tang"])
                     + " tầng nổi, cao " + str(i["cao"]) + " m<br><br>")
        parts.append("<b>Phụ lục I:</b> " + pl1_status + "<br>")
        parts.append("&nbsp;&nbsp;Mục " + str(pl["pl1_muc"]) + ": "
                     + pl["pl1_ten_muc"] + "<br>")
        parts.append("&nbsp;&nbsp;Lý do: " + pl["pl1_ly_do"] + "<br><br>")
        parts.append("<b>Phụ lục II:</b> " + pl2_status + "<br>")
        parts.append("&nbsp;&nbsp;Mục " + str(pl["pl2_muc"]) + ": "
                     + pl["pl2_ten_muc"] + "<br>")
        parts.append("&nbsp;&nbsp;Lý do: " + pl["pl2_ly_do"] + "<br><br>")
        parts.append("<b>Tự kiểm tra:</b> " + pl["tan_suat_tu_kiem_tra"] + "<br>")
        parts.append("<b>Cơ quan kiểm tra:</b> "
                     + pl["tan_suat_co_quan_kiem_tra"] + "<br>")
        parts.append("<b>Báo cáo định kỳ:</b> trước 15/6 và 15/12 hằng năm<br>")
        parts.append("<b>Cơ quan quản lý:</b> " + pl["co_quan_kiem_tra"] + "<br>")
        parts.append("<b>Bảo hiểm cháy nổ:</b> " + bh_txt + "<br><br>")
        parts.append("<i>Căn cứ: " + pl["nguon"] + "</i>")
        self.lbl_phan_loai_nd105.setText("".join(parts))

    def _render_ho_so_danh_sach(self, pl):
        ds = R.danh_sach_ho_so_pccc(pl)
        links = R.links_mau_pccc()
        out = []
        out.append("<table cellpadding='4' style='font-size:13px;'>")
        out.append(
            "<tr style='background:#fde68a;font-weight:bold;'>"
            "<td>#</td><td>Tài liệu</td><td>Mẫu</td>"
            "<td align='center'>Bắt buộc</td>"
            "<td align='center'>Lưu 5 năm</td>"
            "<td>Ghi chú</td></tr>")
        for x in ds:
            if x["bat_buoc"]:
                bg = "#fef3c7"
                bb_icon = "<b>✓</b>"
            else:
                bg = "#ffffff"
                bb_icon = ""
            luu_icon = "✓" if x["luu_5_nam"] else ""
            mau = x["mau"] or "-"
            if mau != "-" and mau in links:
                mau = "<a href='" + links[mau] + "'>" + mau + "</a>"
            row = (
                "<tr style='background:" + bg + ";'>"
                "<td align='center'>" + str(x["so"]) + "</td>"
                "<td>" + x["ten"] + "</td>"
                "<td align='center'>" + mau + "</td>"
                "<td align='center'>" + bb_icon + "</td>"
                "<td align='center'>" + luu_icon + "</td>"
                "<td style='font-size:11px;color:#555;'>"
                + x["ghi_chu"] + "</td>"
                "</tr>")
            out.append(row)
        out.append("</table>")
        out.append(
            "<br><b>Link tải:</b> "
            "<a href='" + links["ND105_TOAN_VAN"]
            + "'>NĐ 105/2025/NĐ-CP toàn văn</a>"
            " &nbsp;·&nbsp; "
            "<a href='" + links["PC01"]
            + "'>Mẫu PC01–PC06 (TVPL)</a>")
        self.lbl_ds_ho_so.setText("".join(out))

    def _in_pdf(self):
        """In bảng báo giá ra máy in / lưu PDF qua hộp thoại in của Qt."""
        try:
            from PyQt6.QtPrintSupport import QPrintDialog, QPrinter
            from PyQt6.QtGui import QTextDocument
        except ImportError:
            QMessageBox.warning(self, "Thiếu module",
                                "Cần cài PyQt6-Qt6 để in/lưu PDF.")
            return
        doc = QTextDocument()
        doc.setHtml(self.txt_tu_van.toHtml())
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec():
            doc.print(printer)


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    w = TuVanPCCC(user="Phí Ngọc Tùng", user_phone="0934630366")
    w.show()
    sys.exit(app.exec())
