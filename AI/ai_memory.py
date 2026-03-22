# Memory theo phiên chat (in-memory)
# Có thể nâng cấp theo user/session sau.

_memory = {
    "last_result": None,      # {"columns":[...], "rows":[...], "sql":"...", "note":"..."}
    "last_plan": None,        # JSON plan
}

def set_last(plan=None, result=None):
    if plan is not None:
        _memory["last_plan"] = plan
    if result is not None:
        _memory["last_result"] = result

def get_last():
    return _memory["last_plan"], _memory["last_result"]

def clear():
    _memory["last_plan"] = None
    _memory["last_result"] = None
