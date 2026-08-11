from PyQt6.QtWidgets import QLabel, QTableWidget, QHeaderView, QWidget, QComboBox


def _ensure_valid_font(widget, default_size=10):
    try:
        f = widget.font()
        if f.pointSize() <= 0:
            f.setPointSize(default_size)
            widget.setFont(f)
    except Exception:
        pass


def apply_ui_v2(window: QWidget):
    """Runtime UX polish applied after setupUi for each window/screen."""
    if window is None:
        return

    # Global font guard for this window tree (prevents pointSize=-1 warnings)
    _ensure_valid_font(window, 10)
    for w in window.findChildren(QWidget):
        _ensure_valid_font(w, 10)

    # Normalize all combo boxes: compact height + valid fonts
    for cb in window.findChildren(QComboBox):
        cb.setMinimumHeight(18)
        _ensure_valid_font(cb, 10)
        try:
            cb_view = cb.view()
            if cb_view is not None:
                _ensure_valid_font(cb_view, 10)
                cb_view.setMinimumHeight(160)
                cb_view.setStyleSheet((cb_view.styleSheet() or "") + " QAbstractItemView::item { min-height: 20px; }")
        except Exception:
            pass

    # Notification labels: easier to read + consistent
    for lb in window.findChildren(QLabel):
        name = (lb.objectName() or "").lower()
        if "label_noti" in name:
            lb.setWordWrap(True)
            lb.setMinimumHeight(28)
            lb.setStyleSheet(lb.styleSheet() + "; padding: 4px 8px; border-radius: 6px;")

    # Tables: zebra + better header behavior + consistent row height
    for tb in window.findChildren(QTableWidget):
        tb.setAlternatingRowColors(True)
        tb.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tb.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        tb.setShowGrid(False)
        try:
            tb.verticalHeader().setDefaultSectionSize(34)
            tb.horizontalHeader().setStretchLastSection(True)
            tb.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        except Exception:
            pass
