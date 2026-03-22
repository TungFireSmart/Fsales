from AI.ai_planner import plan_question
from AI.ai_safe_executor import run_query, apply_filter_on_last
from AI.ai_memory import set_last, get_last
from AI.ai_llm import ask_chatgpt
from AI.answer_types import AnswerType


def _aggregate(result: dict, mode: str):
    rows = result.get("rows", [])
    if not rows:
        return 0

    if mode == "SUM":
        return sum(r[0] for r in rows if isinstance(r[0], (int, float)))
    if mode == "COUNT":
        return len(rows)

    return None


def _format_list(result: dict, max_rows=20):
    cols = result.get("columns", [])
    rows = result.get("rows", [])

    lines = []
    for r in rows[:max_rows]:
        items = []
        for i, c in enumerate(cols):
            try:
                items.append(f"{c}={r[i]}")
            except:
                pass
        lines.append("- " + " | ".join(items))
    return "\n".join(lines)


def answer_manager_question(question: str) -> str:
    plan = plan_question(question)
    intent = plan.get("intent")
    atype = plan.get("answer_type", AnswerType.ANALYSIS.value)

    last_plan, last_result = get_last()

    # =========================
    # FOLLOW-UP
    # =========================
    if intent == "followup_filter":
        filtered = apply_filter_on_last(last_result, plan.get("filter_on_last", []))
        set_last(plan=plan, result=filtered)
        return _format_list(filtered)

    # =========================
    # QUERY
    # =========================
    if intent == "query":
        result = run_query(plan["query"])
        set_last(plan=plan, result=result)

        note = plan.get("note", "")

        # DIRECT NUMBER
        if atype == AnswerType.DIRECT_NUMBER.value:
            if note == "total_revenue":
                total = _aggregate(result, "SUM")
                return f"Tổng doanh số là {total:,.0f} VNĐ."
            if note == "count_quotes":
                total = _aggregate(result, "COUNT")
                return f"Tổng số báo giá là {total}."

        # LIST
        if atype == AnswerType.LIST.value:
            return _format_list(result)

        # ANALYSIS
        context = _format_list(result)
        return ask_chatgpt(f"""
Bạn là trợ lý quản lý CRM.
Dựa trên dữ liệu dưới đây, hãy phân tích ngắn gọn.

DỮ LIỆU:
{context}

CÂU HỎI:
{question}
""")

    # =========================
    # HELP / FALLBACK
    # =========================
    return ask_chatgpt(f"""
Bạn là trợ lý CRM nội bộ.
Nếu câu hỏi chưa rõ hoặc vượt khả năng hiện tại:
- nói rõ thiếu dữ liệu gì
- gợi ý cải tiến hệ thống

CÂU HỎI:
{question}
""")
