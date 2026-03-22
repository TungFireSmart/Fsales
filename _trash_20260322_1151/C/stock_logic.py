from misc import sql_one, sql_all, sql_commit

class KhoService:
    def __init__(self):
        pass

    def get_ton_kho(self, model):
        kq = sql_one("SELECT SUM(so_luong) FROM ton_kho WHERE model = %s", (model,))
        return int(kq[0]) if kq and kq[0] else 0

    def can_xuat(self, model, so_luong):
        return self.get_ton_kho(model) >= so_luong

    def tru_ton(self, model, so_luong):
        if not self.can_xuat(model, so_luong):
            raise ValueError(f"Không đủ tồn kho để xuất {so_luong} sản phẩm {model}")

        ton_list = sql_all("SELECT id, so_luong FROM ton_kho WHERE model = %s ORDER BY ngay_nhap ASC", (model,))
        for ton_id, sl in ton_list:
            if so_luong <= 0:
                break
            tru = min(so_luong, sl)
            sql_commit("UPDATE ton_kho SET so_luong = so_luong - %s WHERE id = %s", (tru, ton_id))
            so_luong -= tru

    def cong_ton(self, model, so_luong, ten_kho, gia):
        sql_commit("INSERT INTO ton_kho (model, ten_kho, so_luong, gia) VALUES (%s, %s, %s, %s)",
                   (model, ten_kho, so_luong, gia))

    def get_ds_ton_kho(self):
        return sql_all("SELECT ten_kho, model, so_luong, gia FROM ton_kho ORDER BY ten_kho")
