# -*- coding: utf-8 -*-
"""Chạy 1 file .sql vào DB Fsales (lấy connection từ misc.db_config).

Cách dùng:
    python run_sql_file.py insert_bom_affetti_20260617.sql
"""
import sys
import os

if len(sys.argv) < 2:
    sys.exit("Cu phap: python run_sql_file.py <file.sql>")

sql_file = sys.argv[1]
if not os.path.exists(sql_file):
    sys.exit(f"Khong tim thay file: {sql_file}")

import misc

print(f"Doc file: {sql_file}")
with open(sql_file, encoding="utf-8") as f:
    sql_text = f.read()

# Tách thành các statement (bỏ comment lines, split theo ';')
statements = []
buf = []
for line in sql_text.splitlines():
    s = line.strip()
    if not s or s.startswith("--"):
        continue
    buf.append(line)
    if s.endswith(";"):
        statements.append("\n".join(buf))
        buf = []
if buf:
    statements.append("\n".join(buf))

print(f"Tong: {len(statements)} statement")

# Connect + execute
conn = misc._connect()
cur = conn.cursor()
ok, fail = 0, 0
errors = []
for i, stmt in enumerate(statements, 1):
    try:
        cur.execute(stmt)
        ok += 1
    except Exception as e:
        fail += 1
        errors.append((i, str(e)[:200], stmt[:120]))

conn.commit()
cur.close()
conn.close()

print(f"\nKet qua: {ok} OK, {fail} loi")
if errors:
    print("\nMot so loi (toi da 10):")
    for i, msg, stmt in errors[:10]:
        print(f"  Statement #{i}: {msg}")
        print(f"    SQL: {stmt}...")
print("\nXong. Mo lai Tu van PCCC -> tab Bao gia se thay SP moi.")
