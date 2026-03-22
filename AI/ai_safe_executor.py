import re
import misc

# =========================================================
#  CẤU HÌNH AN TOÀN
# =========================================================

# Các field TUYỆT ĐỐI KHÔNG cho AI đọc
FORBIDDEN_FIELDS = {
    "password", "pass", "passwd",
    "token", "secret", "api_key",
    "hash", "salt"
}

# Cache schema DB (đọc 1 lần)
_DB_SCHEMA_CACHE = {}

# =========================================================
#  OPERATOR ĐƯỢC PHÉP
# =========================================================

OPS = {"=", "!=", "<", ">", "<=", ">=", "LIKE", "IN"}
SPECIAL_OPS = {"YEAR=", "YEARWEEK_ISO=", "MONTH="}

# =========================================================
#  LOAD DB SCHEMA ĐỘNG
# =========================================================

def _load_db_schema():
    if _DB_SCHEMA_CACHE:
        return

    rows = misc.sql_all("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
    """)

    for table, column in rows:
        col = column.lower()
        if col in FORBIDDEN_FIELDS:
            continue
        _DB_SCHEMA_CACHE.setdefault(table.lower(), set()).add(column.lower())


# =========================================================
#  HÀM TIỆN ÍCH
# =========================================================

def _safe_ident(s: str) -> bool:
    """Chỉ cho phép chữ/số/_ để tránh injection"""
    return bool(re.fullmatch(r"[A-Za-z0-9_]+", s or ""))


def _check_table(table: str):
    _load_db_schema()
    if table.lower() not in _DB_SCHEMA_CACHE:
        raise ValueError(f"Table not found: {table}")


def _check_field(table: str, field: str):
    _load_db_schema()
    table_l = table.lower()
    field_l = field.lower()

    if field_l not in _DB_SCHEMA_CACHE.get(table_l, set()):
        raise ValueError(f"Field not allowed: {table}.{field}")


def _clamp_limit(limit):
    try:
        limit = int(limit)
    except Exception:
        limit = 50
    if limit <= 0:
        limit = 50
    if limit > 2000:
        limit = 2000
    return limit


# =========================================================
#  BUILD SQL AN TOÀN TỪ JSON PLAN
# =========================================================

def build_sql(query: dict):
    table = query.get("table")
    _check_table(table)

    # ---------- SELECT ----------
    select = query.get("select") or []

    if select == ["*"] or not select:
        raise ValueError("SELECT * is not allowed")

    for f in select:
        if not _safe_ident(f):
            raise ValueError("Unsafe select field")
        _check_field(table, f)

    select_sql = ", ".join(select)
    columns = select.copy()

    # ---------- GROUP BY ----------
    group_by = query.get("group_by") or []
    for g in group_by:
        if not _safe_ident(g):
            raise ValueError("Unsafe group field")
        _check_field(table, g)

    if group_by:
        select_sql = ", ".join(group_by) + ", COUNT(*) AS total"
        columns = list(group_by) + ["total"]

    # ---------- WHERE ----------
    where = query.get("where") or []
    where_sql_parts = []
    params = []

    for w in where:
        field = w.get("field")
        op = (w.get("op") or "=").upper()
        value = w.get("value")

        if not _safe_ident(field):
            raise ValueError("Unsafe where field")
        _check_field(table, field)

        if op not in OPS and op not in SPECIAL_OPS:
            raise ValueError(f"Operator not allowed: {op}")

        if op == "YEAR=":
            where_sql_parts.append(f"YEAR({field}) = %s")
            params.append(int(value))

        elif op == "MONTH=":
            where_sql_parts.append(f"MONTH({field}) = %s")
            params.append(int(value))

        elif op == "YEARWEEK_ISO=":
            where_sql_parts.append(
                f"YEARWEEK({field}, 1) = YEARWEEK(CURDATE(), 1)"
            )

        elif op == "IN":
            if not isinstance(value, list) or len(value) == 0 or len(value) > 100:
                raise ValueError("IN value invalid")
            placeholders = ",".join(["%s"] * len(value))
            where_sql_parts.append(f"{field} IN ({placeholders})")
            params.extend(value)

        elif op == "LIKE":
            where_sql_parts.append(f"{field} LIKE %s")
            params.append(str(value))

        else:
            where_sql_parts.append(f"{field} {op} %s")
            params.append(value)

    # ---------- ORDER BY ----------
    order_by = query.get("order_by") or []
    order_sql_parts = []

    for o in order_by:
        f = o.get("field")
        d = (o.get("direction") or "desc").lower()

        if not _safe_ident(f):
            raise ValueError("Unsafe order field")

        if f != "total":
            _check_field(table, f)

        if d not in {"asc", "desc"}:
            d = "desc"

        order_sql_parts.append(f"{f} {d}")

    # ---------- LIMIT ----------
    limit = _clamp_limit(query.get("limit", 50))

    # ---------- BUILD SQL ----------
    sql = f"SELECT {select_sql} FROM {table}"

    if where_sql_parts:
        sql += " WHERE " + " AND ".join(where_sql_parts)

    if group_by:
        sql += " GROUP BY " + ", ".join(group_by)

    if order_sql_parts:
        sql += " ORDER BY " + ", ".join(order_sql_parts)

    sql += f" LIMIT {limit}"

    return sql, tuple(params), columns


# =========================================================
#  THỰC THI QUERY AN TOÀN
# =========================================================

def run_query(query: dict):
    sql, params, columns = build_sql(query)
    rows = misc.sql_all(sql, params)

    return {
        "sql": sql,
        "columns": columns,
        "rows": rows,
    }


# =========================================================
#  FOLLOW-UP FILTER (KHÔNG QUERY LẠI DB)
# =========================================================

def apply_filter_on_last(last_result: dict, filters: list):
    if not last_result or not last_result.get("columns"):
        raise ValueError("No previous result to filter")

    cols = last_result["columns"]
    rows = last_result.get("rows", [])

    index = {c: i for i, c in enumerate(cols)}

    def _match(row):
        for f in filters:
            field = f.get("field")
            op = (f.get("op") or "=").upper()
            val = f.get("value")

            if field not in index:
                return False

            rv = row[index[field]]

            try:
                if op == ">":
                    if not rv > val: return False
                elif op == "<":
                    if not rv < val: return False
                elif op == ">=":
                    if not rv >= val: return False
                elif op == "<=":
                    if not rv <= val: return False
                elif op == "!=":
                    if not rv != val: return False
                elif op == "=":
                    if not rv == val: return False
                else:
                    return False
            except Exception:
                return False

        return True

    filtered_rows = [r for r in rows if _match(r)]

    return {
        "sql": last_result.get("sql", ""),
        "columns": cols,
        "rows": filtered_rows,
        "note": "filtered_on_last_result"
    }
