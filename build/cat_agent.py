"""AGENT: 8 multi-turn tool-use tasks run against deterministic simulated environments (bench/envs.py)."""
from __future__ import annotations

import json
import random
import sys
from datetime import datetime
from itertools import permutations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bench.envs import PROTOCOL, bfs_dist, bfs_path  # noqa: E402

from util import T, exact, num  # noqa: E402

C = "agent"


def call(tool, **args):
    return "CALL " + json.dumps({"tool": tool, "args": args})


def prompt(tools: str, task: str) -> str:
    return f"{PROTOCOL}\n\nTools:\n{tools.strip()}\n\nTask:\n{task.strip()}"


def agent_grader(env, config, *, answer=None, state_check=None, max_turns=20, required_tools=()):
    return {"type": "agent", "env": env, "config": config, "answer": answer, "state_check": state_check,
            "max_turns": max_turns, "required_tools": list(required_tools)}


def ref(script):
    return {"script": script}


# ------------------------------------------------------------------------------------------- data
def files_config():
    rng = random.Random(9)
    files = {}
    ports = {"gateway": 8080, "search": 8444, "notifier": 9443, "reports": 8433, "ledger": 8443, "auth": 8442,
             "media": 18443, "inventory": 8843}
    for svc, port in ports.items():
        files[f"/srv/apps/{svc}/conf/app.yaml"] = (f"name: {svc}\nreplicas: {rng.randint(1, 6)}\nlisten:\n"
                                                   f"  host: 0.0.0.0\n  port: {port}\nlog_level: info\n")
        files[f"/srv/apps/{svc}/README.md"] = f"# {svc}\nOwned by the {rng.choice(['core', 'platform', 'money'])} team.\n"
    files["/srv/apps/legacy-gateway/README.md"] = ("# legacy-gateway\nThis service used to listen on port 8443 before "
                                                   "it was decommissioned in 2025. Its configuration was removed.\n")
    files["/srv/apps/ledger/conf/defaults.yaml"] = "retry: 3\ntimeout_s: 30\n"
    files["/srv/apps/search/conf/tls.yaml"] = "cert: /etc/ssl/search.pem\n# formerly served TLS on 8443\n"
    files["/etc/motd"] = "Welcome. Deployed services live under /srv/apps/<service>/conf/app.yaml\n"
    files["/var/log/deploy.log"] = "2026-11-02 deployed ledger v4.2\n2026-11-03 deployed search v9.0\n"
    return {"files": files}, "ledger"


def orders_config():
    customers = [{"id": "C-204", "name": "Mara Ilić"}, {"id": "C-731", "name": "Marta Ilić"},
                 {"id": "C-118", "name": "Jonas Berg"}]
    orders = [
        {"order_id": "O-9001", "customer_id": "C-204", "status": "delivered", "date": "2026-09-12",
         "items": [{"sku": "SKU-A", "qty": 2, "unit_price": 19.99}, {"sku": "SKU-B", "qty": 1, "unit_price": 149.00}]},
        {"order_id": "O-9002", "customer_id": "C-204", "status": "cancelled", "date": "2026-09-30",
         "items": [{"sku": "SKU-Z", "qty": 1, "unit_price": 999.00}]},
        {"order_id": "O-9003", "customer_id": "C-204", "status": "delivered", "date": "2026-10-08",
         "items": [{"sku": "SKU-C", "qty": 3, "unit_price": 7.50}, {"sku": "SKU-D", "qty": 1, "unit_price": 64.25}]},
        {"order_id": "O-9004", "customer_id": "C-204", "status": "shipped", "date": "2026-11-01",
         "items": [{"sku": "SKU-E", "qty": 1, "unit_price": 300.00}]},
        {"order_id": "O-9100", "customer_id": "C-731", "status": "delivered", "date": "2026-10-02",
         "items": [{"sku": "SKU-A", "qty": 5, "unit_price": 19.99}]},
    ]
    total = round(sum(i["qty"] * i["unit_price"] for o in orders if o["customer_id"] == "C-204"
                      and o["status"] == "delivered" for i in o["items"]), 2)
    return {"customers": customers, "orders": orders}, total


def flights_config():
    D = "2026-12-03"
    F = lambda no, a, b, dep, arr, price: {"flight": no, "from": a, "to": b, "dep": dep, "arr": arr, "price_eur": price}
    d, n = "2026-12-03T", "2026-12-04T"
    flights = [
        F("TK79", "IST", "SFO", d + "10:00Z", d + "23:55Z", 1480),
        F("TK1591", "IST", "FRA", d + "06:30Z", d + "09:35Z", 210), F("LH1305", "IST", "FRA", d + "12:10Z", d + "15:05Z", 180),
        F("LH454", "FRA", "SFO", d + "10:05Z", d + "21:45Z", 690), F("LH458", "FRA", "SFO", d + "13:20Z", n + "01:00Z", 610),
        F("LH460", "FRA", "SFO", d + "16:30Z", n + "04:10Z", 655),
        F("TK1979", "IST", "LHR", d + "07:00Z", d + "10:10Z", 195), F("BA675", "IST", "LHR", d + "13:00Z", d + "16:05Z", 240),
        F("BA285", "LHR", "SFO", d + "11:05Z", d + "22:30Z", 590), F("BA287", "LHR", "SFO", d + "15:30Z", n + "03:00Z", 560),
        F("VS19", "LHR", "SFO", d + "17:20Z", n + "05:10Z", 545),
        F("TK1951", "IST", "AMS", d + "05:50Z", d + "09:05Z", 170), F("KL1610", "IST", "AMS", d + "11:00Z", d + "14:10Z", 230),
        F("KL605", "AMS", "SFO", d + "10:00Z", d + "21:40Z", 620), F("KL607", "AMS", "SFO", d + "14:50Z", n + "02:30Z", 540),
        F("KL641", "AMS", "JFK", d + "10:30Z", d + "18:40Z", 150),
        F("TK1", "IST", "JFK", d + "09:00Z", d + "20:30Z", 450),
        F("B6915", "JFK", "SFO", d + "21:45Z", n + "03:50Z", 190), F("AA177", "JFK", "SFO", n + "07:00Z", n + "13:30Z", 120),
        F("QR240", "IST", "DOH", d + "01:00Z", d + "05:15Z", 160), F("QR737", "DOH", "SFO", d + "08:00Z", n + "00:30Z", 610),
    ]
    deadline = datetime.fromisoformat("2026-12-04T06:00+00:00")
    ts = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
    best = None
    for f in flights:
        if f["from"] == "IST" and f["to"] == "SFO" and ts(f["arr"]) <= deadline:
            cand = (f["price_eur"], [f["flight"]])
            best = min(best, cand) if best else cand
    for f1 in flights:
        for f2 in flights:
            if f1["from"] == "IST" and f1["to"] == f2["from"] and f2["to"] == "SFO" and f1["to"] != "SFO":
                if (ts(f2["dep"]) - ts(f1["arr"])).total_seconds() >= 3600 and ts(f2["arr"]) <= deadline:
                    cand = (f1["price_eur"] + f2["price_eur"], [f1["flight"], f2["flight"]])
                    best = min(best, cand) if best else cand
    return {"date": D, "flights": flights}, best


REPO_FILES = {
    "shop/__init__.py": "",
    "shop/pagination.py": '''def paginate(items, page, page_size):
    """Return the items on the 1-indexed page `page`."""
    if page < 1 or page_size < 1:
        raise ValueError("page and page_size must be positive")
    start = (page - 1) * page_size
    end = start + page_size - 1
    return items[start:end]
''',
    "shop/cart.py": '''from shop.pagination import paginate
from shop.pricing import line_total

PAGE_SIZE = 4


class Cart:
    def __init__(self):
        self.items = []

    def add(self, sku, qty, unit_price):
        self.items.append((sku, qty, unit_price))

    def total(self):
        return round(sum(line_total(q, p) for _, q, p in self.items), 2)

    def page_items(self, page_number):
        # page_number is 1-indexed, as shown in the UI
        return paginate(self.items, page_number, PAGE_SIZE)
''',
    "shop/pricing.py": '''def line_total(qty, unit_price):
    # TODO: switch to Decimal before multi-currency launch
    return qty * unit_price


def apply_discount(amount, percent):
    if not 0 <= percent <= 100:
        raise ValueError("percent out of range")
    return round(amount * (100 - percent) / 100, 2)
''',
    "tests/test_cart.py": '''from shop.cart import Cart


def make_cart(n):
    c = Cart()
    for i in range(n):
        c.add(f"SKU-{i}", 1, 2.5)
    return c


def test_total():
    assert make_cart(3).total() == 7.5


def test_first_page_full():
    assert len(make_cart(10).page_items(1)) == 4


def test_last_page_partial():
    assert len(make_cart(10).page_items(3)) == 2
''',
    "tests/test_pricing.py": '''from shop.pricing import apply_discount


def test_discount():
    assert apply_discount(200, 15) == 170.0
''',
}

REPO_TEST_OUTPUT = """============================= test session starts ==============================
collected 4 items

tests/test_cart.py .FF                                                   [ 75%]
tests/test_pricing.py .                                                  [100%]

=================================== FAILURES ===================================
____________________________ test_first_page_full _____________________________
    def test_first_page_full():
>       assert len(make_cart(10).page_items(1)) == 4
E       assert 3 == 4
___________________________ test_last_page_partial ____________________________
    def test_last_page_partial():
>       assert len(make_cart(10).page_items(3)) == 2
E       assert 1 == 2
========================= 2 failed, 2 passed in 0.04s =========================="""


def tickets_config():
    rng = random.Random(66)
    tickets = []
    for i in range(57):
        tickets.append({
            "id": f"TCK-{1001 + i}",
            "status": rng.choices(["open", "closed", "pending"], [45, 40, 15])[0],
            "priority": rng.choices(["low", "medium", "high", "urgent"], [25, 35, 30, 10])[0],
            "team": rng.choice(["payments", "core", "mobile", "infra"]),
            "created": f"2026-{rng.choice([9, 10, 10, 11]):02d}-{rng.randint(1, 28):02d}",
        })
    for i in (4, 13, 27, 35, 48, 56):  # planted matches, spread over pages (incl. the last one)
        tickets[i].update(status="open", priority="high", team="payments", created=f"2026-10-{rng.randint(1, 28):02d}")
    near = [("status", "pending"), ("priority", "urgent"), ("team", "core"), ("created", "2026-09-30"),
            ("created", "2026-11-01"), ("priority", "medium")]
    for i, (k, v) in zip((7, 19, 22, 31, 44, 52), near):  # near misses: match on everything but one field
        tickets[i].update(status="open", priority="high", team="payments", created="2026-10-15")
        tickets[i][k] = v
    match = lambda t: (t["status"] == "open" and t["priority"] == "high" and t["team"] == "payments"
                       and t["created"].startswith("2026-10"))
    count = sum(map(match, tickets))
    first_page = sum(map(match, tickets[:10]))
    later = sum(map(match, tickets[40:]))
    assert count >= 4 and first_page < count and later >= 1, (count, first_page, later)
    tokens = ["".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(12)) for _ in range(6)]
    return {"tickets": tickets, "page_size": 10, "tokens": tokens}, count


def stock_config():
    stock = {
        "A1": {"cached": 40, "live": 40, "stale": False, "as_of": "2026-11-16T08:00Z"},
        "B7": {"cached": 12, "live": 3, "stale": True, "as_of": "2026-11-09T17:20Z"},
        "C3": {"cached": 0, "live": 25, "stale": True, "as_of": "2026-11-02T09:45Z"},
        "D9": {"cached": 18, "live": 18, "stale": False, "as_of": "2026-11-16T07:55Z"},
        "E2": {"cached": 7, "live": 9, "stale": True, "as_of": "2026-11-12T12:00Z"},
    }
    return {"stock": stock}, sum(s["live"] for s in stock.values())


ROBOT_GRID = [
    "###########",
    "#S..#.....#",
    "#.#.#.###.#",
    "#.#...#...#",
    "#.#####.#.#",
    "#...#...#.#",
    "#.#.#.#.#.#",
    "#.#...#...#",
    "###########",
]


def robot_config():
    grid = ROBOT_GRID
    start = (1, 1)
    packages = [{"id": "P1", "pickup": [7, 1], "dest": [1, 9]},
                {"id": "P2", "pickup": [3, 5], "dest": [7, 9]},
                {"id": "P3", "pickup": [1, 3], "dest": [5, 5]}]
    costs = {}
    for order in permutations(range(3)):
        pos, cost = start, 0
        for k in order:
            p = packages[k]
            cost += bfs_dist(grid, pos, p["pickup"]) + bfs_dist(grid, p["pickup"], p["dest"])
            pos = tuple(p["dest"])
        costs[order] = cost
    best_order = min(costs, key=costs.get)
    budget = costs[best_order] + 2
    assert costs[(0, 1, 2)] > budget, costs  # delivering in the listed order is not good enough
    assert sum(c <= budget for c in costs.values()) <= 2, costs
    return {"grid": grid, "start": list(start), "packages": packages, "budget": budget}, best_order, costs


# ------------------------------------------------------------------------------------------- tasks
def tasks():
    out = []
    # AGENT-01 ------------------------------------------------------------------------------
    a, b, c = 123456789, 987654321, 1111111111
    ans = a * b + c
    out.append(T("AGENT-01", C, 1, "Calculator tools",
                 prompt('- multiply(a: int, b: int) -> {"result": int}\n- add(a: int, b: int) -> {"result": int}',
                        f"Compute {a} * {b} + {c} exactly. Give the integer as the final answer."),
                 agent_grader("calc", {}, answer=num(ans, exact=True), max_turns=8), 0.95,
                 ref([call("multiply", a=a, b=b), call("add", a=a * b, b=c), f"FINAL ANSWER: {ans}"]), mode="agent",
                 wrong=ref([f"FINAL ANSWER: {ans + 10}"])))
    # AGENT-02 ------------------------------------------------------------------------------
    cfg, svc = files_config()
    out.append(T("AGENT-02", C, 2, "Find a config in a file tree",
                 prompt('- list_dir(path: str) -> {"entries": [...]}  (directories end with "/")\n'
                        '- read_file(path: str) -> {"content": str}',
                        "Exactly one currently deployed service is configured, in its conf/app.yaml file, to listen "
                        "on port 8443. Find it. The final answer is the service's directory name."),
                 agent_grader("files", cfg, answer=exact(svc), max_turns=25, required_tools=["read_file"]), 0.85,
                 ref([call("list_dir", path="/srv/apps"), call("read_file", path=f"/srv/apps/{svc}/conf/app.yaml"),
                      f"FINAL ANSWER: {svc}"]), mode="agent",
                 wrong=ref(["FINAL ANSWER: legacy-gateway"])))
    # AGENT-03 ------------------------------------------------------------------------------
    cfg, total = orders_config()
    out.append(T("AGENT-03", C, 2, "Order lookup and aggregation",
                 prompt('- find_customer(name: str) -> {"customer_id": str}\n'
                        '- list_orders(customer_id: str) -> {"orders": [{"order_id", "status", "date"}]}\n'
                        '- get_order(order_id: str) -> {"items": [{"sku", "qty", "unit_price"}], "currency": "EUR"}',
                        "What is the total value in EUR (sum of qty * unit_price over all items) of all orders with "
                        "status 'delivered' for the customer named \"Mara Ilić\"? Give the number with two decimals."),
                 agent_grader("orders", cfg, answer=num(f"{total:.2f}", abs_tol=0.005), max_turns=15,
                              required_tools=["get_order"]), 0.85,
                 ref([call("find_customer", name="Mara Ilić"), call("list_orders", customer_id="C-204"),
                      call("get_order", order_id="O-9001"), call("get_order", order_id="O-9003"),
                      f"FINAL ANSWER: {total:.2f}"]), mode="agent", wrong=ref(["FINAL ANSWER: 575.73"])))
    # AGENT-04 ------------------------------------------------------------------------------
    cfg, best = flights_config()
    price, legs = best
    assert legs == ["TK1", "B6915"], best
    out.append(T("AGENT-04", C, 3, "Constrained flight search",
                 prompt('- search_flights(origin: str, destination: str, date: str) -> {"flights": [...]}  '
                        '(IATA codes, date as YYYY-MM-DD; all times in the results are UTC)',
                        "Find the cheapest way to fly from IST to SFO departing on 2026-12-03, subject to: at most "
                        "one connection (so either a direct flight, or two flights via one connection airport); at a "
                        "connection, the second flight must depart at least 60 minutes after the first one arrives; "
                        "the final arrival in SFO must be no later than 2026-12-04 06:00 UTC. Prices are per flight "
                        "and simply add up. Possible connection airports: FRA, LHR, AMS, JFK, DOH. The final answer is "
                        "the flight number(s) of the cheapest valid itinerary in travel order, comma-separated."),
                 agent_grader("flights", cfg, answer={"type": "sequence", "items": legs}, max_turns=25,
                              required_tools=["search_flights"]), 0.55,
                 ref([call("search_flights", origin="IST", destination="JFK", date="2026-12-03"),
                      call("search_flights", origin="JFK", destination="SFO", date="2026-12-03"),
                      f"FINAL ANSWER: {', '.join(legs)}"]), mode="agent", wrong=ref(["FINAL ANSWER: TK1, AA177"])))
    # AGENT-05 ------------------------------------------------------------------------------
    cfg = {"files": REPO_FILES, "test_output": REPO_TEST_OUTPUT}
    out.append(T("AGENT-05", C, 3, "Locate a bug from failing tests",
                 prompt('- list_files() -> {"files": [...]}\n'
                        '- read_file(path: str) -> {"content": str}  (each line is prefixed with its line number)\n'
                        '- run_tests() -> {"output": str}',
                        "The test suite of this small repository is failing. Find the single line of code that "
                        "causes the failures. The final answer is the file path and the line number in the form "
                        "path:line (for example pkg/module.py:12)."),
                 agent_grader("repo", cfg, answer={"type": "regex", "pattern": r"`?shop/pagination\.py\s*:\s*6`?"},
                              max_turns=15), 0.60,
                 ref([call("run_tests"), call("read_file", path="shop/cart.py"),
                      call("read_file", path="shop/pagination.py"), "FINAL ANSWER: shop/pagination.py:6"]),
                 mode="agent", wrong=ref(["FINAL ANSWER: shop/cart.py:20"])))
    # AGENT-06 ------------------------------------------------------------------------------
    cfg, count = tickets_config()
    script = [call("list_tickets")] + [call("list_tickets", page_token=t) for t in cfg["tokens"][:5]] + \
             [f"FINAL ANSWER: {count}"]
    out.append(T("AGENT-06", C, 4, "Paginated API aggregation",
                 prompt('- list_tickets(page_token: str | null) -> {"tickets": [...], "next_page_token": str | null}\n'
                        '  Returns one page of tickets. Pass the returned next_page_token to get the following page; '
                        'it is null on the last page.',
                        "How many tickets are currently open (status 'open'), have priority 'high' (exactly 'high', "
                        "not 'urgent'), belong to team 'payments', and were created in October 2026? Consider every "
                        "ticket in the system."),
                 agent_grader("tickets", cfg, answer=num(count, exact=True), max_turns=15), 0.55,
                 ref(script), mode="agent", wrong=ref([f"FINAL ANSWER: {count - 1}"])))
    # AGENT-07 ------------------------------------------------------------------------------
    cfg, live_total = stock_config()
    skus = list(cfg["stock"])
    script = [call("get_stock", sku=s) for s in skus] + \
             [call("refresh_stock", sku=s) for s in skus if cfg["stock"][s]["stale"]] + [f"FINAL ANSWER: {live_total}"]
    out.append(T("AGENT-07", C, 4, "Stale cache awareness",
                 prompt('- get_stock(sku: str) -> {"qty": int, "source": "cache", "as_of": str, "stale": bool}\n'
                        '  Fast, but served from a cache. When "stale" is true the quantity may be outdated.\n'
                        '- refresh_stock(sku: str) -> {"qty": int, "source": "live"}\n'
                        '  Slow, always returns the current live quantity.',
                        f"What is the current total stock (sum of quantities) of SKUs {', '.join(skus)}? The answer must "
                        "reflect live quantities."),
                 agent_grader("stock", cfg, answer=num(live_total, exact=True), max_turns=20), 0.55,
                 ref(script), mode="agent",
                 wrong=ref([f"FINAL ANSWER: {sum(s['cached'] for s in cfg['stock'].values())}"])))
    # AGENT-08 ------------------------------------------------------------------------------
    cfg, order, costs = robot_config()
    script = [call("look")]
    pos = tuple(cfg["start"])
    for k in order:
        p = cfg["packages"][k]
        script += [call("move", path=bfs_path(cfg["grid"], pos, p["pickup"])), call("pick"),
                   call("move", path=bfs_path(cfg["grid"], p["pickup"], p["dest"])), call("drop")]
        pos = tuple(p["dest"])
    script.append("FINAL ANSWER: DONE")
    grid_txt = "\n".join(cfg["grid"])
    out.append(T("AGENT-08", C, 5, "Delivery robot under a step budget",
                 prompt('- look() -> robot position, carried package, package locations/destinations, steps used, map\n'
                        '- move(path: str) -> executes a string of moves such as "NNEES" one step at a time '
                        '(N = row-1, S = row+1, E = column+1, W = column-1). Every attempted step costs 1 from the step '
                        'budget, including a step into a wall, which stops the rest of the path.\n'
                        '- pick() -> picks up the package on the current cell (the robot carries at most one)\n'
                        '- drop() -> drops the carried package; it is delivered if this cell is its destination',
                        "A robot on the grid below must deliver all three packages (P1, P2, P3) to their destinations "
                        f"using at most {cfg['budget']} steps in total. Positions are [row, column], 0-indexed, '#' is a "
                        f"wall, and the robot starts at {cfg['start']}.\n\n{grid_txt}\n\n" +
                        "\n".join(f"- {p['id']}: pick up at {p['pickup']}, deliver to {p['dest']}" for p in cfg['packages']) +
                        "\n\nWhen all three packages are delivered, reply with FINAL ANSWER: DONE. The task is graded on "
                        "the final state of the world."),
                 agent_grader("robot", cfg, state_check={}, max_turns=30), 0.20,
                 ref(script), mode="agent", wrong=ref(["FINAL ANSWER: DONE"]),
                 notes=f"optimal order {order}, all order costs {sorted(costs.values())}"))
    return out


if __name__ == "__main__":
    for t in tasks():
        print(t["id"], t["tier"], t["grader"]["env"], (t["grader"].get("answer") or {}).get("value") or
              (t["grader"].get("answer") or {}).get("items") or (t["grader"].get("answer") or {}).get("answers"),
              t["notes"])
