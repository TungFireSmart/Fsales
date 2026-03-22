import types

import order_handle
import stock_handle

# ---- Monkeypatch popup/input ----
class DummyMsgBox:
    class StandardButton:
        Yes = 1
        No = 2

    @staticmethod
    def question(*args, **kwargs):
        return DummyMsgBox.StandardButton.Yes

    @staticmethod
    def warning(*args, **kwargs):
        return DummyMsgBox.StandardButton.Yes

    @staticmethod
    def information(*args, **kwargs):
        return DummyMsgBox.StandardButton.Yes

class DummyInput:
    @staticmethod
    def getInt(*args, **kwargs):
        return (1000000, True)

    @staticmethod
    def getText(*args, **kwargs):
        return ("test tra hang", True)

order_handle.QMessageBox = DummyMsgBox
order_handle.QInputDialog = DummyInput

# ---- Fake UI ----
class T:
    def __init__(self): self.v = ""
    def setText(self, v): self.v = str(v)
    def toPlainText(self): return self.v
    def repaint(self): pass

class L(T):
    def setStyleSheet(self, *_): pass

class DummyUIC6:
    def __init__(self):
        self.text_da_thanhtoan = T()
        self.text_phaithu = T()
        self.text_ghichu = T()
        self.label_mo_ta_lead = L()

# ---- Patch DB helpers for order_handle ----
updates = []

def sql_one(query, params=None):
    q = query.lower()
    if "from ds_don_hang" in q and "select da_thanh_toan" in q:
        # da_thanh_toan, phai_thu, ghi_chu, lich_su_gd
        return (1500000, 500000, "ghi chu cu", "ls_cu")
    if "from xuat_kho" in q and "order by id desc" in q:
        return (123,)
    return None

def sql_commit(query, params=None):
    updates.append((query, params))

def sql_all(query, params=None):
    return []

order_handle.misc.sql_one = sql_one
order_handle.misc.sql_commit = sql_commit
order_handle.misc.sql_all = sql_all
order_handle.misc.send_to_telegram = lambda msg: updates.append(("telegram", msg))

# ---- Patch StockHandle.tao_phieu_nhap for phase2 open form ----
def fake_tao_phieu_nhap(self):
    class C:
        def __init__(self): self.items=[]; self.cur=""
        def setCurrentIndex(self, *_): pass
        def findText(self, t): return 0 if t in self.items else -1
        def addItem(self, t): self.items.append(t)
        def setCurrentText(self, t): self.cur=t
        def currentText(self): return self.cur
    class Ch:
        def __init__(self): self.v=False
        def setChecked(self,v): self.v=v
        def isChecked(self): return self.v
    class X:
        def setText(self, *_): pass
        def setStyleSheet(self, *_): pass
    self.uic8 = types.SimpleNamespace(
        checkBox=Ch(),
        combo_so_px=C(),
        check_tra_lai=Ch(),
        text_nguyen_nhan=X(),
        label_noti=X(),
    )

order_handle.StockHandle.tao_phieu_nhap = fake_tao_phieu_nhap

# ---- Run phase2+4 flow ----
o = order_handle.OrderHandle.__new__(order_handle.OrderHandle)
o.user = "tester"
o.win_order = object()
o.uic6 = DummyUIC6()

order_handle.OrderHandle.tra_lai_hang(o, lead_id=10, so_bg=99)

assert any("update ds_don_hang" in q.lower() for q, _ in updates if isinstance(q, str)), "missing update ds_don_hang"
assert any("tra_lai_px" in str(p).lower() or "sale_lead" in q.lower() for q, p in updates if isinstance(q, str)), "missing downstream updates"

# ---- Phase 3 validation smoke ----n = stock_handle.StockHandle.__new__(stock_handle.StockHandle)

# patch misc in stock_handle
stock_logs = []

def s_sql_one(query, params=None):
    q = query.lower()
    if "from ton_kho" in q:
        return None
    return None

def s_sql_all(query, params=None):
    q = query.lower()
    if "select noi_dung from nhap_kho" in q:
        # already returned 3 for model M1
        return [("Ten|M1|3|1000|Kho Hà Nội@@Ten2|M2|0|1000|Kho Hà Nội",)]
    return []

def s_sql_commit(query, params=None):
    stock_logs.append((query, params))

stock_handle.misc.sql_one = s_sql_one
stock_handle.misc.sql_all = s_sql_all
stock_handle.misc.sql_commit = s_sql_commit

class Item:
    def __init__(self, t): self._t=t
    def text(self): return self._t

class Table:
    def __init__(self):
        # [ten, model, sl_xuat(gia tri col3), sl_nhap(col4)] per code mapping
        self.rows = [
            ["Ten", "M1", "", "5", "2"],
            ["Ten2", "M2", "", "4", "1"],
        ]
    def rowCount(self): return len(self.rows)
    def item(self, r, c): return Item(self.rows[r][c])

class Label:
    def __init__(self): self.msg=""
    def setStyleSheet(self, *_): pass
    def setText(self, t): self.msg=t

class Check:
    def __init__(self, v=False): self.v=v
    def isChecked(self): return self.v

class Combo:
    def currentText(self): return "Kho Hà Nội"

class ComboPx:
    def currentText(self): return "123"

class DateE:
    def text(self): return "13/03/2026"

class Text:
    def toPlainText(self): return "tra lai test"

n = stock_handle.StockHandle.__new__(stock_handle.StockHandle)

n.uic8 = types.SimpleNamespace(
    tableWidget=Table(),
    combo_kho=Combo(),
    combo_sophieu=types.SimpleNamespace(currentText=lambda: "9001"),
    dateEdit=DateE(),
    text_nguyen_nhan=Text(),
    check_bao_hanh=Check(False),
    check_tra_lai=Check(True),
    combo_so_px=ComboPx(),
    label_noti=Label(),
)
n.user = "tester"

stock_handle.StockHandle.luu_phieu_nhap_lai_tu_phieu_xuat(n)

# must pass and insert nhap_kho
assert any("insert into nhap_kho" in q.lower() for q, _ in stock_logs), "missing insert nhap_kho"
print("SMOKE_OK")
