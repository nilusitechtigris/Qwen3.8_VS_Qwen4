"""STRUCTURED OUTPUT & SQL: 6 tasks (JSON extraction, CSV, regex writing, aggregation, SQLite queries)."""
from __future__ import annotations

import json
import random
import sqlite3
from collections import defaultdict

from util import T

C = "structured"


def chk(name, **params):
    return {"type": "checker", "name": name, "params": params}


EMAIL = """From: Omar Haddad
Subject: reimbursement

Hi team,
please reimburse Lena Fischer for the conference hotel in Porto. The invoice is dated 7 March 2026 and the total
is EUR 1,284.50 (VAT included). Her previous claim from 12 February (EUR 310.00) was already paid, so please
ignore it.
Thanks, Omar"""

TABLE = """| City      | Country  | Population (2025) |
|-----------|----------|------------------:|
| Varnholm  | Nordia   | 1,204,330*        |
| Ostrava Nova | Kelvar | 845,002         |
|Tirlen|Nordia|2,010,447|
| Quessa    | Mareth   | 98,450            |
| Brindmoor | Kelvar   | 1,204,331         |
| Lunett    | Mareth   |   12,999 (est.)   |
* provisional"""
TABLE_ROWS = [["city", "country", "population"], ["Tirlen", "Nordia", "2010447"], ["Brindmoor", "Kelvar", "1204331"],
              ["Varnholm", "Nordia", "1204330"], ["Ostrava Nova", "Kelvar", "845002"], ["Quessa", "Mareth", "98450"],
              ["Lunett", "Mareth", "12999"]]

IPV4_POS = ["0.0.0.0", "255.255.255.255", "192.168.1.1", "10.0.0.254", "1.2.3.4", "249.250.199.100", "100.10.0.1",
            "200.99.9.0", "172.16.254.1", "8.8.8.8"]
IPV4_NEG = ["256.1.1.1", "01.2.3.4", "1.2.3", "1.2.3.4.5", "1.2.3.04", "1..3.4", "a.b.c.d", "1.2.3.4 ", " 1.2.3.4",
            "300.300.300.300", "1.2.3.-1", "255.255.255.256", "00.0.0.0", "1.2.3.4\n", "999.0.0.1", "25a.1.1.1",
            "1.2.3.260", "1.2.3.", ".1.2.3", "1,2,3,4", "１.2.3.4", "260.0.0.0", "1.2.3.4/24", "0x1.2.3.4"]


def employees():
    rng = random.Random(1234)
    first = ["Ada", "Bora", "Chen", "Dara", "Eli", "Femi", "Gul", "Hana", "Ivo", "Jin", "Kemal", "Lior", "Mina", "Noor",
             "Oleg", "Pia", "Quinn", "Rosa", "Sami", "Tara"]
    depts = ["Finance", "Legal", "Ops", "Research", "Sales"]
    out = []
    for i in range(40):
        out.append({"name": f"{first[i % 20]} {chr(65 + i // 20)}.", "dept": rng.choice(depts),
                    "salary": rng.randrange(41000, 128000, 50)})
    return out


SQL_SETUP_EMP = None  # built in tasks()


def build_emp_sql():
    rng = random.Random(77)
    rows = []
    depts = ["Audit", "Design", "Field", "Kitchen", "Lab", "Press"]
    salaries = {"Audit": [70000, 70000, 64000, 64000, 51000], "Design": [88000, 72000, 72000, 60000],
                "Field": [45000], "Kitchen": [39000, 39000], "Lab": [99000, 95000, 95000, 95000, 81000],
                "Press": [52000, 61000, 58000, 61000, 47000, 58000]}
    names = iter(["Abel", "Bea", "Cyd", "Dov", "Eda", "Fyn", "Gia", "Hal", "Ida", "Jon", "Kai", "Lev", "Mo", "Nia",
                  "Oz", "Pam", "Rex", "Sol", "Tia", "Uma", "Val", "Wes", "Xia", "Yul"])
    i = 0
    for d in depts:
        for s in salaries[d]:
            i += 1
            rows.append((i, next(names), d, s, f"20{rng.randint(10, 25)}-{rng.randint(1, 12):02d}-01"))
    setup = ("CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, dept TEXT, salary INTEGER, hired TEXT);\n" +
             "\n".join(f"INSERT INTO employees VALUES ({a}, '{b}', '{c}', {d}, '{e}');" for a, b, c, d, e in rows))
    # expected via python
    exp = []
    by = defaultdict(list)
    for r in rows:
        by[r[2]].append(r)
    for d in sorted(by):
        distinct = sorted({r[3] for r in by[d]}, reverse=True)
        if len(distinct) >= 2:
            for r in sorted(by[d], key=lambda r: r[1]):
                if r[3] == distinct[1]:
                    exp.append((d, r[1], r[3]))
    exp.sort(key=lambda t: (t[0], t[1]))
    ref = ("WITH r AS (SELECT dept, name, salary, DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC) AS rk "
           "FROM employees) SELECT dept, name, salary FROM r WHERE rk = 2 ORDER BY dept, name")
    con = sqlite3.connect(":memory:")
    con.executescript(setup)
    assert [tuple(x) for x in con.execute(ref).fetchall()] == exp
    return setup, exp, ref


def build_bom_sql():
    parts = [(1, "Bike", 0.0), (2, "Frame", 0.0), (3, "Wheel", 0.0), (4, "Tube", 12.5), (5, "Spoke", 0.35),
             (6, "Rim", 22.0), (7, "Hub", 18.75), (8, "Bolt", 0.2), (9, "Scooter", 0.0), (10, "Deck", 31.0),
             (11, "Handlebar", 0.0), (12, "Grip", 3.1), (13, "Bar", 14.0), (14, "Trike", 0.0), (15, "Seat", 27.9)]
    bom = [(1, 2, 1), (1, 3, 2), (1, 11, 1), (1, 15, 1), (2, 4, 6), (2, 8, 12), (3, 5, 32), (3, 6, 1), (3, 7, 1),
           (3, 8, 4), (11, 12, 2), (11, 13, 1), (11, 8, 3), (9, 10, 1), (9, 3, 2), (9, 11, 1), (14, 2, 1), (14, 3, 3),
           (14, 15, 1), (14, 11, 1), (7, 8, 6)]
    setup = ("CREATE TABLE parts (id INTEGER PRIMARY KEY, name TEXT, unit_cost REAL);\n"
             "CREATE TABLE bom (parent_id INTEGER, child_id INTEGER, qty INTEGER);\n" +
             "\n".join(f"INSERT INTO parts VALUES ({a}, '{b}', {c});" for a, b, c in parts) + "\n" +
             "\n".join(f"INSERT INTO bom VALUES ({a}, {b}, {c});" for a, b, c in bom))
    children = defaultdict(list)
    for p, c, q in bom:
        children[p].append((c, q))
    cost = {a: c for a, _, c in parts}
    name = {a: b for a, b, _ in parts}

    def leaf_cost(pid):
        if not children[pid]:
            return cost[pid]
        return sum(q * leaf_cost(c) for c, q in children[pid])

    tops = sorted({p for p, _, _ in bom} - {c for _, c, _ in bom}, key=lambda p: name[p])
    exp = [(name[t], round(leaf_cost(t), 2)) for t in tops]
    ref = ("WITH RECURSIVE x(top, part, mult) AS ("
           " SELECT p.id, p.id, 1.0 FROM parts p WHERE p.id IN (SELECT parent_id FROM bom) AND p.id NOT IN "
           "(SELECT child_id FROM bom)"
           " UNION ALL SELECT x.top, b.child_id, x.mult * b.qty FROM x JOIN bom b ON b.parent_id = x.part)"
           " SELECT t.name, ROUND(SUM(x.mult * p.unit_cost), 2) FROM x JOIN parts p ON p.id = x.part"
           " JOIN parts t ON t.id = x.top WHERE x.part NOT IN (SELECT parent_id FROM bom)"
           " GROUP BY t.name ORDER BY t.name")
    con = sqlite3.connect(":memory:")
    con.executescript(setup)
    got = [(a, round(b, 2)) for a, b in con.execute(ref).fetchall()]
    assert got == exp, (got, exp)
    return setup, exp, ref


def sql_ref(q):
    return "```sql\n" + q + "\n```"


def tasks():
    out = []
    expected = {"name": "Lena Fischer", "date": "2026-03-07", "amount": 1284.5, "currency": "EUR"}
    out.append(T("STRUCT-01", C, 1, "Extract fields from an email",
                 "Extract the reimbursement that is being requested in the email below as a JSON object with exactly "
                 "these keys: \"name\" (person to reimburse), \"date\" (invoice date, YYYY-MM-DD), \"amount\" (a JSON "
                 "number) and \"currency\" (ISO 4217 code). Output only the JSON object.\n\n" + EMAIL,
                 chk("email_json", expected=expected), 0.95, json.dumps(expected), mode="raw",
                 wrong=json.dumps({**expected, "amount": 310.0, "date": "2026-02-12"})))
    out.append(T("STRUCT-02", C, 2, "Messy table to clean CSV",
                 "Convert the table below to CSV with the header line `city,country,population`. Population must be a "
                 "plain integer (no separators, footnote marks or notes). Sort the rows by population, largest first. "
                 "Output only the CSV lines (no code fence needed).\n\n" + TABLE,
                 chk("csv_exact", expected_rows=TABLE_ROWS), 0.85, "\n".join(",".join(r) for r in TABLE_ROWS),
                 mode="raw", wrong="\n".join(",".join(r) for r in [TABLE_ROWS[0]] + TABLE_ROWS[1:][::-1])))
    ref_rx = r"(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])"
    out.append(T("STRUCT-03", C, 3, "Write a strict IPv4 regex",
                 "Write a Python regular expression that, when used with re.fullmatch (no flags), matches exactly the "
                 "IPv4 addresses in dotted-decimal form: four decimal octets 0-255 separated by single dots, using "
                 "only ASCII digits, with no leading zeros (\"0\" itself is fine, \"01\" is not), and nothing else - "
                 "no whitespace, no trailing newline. Put the regex, wrapped in backticks, on the FINAL ANSWER line.",
                 chk("regex_tester", positives=IPV4_POS, negatives=IPV4_NEG), 0.60, f"FINAL ANSWER: `{ref_rx}`",
                 wrong=r"FINAL ANSWER: `(\d{1,3}\.){3}\d{1,3}`"))
    emps = employees()
    by = defaultdict(list)
    for e in emps:
        by[e["dept"]].append(e["salary"])
    avg = {d: round(sum(v) / len(v), 2) for d, v in sorted(by.items())}
    out.append(T("STRUCT-04", C, 3, "Group-by average from JSON",
                 "Here is a JSON array of employee records:\n\n" + json.dumps(emps) + "\n\nReturn a JSON object that "
                 "maps each department name to the average salary of that department, rounded to 2 decimal places, "
                 "with the keys sorted alphabetically. Output only the JSON object.",
                 chk("json_object_exact", expected=avg, tol=0.006), 0.45, json.dumps(avg), mode="raw",
                 wrong=json.dumps({k: round(v + 1, 2) for k, v in avg.items()})))
    setup, exp, ref = build_emp_sql()
    out.append(T("STRUCT-05", C, 3, "SQL: second-highest salary per department",
                 "SQLite database:\n\n```sql\n" + setup + "\n```\n\nWrite ONE SQLite query that returns, for every "
                 "department, the employee(s) whose salary equals the second-highest DISTINCT salary in that "
                 "department (departments with fewer than two distinct salaries produce no rows; ties produce several "
                 "rows). Columns: dept, name, salary. Order by dept, then name. Return only the query in a ```sql "
                 "code block.",
                 {"type": "sql", "setup_sql": setup, "expected_rows": exp, "ordered": True}, 0.60, sql_ref(ref),
                 mode="sql",
                 wrong=sql_ref("SELECT dept, name, MAX(salary) FROM employees GROUP BY dept ORDER BY dept")))
    setup, exp, ref = build_bom_sql()
    out.append(T("STRUCT-06", C, 4, "SQL: recursive bill of materials",
                 "SQLite database with a bill of materials (bom.qty = how many child parts one parent part needs):\n\n"
                 "```sql\n" + setup + "\n```\n\nA part is a leaf if it has no children in bom; only leaves have a "
                 "meaningful unit_cost. A top-level product is a part that has children but is never a child itself. "
                 "Write ONE SQLite query that returns, for every top-level product, its name and the total cost of "
                 "all leaf parts needed to build one unit of it (multiplying quantities along every path), rounded to "
                 "2 decimals. Columns: name, total_cost. Order by name. Return only the query in a ```sql code block.",
                 {"type": "sql", "setup_sql": setup, "expected_rows": exp, "ordered": True, "round": 2}, 0.45,
                 sql_ref(ref), mode="sql",
                 wrong=sql_ref("SELECT p.name, SUM(c.unit_cost * b.qty) FROM parts p JOIN bom b ON b.parent_id = p.id "
                               "JOIN parts c ON c.id = b.child_id GROUP BY p.name ORDER BY p.name")))
    return out


if __name__ == "__main__":
    for t in tasks():
        print(t["id"], t["tier"], t["grader"].get("expected_rows") or t["grader"].get("params", {}).get("expected"))
