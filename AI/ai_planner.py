import re
import json

from AI.ai_llm import ask_chatgpt
from AI.business_ontology import BUSINESS_ONTOLOGY
from AI.metric_dictionary import METRIC_DICTIONARY
from AI.db_ontology import DB_ONTOLOGY


SCHEMA_HINT = """
Bạn đang lập kế hoạch truy vấn dữ liệu từ CRM Fsales.

Bảng / field hợp lệ:

- ds_bao_gia: so_bg, lead_id, sotien, user, ngaythang, thanh_cong
- sale_lead: lead_id, name, company, sdt, mst, phu_trach, status, time_create
- ds_don_hang: so_bg, lead_id, tien_hang, vat, ngaythang, nguoi_tao, da_hoan_thanh
- ton_kho: ten_san_pham, model, ton, gia_dau_vao, ma_kho
- gia_tong_hop: ten_san_pham, model, nhan_hieu, don_vi, vat, gia_dau_vao

Thời gian:
- Tuần ISO: YEARWEEK(date_col, 1)
- Năm: YEAR(date_col)
- Tháng: YEAR + MONTH

JSON FORMAT:
{
  "intent": "query" | "followup_filter" | "help",
  "answer_type": "DIRECT_NUMBER" | "LIST" | "ANALYSIS",
  "query": {...},
  "filter_on_last": [...],
  "note": "..."
}
"""


def _parse_time(q: str):
    year = None
    month = None

    m_year = re.search(r"\b(20\d{2})\b", q)
    if m_year:
        year = int(m_year.group(1))

    m_month = re.search(r"tháng\s*(\d{1,2})", q)
    if m_month:
        month = int(m_month.group(1))

    return year, month


def plan_question(user_question: str) -> dict:
    q = (user_question or "").strip().lower()
    year, month = _parse_time(q)

    # =========================
    # FOLLOW-UP
    # =========================
    if any(x in q for x in ["liệt kê", "liệt kê chúng", "trong số đó", "chúng"]):
        return {
            "intent": "followup_filter",
            "answer_type": "LIST",
            "filter_on_last": [],
            "note": "followup"
        }

    # =========================
    # TỔNG DOANH SỐ
    # =========================
    if "doanh số" in q and not ("sale" in q or "nhân viên" in q):
        where = []
        if year:
            where.append({"field": "ngaythang", "op": "YEAR=", "value": year})
        if month:
            where.append({"field": "ngaythang", "op": "MONTH=", "value": month})

        return {
            "intent": "query",
            "answer_type": "DIRECT_NUMBER",
            "query": {
                "table": "ds_don_hang",
                "select": ["tien_hang"],
                "where": where,
                "group_by": [],
                "limit": 200
            },
            "note": "total_revenue"
        }

    # =========================
    # TOP SALE THEO DOANH SỐ
    # =========================
    if "doanh số" in q and ("sale" in q or "nhân viên" in q):
        where = []
        if year:
            where.append({"field": "ngaythang", "op": "YEAR=", "value": year})
        if month:
            where.append({"field": "ngaythang", "op": "MONTH=", "value": month})

        return {
            "intent": "query",
            "answer_type": "LIST",
            "query": {
                "table": "ds_don_hang",
                "select": ["nguoi_tao"],
                "where": where,
                "group_by": ["nguoi_tao"],
                "order_by": [{"field": "total", "direction": "desc"}],
                "limit": 5
            },
            "note": "top_sale_revenue"
        }

    # =========================
    # ĐẾM BÁO GIÁ
    # =========================
    if "báo giá" in q and any(x in q for x in ["bao nhiêu", "tổng", "số lượng"]):
        where = []
        if year:
            where.append({"field": "ngaythang", "op": "YEAR=", "value": year})
        if month:
            where.append({"field": "ngaythang", "op": "MONTH=", "value": month})
        if "tuần" in q:
            where.append({"field": "ngaythang", "op": "YEARWEEK_ISO=", "value": "THIS"})

        return {
            "intent": "query",
            "answer_type": "DIRECT_NUMBER",
            "query": {
                "table": "ds_bao_gia",
                "select": ["so_bg"],
                "where": where,
                "group_by": [],
                "limit": 200
            },
            "note": "count_quotes"
        }

    # =========================
    # FALLBACK → LLM PLANNER
    # =========================
    prompt = f"""
{BUSINESS_ONTOLOGY}

=== DATABASE ONTOLOGY ===
{DB_ONTOLOGY}

=== METRIC DICTIONARY ===
{METRIC_DICTIONARY}

{SCHEMA_HINT}

Câu hỏi:
{user_question}

Nếu không trả lời được:
- nói rõ thiếu dữ liệu gì
- đề xuất cải tiến code / DB
Chỉ trả JSON.
"""

    raw = ask_chatgpt(prompt)

    try:
        return json.loads(raw)
    except Exception:
        return {
            "intent": "help",
            "answer_type": "ANALYSIS",
            "note": "planner_failed"
        }
