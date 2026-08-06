# -*- coding: utf-8 -*-
"""
Form implementation generated from reading ui file 'UI/tu_van_pccc.ui'

Tạo bằng tay theo style pyuic6. Anh có thể chỉnh layout trong Qt Designer
rồi regenerate bằng lệnh:
    pyuic6 UI/tu_van_pccc.ui -o UI/tu_van_pccc.py
"""

from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_TuVanPCCC_Window(object):
    def setupUi(self, TuVanPCCC_Window):
        TuVanPCCC_Window.setObjectName("TuVanPCCC_Window")
        TuVanPCCC_Window.resize(1380, 820)

        self.centralwidget = QtWidgets.QWidget(parent=TuVanPCCC_Window)
        self.centralwidget.setObjectName("centralwidget")
        self.rootLayout = QtWidgets.QHBoxLayout(self.centralwidget)
        self.rootLayout.setContentsMargins(8, 8, 8, 8)
        self.rootLayout.setSpacing(8)
        self.rootLayout.setObjectName("rootLayout")

        self.splitter = QtWidgets.QSplitter(parent=self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.splitter.setObjectName("splitter")

        # ========== CỘT TRÁI ==========
        self.panel_left = QtWidgets.QWidget(parent=self.splitter)
        self.panel_left.setMinimumSize(QtCore.QSize(360, 0))
        self.panel_left.setMaximumSize(QtCore.QSize(420, 16777215))
        self.panel_left.setObjectName("panel_left")
        self.leftLayout = QtWidgets.QVBoxLayout(self.panel_left)
        self.leftLayout.setContentsMargins(10, 10, 10, 10)
        self.leftLayout.setSpacing(8)
        self.leftLayout.setObjectName("leftLayout")

        # GroupBox: Thông tin công trình — Công năng SỬ DỤNG nằm dòng riêng
        # (label trên, combobox dưới, full width), 7 field còn lại dùng QFormLayout
        self.gb_ct = QtWidgets.QGroupBox(parent=self.panel_left)
        self.gb_ct.setObjectName("gb_ct")
        self.vl_ct = QtWidgets.QVBoxLayout(self.gb_ct)
        self.vl_ct.setObjectName("vl_ct")

        self.lab_cn = QtWidgets.QLabel(parent=self.gb_ct)
        self.lab_cn.setObjectName("lab_cn")
        self.vl_ct.addWidget(self.lab_cn)

        self.cbo_cong_nang = QtWidgets.QComboBox(parent=self.gb_ct)
        self.cbo_cong_nang.setObjectName("cbo_cong_nang")
        self.cbo_cong_nang.setMinimumSize(QtCore.QSize(0, 44))
        self.cbo_cong_nang.setSizeAdjustPolicy(
            QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.cbo_cong_nang.setStyleSheet(
            "QComboBox { padding: 6px 8px; font-size: 13px; }"
            "QComboBox QAbstractItemView { padding: 4px; }")
        self.vl_ct.addWidget(self.cbo_cong_nang)

        self.form_ct = QtWidgets.QFormLayout()
        self.form_ct.setObjectName("form_ct")
        self.vl_ct.addLayout(self.form_ct)

        self.lab_dt = QtWidgets.QLabel(parent=self.gb_ct)
        self.lab_dt.setObjectName("lab_dt")
        self.form_ct.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lab_dt)
        self.spin_dt = QtWidgets.QDoubleSpinBox(parent=self.gb_ct)
        self.spin_dt.setMinimumSize(QtCore.QSize(0, 28))
        self.spin_dt.setDecimals(1)
        self.spin_dt.setMaximum(9999999.0)
        self.spin_dt.setObjectName("spin_dt")
        self.form_ct.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.spin_dt)

        self.lab_cao = QtWidgets.QLabel(parent=self.gb_ct)
        self.lab_cao.setObjectName("lab_cao")
        self.form_ct.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lab_cao)
        self.spin_cao = QtWidgets.QDoubleSpinBox(parent=self.gb_ct)
        self.spin_cao.setMinimumSize(QtCore.QSize(0, 28))
        self.spin_cao.setDecimals(1)
        self.spin_cao.setMaximum(9999.0)
        self.spin_cao.setObjectName("spin_cao")
        self.form_ct.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.spin_cao)

        self.lab_tang = QtWidgets.QLabel(parent=self.gb_ct)
        self.lab_tang.setObjectName("lab_tang")
        self.form_ct.setWidget(3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lab_tang)
        self.spin_tang = QtWidgets.QSpinBox(parent=self.gb_ct)
        self.spin_tang.setMinimumSize(QtCore.QSize(0, 28))
        self.spin_tang.setMaximum(999)
        self.spin_tang.setValue(1)
        self.spin_tang.setObjectName("spin_tang")
        self.form_ct.setWidget(3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.spin_tang)

        self.lab_ham = QtWidgets.QLabel(parent=self.gb_ct)
        self.lab_ham.setObjectName("lab_ham")
        self.form_ct.setWidget(4, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lab_ham)
        self.spin_ham = QtWidgets.QSpinBox(parent=self.gb_ct)
        self.spin_ham.setMinimumSize(QtCore.QSize(0, 28))
        self.spin_ham.setMaximum(99)
        self.spin_ham.setObjectName("spin_ham")
        self.form_ct.setWidget(4, QtWidgets.QFormLayout.ItemRole.FieldRole, self.spin_ham)

        self.lab_phong = QtWidgets.QLabel(parent=self.gb_ct)
        self.lab_phong.setObjectName("lab_phong")
        self.form_ct.setWidget(5, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lab_phong)
        self.spin_so_phong = QtWidgets.QSpinBox(parent=self.gb_ct)
        self.spin_so_phong.setMinimumSize(QtCore.QSize(0, 28))
        self.spin_so_phong.setMaximum(9999)
        self.spin_so_phong.setObjectName("spin_so_phong")
        self.form_ct.setWidget(5, QtWidgets.QFormLayout.ItemRole.FieldRole, self.spin_so_phong)

        self.lbl_nguoi = QtWidgets.QLabel(parent=self.gb_ct)
        self.lbl_nguoi.setObjectName("lbl_nguoi")
        self.form_ct.setWidget(6, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lbl_nguoi)
        self.spin_nguoi = QtWidgets.QSpinBox(parent=self.gb_ct)
        self.spin_nguoi.setMinimumSize(QtCore.QSize(0, 28))
        self.spin_nguoi.setMaximum(999999)
        self.spin_nguoi.setObjectName("spin_nguoi")
        self.form_ct.setWidget(6, QtWidgets.QFormLayout.ItemRole.FieldRole, self.spin_nguoi)

        self.lbl_chau = QtWidgets.QLabel(parent=self.gb_ct)
        self.lbl_chau.setObjectName("lbl_chau")
        self.form_ct.setWidget(7, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lbl_chau)
        self.spin_chau = QtWidgets.QSpinBox(parent=self.gb_ct)
        self.spin_chau.setMinimumSize(QtCore.QSize(0, 28))
        self.spin_chau.setMaximum(99999)
        self.spin_chau.setObjectName("spin_chau")
        self.form_ct.setWidget(7, QtWidgets.QFormLayout.ItemRole.FieldRole, self.spin_chau)

        self.leftLayout.addWidget(self.gb_ct)

        # GroupBox: Thông tin khách hàng
        self.gb_kh = QtWidgets.QGroupBox(parent=self.panel_left)
        self.gb_kh.setObjectName("gb_kh")
        self.form_kh = QtWidgets.QFormLayout(self.gb_kh)
        self.form_kh.setObjectName("form_kh")

        # Row 0: Tên công ty
        self.lab_kh_cty = QtWidgets.QLabel(parent=self.gb_kh)
        self.lab_kh_cty.setObjectName("lab_kh_cty")
        self.form_kh.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lab_kh_cty)
        self.kh_cty = QtWidgets.QLineEdit(parent=self.gb_kh)
        self.kh_cty.setMinimumSize(QtCore.QSize(0, 28))
        self.kh_cty.setObjectName("kh_cty")
        self.form_kh.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.kh_cty)

        # Row 1: Người liên hệ
        self.lab_kh_ten = QtWidgets.QLabel(parent=self.gb_kh)
        self.lab_kh_ten.setObjectName("lab_kh_ten")
        self.form_kh.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lab_kh_ten)
        self.kh_ten = QtWidgets.QLineEdit(parent=self.gb_kh)
        self.kh_ten.setMinimumSize(QtCore.QSize(0, 28))
        self.kh_ten.setObjectName("kh_ten")
        self.form_kh.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.kh_ten)

        # Row 2: Điện thoại
        self.lab_kh_dt = QtWidgets.QLabel(parent=self.gb_kh)
        self.lab_kh_dt.setObjectName("lab_kh_dt")
        self.form_kh.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lab_kh_dt)
        self.kh_dt = QtWidgets.QLineEdit(parent=self.gb_kh)
        self.kh_dt.setMinimumSize(QtCore.QSize(0, 28))
        self.kh_dt.setObjectName("kh_dt")
        self.form_kh.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.kh_dt)

        # Row 3: Mã số thuế
        self.lab_kh_mst = QtWidgets.QLabel(parent=self.gb_kh)
        self.lab_kh_mst.setObjectName("lab_kh_mst")
        self.form_kh.setWidget(3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lab_kh_mst)
        self.kh_mst = QtWidgets.QLineEdit(parent=self.gb_kh)
        self.kh_mst.setMinimumSize(QtCore.QSize(0, 28))
        self.kh_mst.setObjectName("kh_mst")
        self.form_kh.setWidget(3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.kh_mst)

        # Row 4: Địa chỉ
        self.lab_kh_dc = QtWidgets.QLabel(parent=self.gb_kh)
        self.lab_kh_dc.setObjectName("lab_kh_dc")
        self.form_kh.setWidget(4, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lab_kh_dc)
        self.kh_dc = QtWidgets.QLineEdit(parent=self.gb_kh)
        self.kh_dc.setMinimumSize(QtCore.QSize(0, 28))
        self.kh_dc.setObjectName("kh_dc")
        self.form_kh.setWidget(4, QtWidgets.QFormLayout.ItemRole.FieldRole, self.kh_dc)

        # Row 5: V/v
        self.lab_kh_vv = QtWidgets.QLabel(parent=self.gb_kh)
        self.lab_kh_vv.setObjectName("lab_kh_vv")
        self.form_kh.setWidget(5, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lab_kh_vv)
        self.kh_vv = QtWidgets.QLineEdit(parent=self.gb_kh)
        self.kh_vv.setMinimumSize(QtCore.QSize(0, 28))
        self.kh_vv.setObjectName("kh_vv")
        self.form_kh.setWidget(5, QtWidgets.QFormLayout.ItemRole.FieldRole, self.kh_vv)

        self.leftLayout.addWidget(self.gb_kh)

        # Nút Phân tích
        self.but_run = QtWidgets.QPushButton(parent=self.panel_left)
        self.but_run.setMinimumSize(QtCore.QSize(0, 40))
        self.but_run.setStyleSheet(
            "QPushButton { background:#0f766e; color:white; font-weight:600; border-radius:6px; }\n"
            "QPushButton:hover { background:#0d8a80; }")
        self.but_run.setObjectName("but_run")
        self.leftLayout.addWidget(self.but_run)

        self.lbl_status = QtWidgets.QLabel(parent=self.panel_left)
        self.lbl_status.setStyleSheet("color:#666;")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setText("")
        self.lbl_status.setObjectName("lbl_status")
        self.leftLayout.addWidget(self.lbl_status)

        spacerLeft = QtWidgets.QSpacerItem(
            20, 40,
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding)
        self.leftLayout.addItem(spacerLeft)

        # ========== CỘT PHẢI: TABS ==========
        self.tabs = QtWidgets.QTabWidget(parent=self.splitter)
        self.tabs.setObjectName("tabs")

        # ----- Tab 1: Thiết bị bắt buộc -----
        self.tab_thiet_bi = QtWidgets.QWidget()
        self.tab_thiet_bi.setObjectName("tab_thiet_bi")
        self.lay_tb = QtWidgets.QVBoxLayout(self.tab_thiet_bi)
        self.lay_tb.setContentsMargins(10, 10, 10, 10)
        self.lay_tb.setObjectName("lay_tb")

        self.lbl_summary = QtWidgets.QLabel(parent=self.tab_thiet_bi)
        self.lbl_summary.setStyleSheet("padding:8px; background:#f1f5f9; border-radius:6px;")
        self.lbl_summary.setWordWrap(True)
        self.lbl_summary.setObjectName("lbl_summary")
        self.lay_tb.addWidget(self.lbl_summary)

        self.tb_thiet_bi = QtWidgets.QTableWidget(parent=self.tab_thiet_bi)
        self.tb_thiet_bi.setObjectName("tb_thiet_bi")
        self.lay_tb.addWidget(self.tb_thiet_bi)

        self.lbl_note = QtWidgets.QLabel(parent=self.tab_thiet_bi)
        self.lbl_note.setStyleSheet("color:#b45309; padding:6px; background:#fffbeb; border-radius:6px;")
        self.lbl_note.setWordWrap(True)
        self.lbl_note.setText("")
        self.lbl_note.setObjectName("lbl_note")
        self.lay_tb.addWidget(self.lbl_note)

        self.tabs.addTab(self.tab_thiet_bi, "")

        # ----- Tab 2: Gian phòng -----
        self.tab_phong = QtWidgets.QWidget()
        self.tab_phong.setObjectName("tab_phong")
        self.lay_phong = QtWidgets.QVBoxLayout(self.tab_phong)
        self.lay_phong.setContentsMargins(10, 10, 10, 10)
        self.lay_phong.setObjectName("lay_phong")

        # Row định mức
        self.row_dm = QtWidgets.QHBoxLayout()
        self.lab_dm1 = QtWidgets.QLabel(parent=self.tab_phong)
        self.lab_dm1.setObjectName("lab_dm1")
        self.row_dm.addWidget(self.lab_dm1)
        self.sp_dt_khoi = QtWidgets.QDoubleSpinBox(parent=self.tab_phong)
        self.sp_dt_khoi.setMinimumSize(QtCore.QSize(0, 28))
        self.sp_dt_khoi.setDecimals(0)
        self.sp_dt_khoi.setMaximum(999.0)
        self.sp_dt_khoi.setValue(60.0)
        self.sp_dt_khoi.setObjectName("sp_dt_khoi")
        self.row_dm.addWidget(self.sp_dt_khoi)
        self.lab_dm2 = QtWidgets.QLabel(parent=self.tab_phong)
        self.lab_dm2.setObjectName("lab_dm2")
        self.row_dm.addWidget(self.lab_dm2)
        self.sp_dt_nhiet = QtWidgets.QDoubleSpinBox(parent=self.tab_phong)
        self.sp_dt_nhiet.setMinimumSize(QtCore.QSize(0, 28))
        self.sp_dt_nhiet.setDecimals(0)
        self.sp_dt_nhiet.setMaximum(999.0)
        self.sp_dt_nhiet.setValue(20.0)
        self.sp_dt_nhiet.setObjectName("sp_dt_nhiet")
        self.row_dm.addWidget(self.sp_dt_nhiet)
        self.lab_dm3 = QtWidgets.QLabel(parent=self.tab_phong)
        self.lab_dm3.setObjectName("lab_dm3")
        self.row_dm.addWidget(self.lab_dm3)
        self.row_dm.addItem(QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum))
        self.lay_phong.addLayout(self.row_dm)

        # Row bulk-add
        self.row_bulk = QtWidgets.QHBoxLayout()
        self.lab_bk1 = QtWidgets.QLabel(parent=self.tab_phong)
        self.lab_bk1.setObjectName("lab_bk1")
        self.row_bulk.addWidget(self.lab_bk1)
        self.bk_n = QtWidgets.QSpinBox(parent=self.tab_phong)
        self.bk_n.setMinimumSize(QtCore.QSize(0, 28))
        self.bk_n.setMaximum(999)
        self.bk_n.setValue(1)
        self.bk_n.setObjectName("bk_n")
        self.row_bulk.addWidget(self.bk_n)
        self.lab_bk2 = QtWidgets.QLabel(parent=self.tab_phong)
        self.lab_bk2.setObjectName("lab_bk2")
        self.row_bulk.addWidget(self.lab_bk2)
        self.bk_dt = QtWidgets.QDoubleSpinBox(parent=self.tab_phong)
        self.bk_dt.setMinimumSize(QtCore.QSize(0, 28))
        self.bk_dt.setDecimals(1)
        self.bk_dt.setMaximum(9999.0)
        self.bk_dt.setValue(20.0)
        self.bk_dt.setObjectName("bk_dt")
        self.row_bulk.addWidget(self.bk_dt)
        self.lab_bk3 = QtWidgets.QLabel(parent=self.tab_phong)
        self.lab_bk3.setObjectName("lab_bk3")
        self.row_bulk.addWidget(self.lab_bk3)
        self.bk_func = QtWidgets.QComboBox(parent=self.tab_phong)
        self.bk_func.setObjectName("bk_func")
        self.row_bulk.addWidget(self.bk_func)
        self.lab_bk4 = QtWidgets.QLabel(parent=self.tab_phong)
        self.lab_bk4.setObjectName("lab_bk4")
        self.row_bulk.addWidget(self.lab_bk4)
        self.bk_pre = QtWidgets.QLineEdit(parent=self.tab_phong)
        self.bk_pre.setMaximumSize(QtCore.QSize(60, 16777215))
        self.bk_pre.setObjectName("bk_pre")
        self.row_bulk.addWidget(self.bk_pre)
        self.but_bulk_add = QtWidgets.QPushButton(parent=self.tab_phong)
        self.but_bulk_add.setObjectName("but_bulk_add")
        self.row_bulk.addWidget(self.but_bulk_add)
        self.but_gen_rooms = QtWidgets.QPushButton(parent=self.tab_phong)
        self.but_gen_rooms.setObjectName("but_gen_rooms")
        self.row_bulk.addWidget(self.but_gen_rooms)
        self.but_add_room = QtWidgets.QPushButton(parent=self.tab_phong)
        self.but_add_room.setObjectName("but_add_room")
        self.row_bulk.addWidget(self.but_add_room)
        self.row_bulk.addItem(QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum))
        self.lay_phong.addLayout(self.row_bulk)

        self.tb_rooms = QtWidgets.QTableWidget(parent=self.tab_phong)
        self.tb_rooms.setObjectName("tb_rooms")
        self.lay_phong.addWidget(self.tb_rooms)

        self.lbl_phong_tong = QtWidgets.QLabel(parent=self.tab_phong)
        self.lbl_phong_tong.setStyleSheet("padding:8px; background:#ecfdf5; border-radius:6px;")
        self.lbl_phong_tong.setText("")
        self.lbl_phong_tong.setObjectName("lbl_phong_tong")
        self.lay_phong.addWidget(self.lbl_phong_tong)

        self.tabs.addTab(self.tab_phong, "")

        # ----- Tab 3: Thoát nạn -----
        self.tab_thoat_nan = QtWidgets.QWidget()
        self.tab_thoat_nan.setObjectName("tab_thoat_nan")
        self.lay_tn = QtWidgets.QVBoxLayout(self.tab_thoat_nan)
        self.lay_tn.setContentsMargins(10, 10, 10, 10)
        self.lay_tn.setObjectName("lay_tn")

        self.gb_tn = QtWidgets.QGroupBox(parent=self.tab_thoat_nan)
        self.gb_tn.setObjectName("gb_tn")
        self.form_tn = QtWidgets.QFormLayout(self.gb_tn)
        self.form_tn.setObjectName("form_tn")

        def _add_tn(row_i, name_lab, name_w, widget):
            lab = QtWidgets.QLabel(parent=self.gb_tn)
            lab.setObjectName(name_lab)
            self.form_tn.setWidget(row_i, QtWidgets.QFormLayout.ItemRole.LabelRole, lab)
            widget.setObjectName(name_w)
            widget.setMinimumSize(QtCore.QSize(0, 28))
            self.form_tn.setWidget(row_i, QtWidgets.QFormLayout.ItemRole.FieldRole, widget)
            return lab

        self.tn_kc_sc = QtWidgets.QDoubleSpinBox(parent=self.gb_tn)
        self.tn_kc_sc.setDecimals(0); self.tn_kc_sc.setMaximum(999.0); self.tn_kc_sc.setValue(15.0)
        self.lab_tn1 = _add_tn(0, "lab_tn1", "tn_kc_sc", self.tn_kc_sc)

        self.tn_kc_exit = QtWidgets.QDoubleSpinBox(parent=self.gb_tn)
        self.tn_kc_exit.setDecimals(0); self.tn_kc_exit.setMaximum(999.0); self.tn_kc_exit.setValue(30.0)
        self.lab_tn2 = _add_tn(1, "lab_tn2", "tn_kc_exit", self.tn_kc_exit)

        self.tn_loi_ra_ngoai = QtWidgets.QSpinBox(parent=self.gb_tn)
        self.tn_loi_ra_ngoai.setMaximum(999)
        self.lab_tn3 = _add_tn(2, "lab_tn3", "tn_loi_ra_ngoai", self.tn_loi_ra_ngoai)

        self.tn_cau_thang = QtWidgets.QSpinBox(parent=self.gb_tn)
        self.tn_cau_thang.setMaximum(999)
        self.lab_tn4 = _add_tn(3, "lab_tn4", "tn_cau_thang", self.tn_cau_thang)

        self.tn_loi_ra_phong = QtWidgets.QSpinBox(parent=self.gb_tn)
        self.tn_loi_ra_phong.setMaximum(99999)
        self.lab_tn5 = _add_tn(4, "lab_tn5", "tn_loi_ra_phong", self.tn_loi_ra_phong)

        self.tn_dai_hl = QtWidgets.QDoubleSpinBox(parent=self.gb_tn)
        self.tn_dai_hl.setDecimals(1); self.tn_dai_hl.setMaximum(9999.0)
        self.lab_tn6 = _add_tn(5, "lab_tn6", "tn_dai_hl", self.tn_dai_hl)

        self.tn_chieu_nghi = QtWidgets.QSpinBox(parent=self.gb_tn)
        self.tn_chieu_nghi.setMaximum(999)
        self.lab_tn7 = _add_tn(6, "lab_tn7", "tn_chieu_nghi", self.tn_chieu_nghi)

        self.lay_tn.addWidget(self.gb_tn)

        self.lbl_tn_result = QtWidgets.QLabel(parent=self.tab_thoat_nan)
        self.lbl_tn_result.setStyleSheet("padding:10px; background:#eff6ff; border-radius:6px;")
        self.lbl_tn_result.setWordWrap(True)
        self.lbl_tn_result.setObjectName("lbl_tn_result")
        self.lay_tn.addWidget(self.lbl_tn_result)
        self.lay_tn.addItem(QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Expanding))

        self.tabs.addTab(self.tab_thoat_nan, "")

        # ----- Tab 4: Báo giá -----
        self.tab_bao_gia = QtWidgets.QWidget()
        self.tab_bao_gia.setObjectName("tab_bao_gia")
        self.lay_bg = QtWidgets.QVBoxLayout(self.tab_bao_gia)
        self.lay_bg.setContentsMargins(10, 10, 10, 10)
        self.lay_bg.setSpacing(6)
        self.lay_bg.setObjectName("lay_bg")

        self.row_bg_bar = QtWidgets.QHBoxLayout()
        self.lbl_bg_info = QtWidgets.QLabel(parent=self.tab_bao_gia)
        self.lbl_bg_info.setStyleSheet("color:#666;")
        self.lbl_bg_info.setObjectName("lbl_bg_info")
        self.row_bg_bar.addWidget(self.lbl_bg_info, 1)
        self.but_doi_model = QtWidgets.QPushButton(parent=self.tab_bao_gia)
        self.but_doi_model.setObjectName("but_doi_model")
        self.row_bg_bar.addWidget(self.but_doi_model)
        self.but_them_dong = QtWidgets.QPushButton(parent=self.tab_bao_gia)
        self.but_them_dong.setObjectName("but_them_dong")
        self.row_bg_bar.addWidget(self.but_them_dong)
        self.but_xoa_dong = QtWidgets.QPushButton(parent=self.tab_bao_gia)
        self.but_xoa_dong.setObjectName("but_xoa_dong")
        self.row_bg_bar.addWidget(self.but_xoa_dong)
        self.lay_bg.addLayout(self.row_bg_bar)

        self.tb_bg = QtWidgets.QTableWidget(parent=self.tab_bao_gia)
        self.tb_bg.setObjectName("tb_bg")
        self.lay_bg.addWidget(self.tb_bg)

        self.lbl_tong = QtWidgets.QLabel(parent=self.tab_bao_gia)
        self.lbl_tong.setStyleSheet(
            "padding:10px; background:#1e293b; color:white; "
            "border-radius:6px; font-weight:600;")
        self.lbl_tong.setText("")
        self.lbl_tong.setObjectName("lbl_tong")
        self.lay_bg.addWidget(self.lbl_tong)

        self.row_bg_btns = QtWidgets.QHBoxLayout()
        self.but_xuat_excel = QtWidgets.QPushButton(parent=self.tab_bao_gia)
        self.but_xuat_excel.setMinimumSize(QtCore.QSize(0, 34))
        self.but_xuat_excel.setStyleSheet(
            "QPushButton { background:#0ea5e9; color:white; font-weight:600; "
            "padding:6px 16px; border-radius:6px; }\n"
            "QPushButton:hover { background:#0284c7; }")
        self.but_xuat_excel.setObjectName("but_xuat_excel")
        self.row_bg_btns.addWidget(self.but_xuat_excel)
        self.but_in_pdf = QtWidgets.QPushButton(parent=self.tab_bao_gia)
        self.but_in_pdf.setMinimumSize(QtCore.QSize(0, 34))
        self.but_in_pdf.setObjectName("but_in_pdf")
        self.row_bg_btns.addWidget(self.but_in_pdf)
        self.row_bg_btns.addItem(QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum))
        self.lay_bg.addLayout(self.row_bg_btns)

        self.tabs.addTab(self.tab_bao_gia, "")

        # ----- Tab 5: Nội dung tư vấn -----
        self.tab_tu_van = QtWidgets.QWidget()
        self.tab_tu_van.setObjectName("tab_tu_van")
        self.lay_tv = QtWidgets.QVBoxLayout(self.tab_tu_van)
        self.lay_tv.setContentsMargins(10, 10, 10, 10)
        self.lay_tv.setObjectName("lay_tv")
        self.txt_tu_van = QtWidgets.QTextEdit(parent=self.tab_tu_van)
        self.txt_tu_van.setObjectName("txt_tu_van")
        self.lay_tv.addWidget(self.txt_tu_van)
        self.tabs.addTab(self.tab_tu_van, "")

        self.rootLayout.addWidget(self.splitter)
        TuVanPCCC_Window.setCentralWidget(self.centralwidget)

        self.retranslateUi(TuVanPCCC_Window)
        self.tabs.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(TuVanPCCC_Window)

    def retranslateUi(self, TuVanPCCC_Window):
        _t = QtCore.QCoreApplication.translate
        TuVanPCCC_Window.setWindowTitle(_t("TuVanPCCC_Window",
            "Tư vấn & Báo giá PCCC — QCVN 10:2025/BCA"))
        self.gb_ct.setTitle(_t("TuVanPCCC_Window", "Thông tin công trình"))
        self.lab_cn.setText(_t("TuVanPCCC_Window", "Công năng sử dụng:"))
        self.lab_dt.setText(_t("TuVanPCCC_Window", "Tổng diện tích sàn (m²):"))
        self.lab_cao.setText(_t("TuVanPCCC_Window", "Chiều cao PCCC (m):"))
        self.lab_tang.setText(_t("TuVanPCCC_Window", "Số tầng nổi:"))
        self.lab_ham.setText(_t("TuVanPCCC_Window", "Số tầng hầm:"))
        self.lab_phong.setText(_t("TuVanPCCC_Window", "Số phòng (gian):"))
        self.lbl_nguoi.setText(_t("TuVanPCCC_Window", "Số người / chỗ ngồi:"))
        self.lbl_chau.setText(_t("TuVanPCCC_Window", "Số cháu (mầm non):"))
        self.gb_kh.setTitle(_t("TuVanPCCC_Window", "Thông tin khách hàng"))
        self.lab_kh_cty.setText(_t("TuVanPCCC_Window", "Tên công ty:"))
        self.lab_kh_ten.setText(_t("TuVanPCCC_Window", "Người liên hệ:"))
        self.lab_kh_dt.setText(_t("TuVanPCCC_Window", "Điện thoại:"))
        self.lab_kh_mst.setText(_t("TuVanPCCC_Window", "Mã số thuế:"))
        self.lab_kh_dc.setText(_t("TuVanPCCC_Window", "Địa chỉ:"))
        self.lab_kh_vv.setText(_t("TuVanPCCC_Window", "V/v:"))
        self.kh_vv.setText(_t("TuVanPCCC_Window", "Cung cấp lắp đặt hệ thống PCCC"))
        self.but_run.setText(_t("TuVanPCCC_Window", "⚡ Phân tích & lập báo giá"))

        self.lbl_summary.setText(_t("TuVanPCCC_Window",
            "Nhập thông tin công trình bên trái rồi bấm Phân tích."))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_thiet_bi),
            _t("TuVanPCCC_Window", "① Thiết bị bắt buộc"))

        self.lab_dm1.setText(_t("TuVanPCCC_Window", "Định mức:  1 đầu báo khói /"))
        self.lab_dm2.setText(_t("TuVanPCCC_Window", "m²    1 đầu báo nhiệt /"))
        self.lab_dm3.setText(_t("TuVanPCCC_Window", "m²"))
        self.lab_bk1.setText(_t("TuVanPCCC_Window", "Nhập nhanh — Số phòng:"))
        self.lab_bk2.setText(_t("TuVanPCCC_Window", "DT mỗi phòng (m²):"))
        self.lab_bk3.setText(_t("TuVanPCCC_Window", "Công năng:"))
        self.lab_bk4.setText(_t("TuVanPCCC_Window", "Tiền tố:"))
        self.bk_pre.setText(_t("TuVanPCCC_Window", "P"))
        self.but_bulk_add.setText(_t("TuVanPCCC_Window", "+ Thêm hàng loạt"))
        self.but_gen_rooms.setText(_t("TuVanPCCC_Window", "↻ Tạo từ \"Số phòng\""))
        self.but_add_room.setText(_t("TuVanPCCC_Window", "+ 1 phòng"))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_phong),
            _t("TuVanPCCC_Window", "② Gian phòng (báo cháy)"))

        self.gb_tn.setTitle(_t("TuVanPCCC_Window",
            "Tham số thoát nạn (TCVN 13456:2022)"))
        self.lab_tn1.setText(_t("TuVanPCCC_Window",
            "Khoảng cách tối đa giữa các đèn sự cố (m):"))
        self.lab_tn2.setText(_t("TuVanPCCC_Window",
            "Khoảng cách tối đa giữa các đèn EXIT (m):"))
        self.lab_tn3.setText(_t("TuVanPCCC_Window",
            "Số lối ra ngoài nhà (cửa thoát ra ngoài):"))
        self.lab_tn4.setText(_t("TuVanPCCC_Window", "Số cầu thang thoát nạn:"))
        self.lab_tn5.setText(_t("TuVanPCCC_Window",
            "Số cửa phòng dẫn ra hành lang (toàn công trình):"))
        self.lab_tn6.setText(_t("TuVanPCCC_Window", "Tổng chiều dài hành lang (m):"))
        self.lab_tn7.setText(_t("TuVanPCCC_Window", "Số chiếu nghỉ cầu thang:"))
        self.lbl_tn_result.setText(_t("TuVanPCCC_Window",
            "Nhập số liệu để app tính số đèn EXIT + đèn chiếu sáng sự cố."))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_thoat_nan),
            _t("TuVanPCCC_Window", "③ Thoát nạn & chiếu sáng"))

        self.lbl_bg_info.setText(_t("TuVanPCCC_Window",
            "Chưa có dữ liệu. Bấm Phân tích ở cột trái."))
        self.but_doi_model.setText(_t("TuVanPCCC_Window", "🔄 Đổi model dòng đã chọn"))
        self.but_them_dong.setText(_t("TuVanPCCC_Window", "➕ Thêm dòng"))
        self.but_xoa_dong.setText(_t("TuVanPCCC_Window", "🗑️ Xóa dòng"))
        self.but_xuat_excel.setText(_t("TuVanPCCC_Window", "📊 Xuất báo giá Excel"))
        self.but_in_pdf.setText(_t("TuVanPCCC_Window", "🖨️ In / Lưu PDF"))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_bao_gia),
            _t("TuVanPCCC_Window", "④ Báo giá"))

        self.txt_tu_van.setPlaceholderText(_t("TuVanPCCC_Window",
            "Chưa có dữ liệu. Bấm Phân tích ở cột trái."))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_tu_van),
            _t("TuVanPCCC_Window", "⑤ Nội dung tư vấn"))
