# -*- coding: utf-8 -*-
"""Data layer cho tab Khảo sát — thu thập, áp dữ liệu, lưu, xuất.

v5: schema mở rộng cho 4 mẫu PC01-PC04 (NĐ 105/2025).
SSOT: tab Khảo sát là nguồn duy nhất cho mọi thông tin công trình + KH.
"""
import json
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QTableWidgetItem, QMessageBox, QFileDialog,
)
import misc


def _cell(tb, r, c):
    it = tb.item(r, c)
    return it.text() if it else ""


def _set_combo(cb, val):
    if val is None:
        return
    for k in range(cb.count()):
        if cb.itemData(k) == val:
            cb.setCurrentIndex(k)
            return


def _gop_nguoi(ten, chuc_vu, sdt):
    parts = [p.strip() for p in [ten, chuc_vu, sdt] if p and p.strip()]
    return " - ".join(parts)


def _set_date(de, val):
    """Set QDateEdit từ date/string/None. None hoặc invalid → giữ minDate."""
    if not val:
        return
    try:
        if hasattr(val, "year"):
            de.setDate(QDate(val.year, val.month, val.day))
        else:
            s = str(val)[:10]
            parts = s.split("-")
            if len(parts) == 3:
                de.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
    except Exception:
        pass


def _get_date(de):
    """Lấy QDateEdit → 'YYYY-MM-DD' hoặc None nếu là minDate (chưa nhập)."""
    d = de.date()
    if d == de.minimumDate():
        return None
    return d.toString("yyyy-MM-dd")


# =====================================================================
# Hệ thống PCCC sẵn có (table)
# =====================================================================
def add_ht_row(self, ten, tinh_trang, hang, read_only_name=False):
    r = self.ks_tb_ht_san_co.rowCount()
    self.ks_tb_ht_san_co.insertRow(r)
    it_ten = QTableWidgetItem(ten)
    if read_only_name:
        it_ten.setFlags(it_ten.flags() & ~Qt.ItemFlag.ItemIsEditable)
    self.ks_tb_ht_san_co.setItem(r, 0, it_ten)
    self.ks_tb_ht_san_co.setItem(r, 1, QTableWidgetItem(tinh_trang))
    self.ks_tb_ht_san_co.setItem(r, 2, QTableWidgetItem(hang))


def del_ht_row(self):
    r = self.ks_tb_ht_san_co.currentRow()
    if r < 0:
        return
    it = self.ks_tb_ht_san_co.item(r, 0)
    if it and not (it.flags() & Qt.ItemFlag.ItemIsEditable):
        QMessageBox.information(
            self, "Không thể xóa",
            "Không thể xóa 6 hệ thống mặc định.")
        return
    self.ks_tb_ht_san_co.removeRow(r)


# =====================================================================
# Khối nhà (PC01 mục II.2)
# =====================================================================
def add_khoi_nha_row(self, ten="", dtxd="", tang_noi="", tang_ham="",
                     bcl="II", cong_nang="", so_loi="2"):
    r = self.ks_tb_khoi_nha.rowCount()
    self.ks_tb_khoi_nha.insertRow(r)
    self.ks_tb_khoi_nha.setItem(r, 0, QTableWidgetItem(ten))
    self.ks_tb_khoi_nha.setItem(r, 1, QTableWidgetItem(str(dtxd)))
    self.ks_tb_khoi_nha.setItem(r, 2, QTableWidgetItem(str(tang_noi)))
    self.ks_tb_khoi_nha.setItem(r, 3, QTableWidgetItem(str(tang_ham)))
    self.ks_tb_khoi_nha.setItem(r, 4, QTableWidgetItem(bcl))
    self.ks_tb_khoi_nha.setItem(r, 5, QTableWidgetItem(cong_nang))
    self.ks_tb_khoi_nha.setItem(r, 6, QTableWidgetItem(str(so_loi)))


def del_khoi_nha_row(self):
    r = self.ks_tb_khoi_nha.currentRow()
    if r < 0:
        return
    self.ks_tb_khoi_nha.removeRow(r)


# =====================================================================
# Khu vực ngoài nhà (PC01 mục II.2)
# =====================================================================
def add_khu_vuc_row(self, ten="", dt="", day_chuyen=""):
    r = self.ks_tb_khu_vuc.rowCount()
    self.ks_tb_khu_vuc.insertRow(r)
    self.ks_tb_khu_vuc.setItem(r, 0, QTableWidgetItem(ten))
    self.ks_tb_khu_vuc.setItem(r, 1, QTableWidgetItem(str(dt)))
    self.ks_tb_khu_vuc.setItem(r, 2, QTableWidgetItem(day_chuyen))


def del_khu_vuc_row(self):
    r = self.ks_tb_khu_vuc.currentRow()
    if r < 0:
        return
    self.ks_tb_khu_vuc.removeRow(r)


# =====================================================================
# Upload tài liệu (10 checklist)
# =====================================================================
def upload_tai_lieu(self, doc_key, doc_label):
    if not self.lead_id:
        QMessageBox.warning(
            self, "Chưa có lead",
            "Chức năng upload chỉ dùng được khi mở từ form Update lead.")
        return
    file_path, _ = QFileDialog.getOpenFileName(
        self, f"Chọn file: {doc_label}", "", "Tất cả file (*.*)")
    if not file_path:
        return
    try:
        import file_handle
        info = file_handle.upload_file_to_lead_folder(
            self.lead_id, file_path, doc_key=doc_key)
    except Exception as e:
        QMessageBox.critical(self, "Lỗi upload", str(e))
        return
    if not info:
        QMessageBox.warning(self, "Upload thất bại",
                            "Không upload được lên Drive.")
        return
    self.ks_tai_lieu_drive[doc_key] = info
    self.ks_tai_lieu_checks[doc_key].setChecked(True)
    fname = info.split("|")[0]
    self.ks_tai_lieu_labels[doc_key].setText(f"✓ {fname[:50]}")
    self.ks_tai_lieu_labels[doc_key].setStyleSheet(
        "color: #059669; font-style: italic;")


# =====================================================================
# THU THẬP — đọc widget → dict (theo schema v4)
# =====================================================================
def thu_thap(self) -> dict:
    """Đọc widget khảo sát → dict (schema v4 PC01-PC04 ready)."""
    # Hệ thống PCCC sẵn có
    ht_data = []
    for r in range(self.ks_tb_ht_san_co.rowCount()):
        ten = _cell(self.ks_tb_ht_san_co, r, 0)
        if not ten.strip():
            continue
        ht_data.append({
            "ten": ten,
            "tinh_trang": _cell(self.ks_tb_ht_san_co, r, 1),
            "hang": _cell(self.ks_tb_ht_san_co, r, 2),
        })

    # Khối nhà (Group G)
    khoi_nha = []
    for r in range(self.ks_tb_khoi_nha.rowCount()):
        ten = _cell(self.ks_tb_khoi_nha, r, 0)
        if not ten.strip():
            continue
        khoi_nha.append({
            "ten_khoi": ten,
            "dt_xay_dung": _cell(self.ks_tb_khoi_nha, r, 1),
            "so_tang_noi": _cell(self.ks_tb_khoi_nha, r, 2),
            "so_tang_ham": _cell(self.ks_tb_khoi_nha, r, 3),
            "bac_chiu_lua": _cell(self.ks_tb_khoi_nha, r, 4),
            "cong_nang": _cell(self.ks_tb_khoi_nha, r, 5),
            "so_loi_thoat": _cell(self.ks_tb_khoi_nha, r, 6),
        })

    # Khu vực ngoài nhà
    khu_vuc = []
    for r in range(self.ks_tb_khu_vuc.rowCount()):
        ten = _cell(self.ks_tb_khu_vuc, r, 0)
        if not ten.strip():
            continue
        khu_vuc.append({
            "ten_khu_vuc": ten,
            "dt_su_dung": _cell(self.ks_tb_khu_vuc, r, 1),
            "day_chuyen_cn": _cell(self.ks_tb_khu_vuc, r, 2),
        })

    # Tài liệu checklist
    tl_data = {}
    for k, cb in self.ks_tai_lieu_checks.items():
        tl_data[k] = {
            "checked": cb.isChecked(),
            "drive_info": self.ks_tai_lieu_drive.get(k, ""),
        }

    # Nguồn nước multi
    nn_list = [k for k, cb in self.ks_nguon_nuoc_checks.items()
               if cb.isChecked()]

    return {
        # ========== A. Thông tin chung công trình + cơ sở ==========
        "kh_cty": self.ks_kh_cty.text().strip(),
        "kh_mst": self.ks_kh_mst.text().strip(),
        "ten_cong_trinh": self.ks_ten_cong_trinh.text().strip(),
        "dia_chi": self.ks_dia_chi.text().strip(),
        "cong_nang_k": self.ks_cong_nang.currentData() or "",
        "nam_hoat_dong":
            int(self.ks_nam_hoat_dong.value())
            if self.ks_nam_hoat_dong.value() > 0 else None,
        "nganh_nghe": self.ks_nganh_nghe.text().strip(),
        "hinh_thuc_so_huu": self.ks_hinh_thuc_so_huu.currentData(),
        "trang_thai": self.ks_trang_thai.currentData(),
        "thanh_phan_kt": self.ks_thanh_phan_kt.currentData() or "",
        "co_quan_cap_tren": self.ks_co_quan_cap_tren.text().strip(),
        "nguoi_quan_ly": self.ks_nguoi_quan_ly.text().strip(),
        "quan_ly_sdt": self.ks_quan_ly_sdt.text().strip(),
        "dai_dien_pl_ten": self.ks_dai_dien_pl_ten.text().strip(),
        "dai_dien_pl_sdt": self.ks_dai_dien_pl_sdt.text().strip(),
        "ct_doc_lap": 1 if self.ks_ct_doc_lap.isChecked() else 0,
        "thuoc_dm_nguyhiem":
            1 if self.ks_thuoc_dm_nguyhiem.isChecked() else 0,
        "thuoc_dm_thamduyet":
            1 if self.ks_thuoc_dm_thamduyet.isChecked() else 0,

        # ========== B. Quy mô + Kỹ thuật + Giao thông CC ==========
        "dt_san_tong": float(self.ks_dt_san_tong.value()),
        "dt_xay_dung": float(self.ks_dt_xay_dung.value()),
        "cao_pccc": float(self.ks_cao_pccc.value()),
        "so_tang_noi": int(self.ks_so_tang_noi.value()),
        "so_tang_ham": int(self.ks_so_tang_ham.value()),
        "so_phong": int(self.ks_so_phong.value()),
        "dai_nha": float(self.ks_dai_nha.value()),
        "rong_nha": float(self.ks_rong_nha.value()),
        "kc_ct_ke_ben": float(self.ks_kc_ct_ke_ben.value()),
        "bac_chiu_lua": self.ks_bac_chiu_lua.currentData(),
        "cap_nhc": self.ks_cap_nhc.currentData(),
        "hang_nguy_hiem": self.ks_hang_nguy_hiem.currentData(),
        "so_nguoi_du_kien": int(self.ks_so_nguoi_du_kien.value()),
        "so_nguoi": int(self.ks_so_nguoi_du_kien.value()),  # alias
        "so_chau": int(self.ks_so_chau.value()),
        "dgt_rong": float(self.ks_dgt_rong.value()),
        "dgt_cao": float(self.ks_dgt_cao.value()),
        "bai_do_xe_cc": self.ks_bai_do_xe_cc.text().strip(),
        "xe_cc_tiep_can": 1 if self.ks_xe_cc_tiep_can.isChecked() else 0,

        # ========== C. Hạ tầng + Hệ thống PCCC sẵn có ==========
        "nguon_nuoc": ",".join(nn_list),
        "nguon_nuoc_json": json.dumps(nn_list),
        "nguon_nuoc_chi_tiet": self.ks_nguon_nuoc_chi_tiet.text().strip(),
        "so_be_cc": int(self.ks_so_be_cc.value()),
        "khoi_tich_be": float(self.ks_khoi_tich_be.value()),
        "vi_tri_be": self.ks_vi_tri_be.text().strip(),
        "so_tru_cc": int(self.ks_so_tru_cc.value()),
        "vi_tri_tru": self.ks_vi_tri_tru.text().strip(),
        "nguon_dien": self.ks_nguon_dien.currentData(),
        "co_may_phat": 1 if self.ks_co_may_phat.isChecked() else 0,
        "mp_cong_suat_kva": float(self.ks_mp_cong_suat.value()),
        "mp_thoi_gian_chay_h": float(self.ks_mp_thoi_gian.value()),
        "truyen_tin_da_lap":
            1 if self.ks_truyen_tin_da_lap.isChecked() else 0,
        "co_xe_chua_chay":
            1 if self.ks_co_xe_chua_chay.isChecked() else 0,
        "phuong_tien_cc_text": self.ks_phuong_tien_cc.text().strip(),
        "he_thong_sn_json": json.dumps(ht_data, ensure_ascii=False),

        # ========== D. Pháp lý + Văn bản + Tài liệu ==========
        "vb_thamduyet_so": self.ks_vb_thamduyet_so.text().strip(),
        "vb_thamduyet_ngay": _get_date(self.ks_vb_thamduyet_ngay),
        "vb_thamduyet_cq": self.ks_vb_thamduyet_cq.text().strip(),
        "vb_nghiemthu_so": self.ks_vb_nghiemthu_so.text().strip(),
        "vb_nghiemthu_ngay": _get_date(self.ks_vb_nghiemthu_ngay),
        "vb_nghiemthu_cq": self.ks_vb_nghiemthu_cq.text().strip(),
        "bh_cong_ty": self.ks_bh_cong_ty.text().strip(),
        "bh_so_hd": self.ks_bh_so_hd.text().strip(),
        "bh_ngay_het_han": _get_date(self.ks_bh_ngay_het_han),
        "hd_bao_duong": 1 if self.ks_hd_bao_duong.isChecked() else 0,
        "hd_bao_duong_ncc": self.ks_hd_bao_duong_ncc.text().strip(),
        "tai_lieu_json": json.dumps(tl_data, ensure_ascii=False),
        "lich_su_pccc": self.ks_lich_su_pccc.toPlainText().strip(),
        "bkl_drive_info": getattr(self, "ks_bkl_drive_info", ""),

        # ========== E. Thương mại + Đánh giá sales ==========
        "yc_kh": self.ks_yc_kh.toPlainText().strip(),
        "ngan_sach": self.ks_ngan_sach.currentData(),
        "deadline": self.ks_deadline.text().strip(),
        "nguoi_quyet_dinh": _gop_nguoi(
            self.ks_qd_ten.text(), self.ks_qd_chuc_vu.text(),
            self.ks_qd_sdt.text()),
        "qd_ten": self.ks_qd_ten.text().strip(),
        "qd_chuc_vu": self.ks_qd_chuc_vu.text().strip(),
        "qd_sdt": self.ks_qd_sdt.text().strip(),
        "lien_he_ky_thuat": _gop_nguoi(
            self.ks_lh_ten.text(), self.ks_lh_chuc_vu.text(),
            self.ks_lh_sdt.text()),
        "lh_ten": self.ks_lh_ten.text().strip(),
        "lh_chuc_vu": self.ks_lh_chuc_vu.text().strip(),
        "lh_sdt": self.ks_lh_sdt.text().strip(),
        "doi_thu_da_bao_gia":
            1 if self.ks_doi_thu_da_bao_gia.isChecked() else 0,
        "doi_thu_ten": self.ks_doi_thu_ten.text().strip(),
        "danh_gia_sales": self.ks_danh_gia_sales.toPlainText().strip(),
        "buoc_tiep_theo": self.ks_buoc_tiep_theo.toPlainText().strip(),

        # ========== F. Khảo sát + Đội PCCC cơ sở ==========
        "ngay_khao_sat": self.ks_ngay_khao_sat.date().toString("yyyy-MM-dd"),
        "nguoi_khao_sat": self.ks_nguoi_khao_sat.text().strip(),
        "nguoi_tiep_don": _gop_nguoi(
            self.ks_td_ten.text(), self.ks_td_chuc_vu.text(),
            self.ks_td_sdt.text()),
        "td_ten": self.ks_td_ten.text().strip(),
        "td_chuc_vu": self.ks_td_chuc_vu.text().strip(),
        "td_sdt": self.ks_td_sdt.text().strip(),
        "doi_tong_doi_vien": int(self.ks_doi_tong.value()),
        "doi_truong_ten": self.ks_doi_truong_ten.text().strip(),
        "doi_truong_sdt": self.ks_doi_truong_sdt.text().strip(),
        "so_nguoi_pccc": int(self.ks_so_nguoi_pccc.value()),

        # ========== G. Khối nhà + Khu vực ngoài nhà (JSON) ==========
        "khoi_nha_json": json.dumps(khoi_nha, ensure_ascii=False),
        "khu_vuc_json": json.dumps(khu_vuc, ensure_ascii=False),
    }


DEFAULT_HT = {"Báo cháy tự động", "Sprinkler tự động",
              "Họng nước chữa cháy", "Bình chữa cháy",
              "Đèn EXIT + sự cố", "Cửa ngăn cháy"}


def ap_du_lieu(self, data: dict):
    """Áp dict (DB) vào widget."""
    if not data:
        return

    # ===== A. Thông tin chung =====
    self.ks_kh_cty.setText(data.get("kh_cty") or "")
    self.ks_kh_mst.setText(data.get("kh_mst") or "")
    self.ks_ten_cong_trinh.setText(data.get("ten_cong_trinh") or "")
    self.ks_dia_chi.setText(data.get("dia_chi") or "")
    _set_combo(self.ks_cong_nang, data.get("cong_nang_k"))
    if data.get("nam_hoat_dong"):
        try:
            self.ks_nam_hoat_dong.setValue(int(data["nam_hoat_dong"]))
        except (ValueError, TypeError):
            pass
    self.ks_nganh_nghe.setText(data.get("nganh_nghe") or "")
    _set_combo(self.ks_hinh_thuc_so_huu, data.get("hinh_thuc_so_huu"))
    _set_combo(self.ks_trang_thai, data.get("trang_thai"))
    _set_combo(self.ks_thanh_phan_kt, data.get("thanh_phan_kt"))
    self.ks_co_quan_cap_tren.setText(data.get("co_quan_cap_tren") or "")
    self.ks_nguoi_quan_ly.setText(data.get("nguoi_quan_ly") or "")
    self.ks_quan_ly_sdt.setText(data.get("quan_ly_sdt") or "")
    self.ks_dai_dien_pl_ten.setText(data.get("dai_dien_pl_ten") or "")
    self.ks_dai_dien_pl_sdt.setText(data.get("dai_dien_pl_sdt") or "")
    self.ks_ct_doc_lap.setChecked(bool(data.get("ct_doc_lap")))
    self.ks_thuoc_dm_nguyhiem.setChecked(bool(data.get("thuoc_dm_nguyhiem")))
    self.ks_thuoc_dm_thamduyet.setChecked(bool(data.get("thuoc_dm_thamduyet")))

    # ===== B. Quy mô + Kỹ thuật =====
    self.ks_dt_san_tong.setValue(float(data.get("dt_san_tong") or 0))
    self.ks_dt_xay_dung.setValue(float(data.get("dt_xay_dung") or 0))
    self.ks_cao_pccc.setValue(float(data.get("cao_pccc") or 0))
    self.ks_so_tang_noi.setValue(int(data.get("so_tang_noi") or 0))
    self.ks_so_tang_ham.setValue(int(data.get("so_tang_ham") or 0))
    self.ks_so_phong.setValue(int(data.get("so_phong") or 0))
    self.ks_dai_nha.setValue(float(data.get("dai_nha") or 0))
    self.ks_rong_nha.setValue(float(data.get("rong_nha") or 0))
    self.ks_kc_ct_ke_ben.setValue(float(data.get("kc_ct_ke_ben") or 0))
    _set_combo(self.ks_bac_chiu_lua, data.get("bac_chiu_lua"))
    _set_combo(self.ks_cap_nhc, data.get("cap_nhc"))
    _set_combo(self.ks_hang_nguy_hiem, data.get("hang_nguy_hiem"))
    self.ks_so_nguoi_du_kien.setValue(
        int(data.get("so_nguoi_du_kien") or data.get("so_nguoi") or 0))
    self.ks_so_chau.setValue(int(data.get("so_chau") or 0))
    self.ks_dgt_rong.setValue(float(data.get("dgt_rong") or 0))
    self.ks_dgt_cao.setValue(float(data.get("dgt_cao") or 0))
    self.ks_bai_do_xe_cc.setText(data.get("bai_do_xe_cc") or "")
    self.ks_xe_cc_tiep_can.setChecked(bool(data.get("xe_cc_tiep_can")))

    # ===== C. Hạ tầng =====
    nn_list = []
    if data.get("nguon_nuoc_json"):
        try:
            nn_list = json.loads(data["nguon_nuoc_json"])
        except Exception:
            pass
    elif data.get("nguon_nuoc"):
        nn_list = [x.strip() for x in str(data["nguon_nuoc"]).split(",")]
    for k, cb in self.ks_nguon_nuoc_checks.items():
        cb.setChecked(k in nn_list)
    self.ks_nguon_nuoc_chi_tiet.setText(data.get("nguon_nuoc_chi_tiet") or "")
    self.ks_so_be_cc.setValue(int(data.get("so_be_cc") or 0))
    self.ks_khoi_tich_be.setValue(float(data.get("khoi_tich_be") or 0))
    self.ks_vi_tri_be.setText(data.get("vi_tri_be") or "")
    self.ks_so_tru_cc.setValue(int(data.get("so_tru_cc") or 0))
    self.ks_vi_tri_tru.setText(data.get("vi_tri_tru") or "")
    _set_combo(self.ks_nguon_dien, data.get("nguon_dien"))
    self.ks_co_may_phat.setChecked(bool(data.get("co_may_phat")))
    self.ks_mp_cong_suat.setValue(float(data.get("mp_cong_suat_kva") or 0))
    self.ks_mp_thoi_gian.setValue(
        float(data.get("mp_thoi_gian_chay_h") or 0))
    self.ks_truyen_tin_da_lap.setChecked(bool(data.get("truyen_tin_da_lap")))
    self.ks_co_xe_chua_chay.setChecked(bool(data.get("co_xe_chua_chay")))
    self.ks_phuong_tien_cc.setText(data.get("phuong_tien_cc_text") or "")

    # Hệ thống PCCC sẵn có
    while self.ks_tb_ht_san_co.rowCount() > 0:
        self.ks_tb_ht_san_co.removeRow(0)
    try:
        ht_data = json.loads(data.get("he_thong_sn_json") or "[]")
        for ht in ht_data:
            ten = ht.get("ten", "")
            read_only = ten in DEFAULT_HT
            add_ht_row(self, ten, ht.get("tinh_trang", ""),
                       ht.get("hang", ""), read_only_name=read_only)
    except Exception:
        pass
    cur_names = {_cell(self.ks_tb_ht_san_co, r, 0)
                 for r in range(self.ks_tb_ht_san_co.rowCount())}
    for nm in DEFAULT_HT:
        if nm not in cur_names:
            add_ht_row(self, nm, "", "", read_only_name=True)

    # ===== D. Pháp lý + Tài liệu =====
    self.ks_vb_thamduyet_so.setText(data.get("vb_thamduyet_so") or "")
    _set_date(self.ks_vb_thamduyet_ngay, data.get("vb_thamduyet_ngay"))
    self.ks_vb_thamduyet_cq.setText(data.get("vb_thamduyet_cq") or "")
    self.ks_vb_nghiemthu_so.setText(data.get("vb_nghiemthu_so") or "")
    _set_date(self.ks_vb_nghiemthu_ngay, data.get("vb_nghiemthu_ngay"))
    self.ks_vb_nghiemthu_cq.setText(data.get("vb_nghiemthu_cq") or "")
    self.ks_bh_cong_ty.setText(data.get("bh_cong_ty") or "")
    self.ks_bh_so_hd.setText(data.get("bh_so_hd") or "")
    _set_date(self.ks_bh_ngay_het_han, data.get("bh_ngay_het_han"))
    self.ks_hd_bao_duong.setChecked(bool(data.get("hd_bao_duong")))
    self.ks_hd_bao_duong_ncc.setText(data.get("hd_bao_duong_ncc") or "")
    self.ks_lich_su_pccc.setPlainText(data.get("lich_su_pccc") or "")

    # Tài liệu checklist + Drive info
    try:
        tl_data = json.loads(data.get("tai_lieu_json") or "{}")
        for k, cb in self.ks_tai_lieu_checks.items():
            v = tl_data.get(k)
            if isinstance(v, dict):
                cb.setChecked(bool(v.get("checked")))
                info = v.get("drive_info") or ""
                if info:
                    self.ks_tai_lieu_drive[k] = info
                    fname = info.split("|")[0]
                    self.ks_tai_lieu_labels[k].setText(f"OK {fname[:50]}")
                    self.ks_tai_lieu_labels[k].setStyleSheet(
                        "color: #059669; font-style: italic;")
            else:
                cb.setChecked(bool(v))
    except Exception:
        pass

    # Bảng khối lượng đã upload
    bkl = data.get("bkl_drive_info") or ""
    if bkl:
        self.ks_bkl_drive_info = bkl
        fname = bkl.split("|")[0]
        if hasattr(self, "ks_bkl_status"):
            self.ks_bkl_status.setText(f"OK {fname[:60]}")
            self.ks_bkl_status.setStyleSheet(
                "color: #059669; font-style: italic;")

    # ===== E. Thương mại =====
    self.ks_yc_kh.setPlainText(data.get("yc_kh") or "")
    _set_combo(self.ks_ngan_sach, data.get("ngan_sach"))
    self.ks_deadline.setText(data.get("deadline") or "")
    self.ks_qd_ten.setText(data.get("qd_ten") or "")
    self.ks_qd_chuc_vu.setText(data.get("qd_chuc_vu") or "")
    self.ks_qd_sdt.setText(data.get("qd_sdt") or "")
    self.ks_lh_ten.setText(data.get("lh_ten") or "")
    self.ks_lh_chuc_vu.setText(data.get("lh_chuc_vu") or "")
    self.ks_lh_sdt.setText(data.get("lh_sdt") or "")
    self.ks_doi_thu_da_bao_gia.setChecked(
        bool(data.get("doi_thu_da_bao_gia")))
    self.ks_doi_thu_ten.setText(data.get("doi_thu_ten") or "")
    self.ks_danh_gia_sales.setPlainText(data.get("danh_gia_sales") or "")
    self.ks_buoc_tiep_theo.setPlainText(data.get("buoc_tiep_theo") or "")

    # ===== F. Khảo sát + Đội PCCC =====
    _set_date(self.ks_ngay_khao_sat, data.get("ngay_khao_sat"))
    self.ks_nguoi_khao_sat.setText(
        data.get("nguoi_khao_sat") or getattr(self, "user", "") or "")
    self.ks_td_ten.setText(data.get("td_ten") or "")
    self.ks_td_chuc_vu.setText(data.get("td_chuc_vu") or "")
    self.ks_td_sdt.setText(data.get("td_sdt") or "")
    self.ks_doi_tong.setValue(int(data.get("doi_tong_doi_vien") or 0))
    self.ks_doi_truong_ten.setText(data.get("doi_truong_ten") or "")
    self.ks_doi_truong_sdt.setText(data.get("doi_truong_sdt") or "")
    self.ks_so_nguoi_pccc.setValue(int(data.get("so_nguoi_pccc") or 0))

    # ===== G. Khối nhà + Khu vực ngoài nhà =====
    while self.ks_tb_khoi_nha.rowCount() > 0:
        self.ks_tb_khoi_nha.removeRow(0)
    try:
        kn = json.loads(data.get("khoi_nha_json") or "[]")
        for x in kn:
            add_khoi_nha_row(
                self, x.get("ten_khoi", ""), x.get("dt_xay_dung", ""),
                x.get("so_tang_noi", ""), x.get("so_tang_ham", ""),
                x.get("bac_chiu_lua", "II"), x.get("cong_nang", ""),
                x.get("so_loi_thoat", ""))
    except Exception:
        pass

    while self.ks_tb_khu_vuc.rowCount() > 0:
        self.ks_tb_khu_vuc.removeRow(0)
    try:
        kv = json.loads(data.get("khu_vuc_json") or "[]")
        for x in kv:
            add_khu_vuc_row(self, x.get("ten_khu_vuc", ""),
                            x.get("dt_su_dung", ""),
                            x.get("day_chuyen_cn", ""))
    except Exception:
        pass

    # Bật Group G nếu có dữ liệu
    if (data.get("khoi_nha_json") and data["khoi_nha_json"] != "[]") or \
       (data.get("khu_vuc_json") and data["khu_vuc_json"] != "[]"):
        self.ks_co_nhieu_khoi.setChecked(True)


def luu_khao_sat(self):
    if not self.lead_id:
        QMessageBox.warning(
            self, "Chua co lead",
            "Khao sat chi luu duoc khi mo tu form Update lead "
            "(nhan Ho tro tu van).")
        return
    try:
        data = thu_thap(self)
        misc.luu_khao_sat(self.lead_id, data)
        QMessageBox.information(
            self, "Da luu",
            f"Da luu khao sat cho Lead #{self.lead_id}.")
    except Exception as e:
        QMessageBox.critical(self, "Loi luu khao sat", str(e))


def xuat_bien_ban(self):
    try:
        data = thu_thap(self)
    except Exception as e:
        QMessageBox.critical(self, "Loi doc du lieu", str(e))
        return
    ten_ct = (data.get("ten_cong_trinh") or "cong_trinh")[:60]
    default_name = f"BB_khao_sat_{ten_ct}.docx"
    path, _ = QFileDialog.getSaveFileName(
        self, "Luu bien ban khao sat", default_name,
        "Word Files (*.docx)")
    if not path:
        return
    try:
        from bien_ban_khao_sat import xuat_bien_ban_khao_sat
        xuat_bien_ban_khao_sat(
            data, path,
            nguoi_lap=getattr(self, "user", ""),
            sdt_nguoi_lap=getattr(self, "user_phone", ""))
    except Exception as e:
        QMessageBox.critical(self, "Loi xuat Word", str(e))
        return
    upload_msg = ""
    if self.lead_id:
        try:
            import file_handle
            info = file_handle.upload_file_to_lead_folder(
                self.lead_id, path, doc_key="bien_ban_khao_sat")
            if info:
                old = misc.sql_one(
                    "SELECT file FROM sale_lead WHERE lead_id = %s",
                    (self.lead_id,))
                file_value = (old[0] + "@@" + info) if (old and old[0]) else info
                misc.sql_commit(
                    "UPDATE sale_lead SET file = %s WHERE lead_id = %s",
                    (file_value, self.lead_id))
                upload_msg = f"<br>Da dinh kem vao Lead #{self.lead_id}."
            else:
                upload_msg = "<br>Upload Drive that bai - file van luu local."
        except Exception as e:
            upload_msg = f"<br>Loi upload: {e}"
    QMessageBox.information(
        self, "Thanh cong",
        f"Da xuat bien ban:<br><b>{path}</b>{upload_msg}")
