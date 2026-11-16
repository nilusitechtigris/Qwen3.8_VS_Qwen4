"""LONG CONTEXT: 8 synthetic documents (seeded) with answers computed from the generated data."""
from __future__ import annotations

import heapq
import random
from datetime import datetime, timedelta

from util import T, exact, fa, num

C = "long_context"

TEAMS = ["platform", "billing", "search", "mobile", "data", "security", "growth", "infra", "payments", "support"]
ADJ = ["legacy", "new", "flaky", "critical", "experimental", "shared", "internal", "public", "slow", "patched"]
NOUN = ["dashboard", "pipeline", "cache layer", "release train", "API gateway", "test suite", "migration plan",
        "rollout", "alerting rule", "runbook", "schema", "load balancer", "feature flag", "batch job", "SDK"]
VERB = ["review", "simplify", "document", "benchmark", "deprecate", "refactor", "monitor", "audit", "split", "pin"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
PEOPLE = ["Aylin", "Marek", "Sofia", "Tunde", "Keiko", "Ravi", "Lena", "Omar", "Ines", "Piotr", "Mei", "Jonas"]


def filler_sentence(rng):
    t = rng.randrange(6)
    if t == 0:
        return (f"The {rng.choice(TEAMS)} team reviewed the {rng.choice(ADJ)} {rng.choice(NOUN)} and agreed to "
                f"{rng.choice(VERB)} it before {rng.choice(DAYS)}.")
    if t == 1:
        return (f"{rng.choice(PEOPLE)} noted that the {rng.choice(NOUN)} still depends on the {rng.choice(ADJ)} "
                f"{rng.choice(NOUN)}, so nobody should {rng.choice(VERB)} either one in isolation.")
    if t == 2:
        return (f"A follow-up about the {rng.choice(NOUN)} was scheduled with {rng.choice(PEOPLE)} and "
                f"{rng.choice(PEOPLE)} for {rng.choice(DAYS)} afternoon.")
    if t == 3:
        return (f"Latency on the {rng.choice(NOUN)} moved from {rng.randint(80, 400)} ms to {rng.randint(80, 400)} ms "
                f"after the {rng.choice(TEAMS)} change, which the group considered {rng.choice(['acceptable', 'worrying', 'noise', 'a regression'])}.")
    if t == 4:
        return (f"There was a short discussion on whether to {rng.choice(VERB)} the {rng.choice(ADJ)} "
                f"{rng.choice(NOUN)}; the decision was postponed.")
    return (f"{rng.choice(PEOPLE)} will share notes on the {rng.choice(NOUN)} in the {rng.choice(TEAMS)} channel.")


def filler_paragraph(rng, n_sent):
    return " ".join(filler_sentence(rng) for _ in range(n_sent))


def wc(s):
    return len(s.split())


# ---------------------------------------------------------------------------------------------- LC01
def lc01():
    rng = random.Random(101)
    hosts = [f"web-{i:02d}" for i in range(1, 25)]
    t = datetime(2026, 3, 14, 6, 0, 0)
    lines = []
    target_line = rng.randrange(250, 450)
    decoy_lines = set(rng.sample(range(50, 650), 7))
    answer = "37h"
    for i in range(700):
        t += timedelta(seconds=rng.randint(1, 40))
        h = rng.choice(hosts)
        if i == target_line:
            lines.append(f"{t:%Y-%m-%dT%H:%M:%SZ} host=web-12 svc=vault level=INFO msg=\"config set\" "
                         f"key=vault.rotation.window value={answer}")
            continue
        if i in decoy_lines:
            dh = rng.choice([x for x in hosts if x not in ("web-12",)])
            lines.append(f"{t:%Y-%m-%dT%H:%M:%SZ} host={dh} svc=vault level=INFO msg=\"config set\" "
                         f"key=vault.rotation.window value={rng.choice([12, 24, 36, 48, 72, 30])}h")
            continue
        svc = rng.choice(["auth", "api", "worker", "vault", "cron", "edge"])
        lvl = rng.choices(["INFO", "WARN", "ERROR", "DEBUG"], [70, 15, 5, 10])[0]
        msg = rng.choice(["request served", "cache miss", "retrying upstream", "token refreshed", "job finished",
                          "config reloaded", "slow query", "health check ok", "connection reset"])
        lines.append(f"{t:%Y-%m-%dT%H:%M:%SZ} host={h} svc={svc} level={lvl} msg=\"{msg}\" "
                     f"req={rng.getrandbits(32):08x} dur_ms={rng.randint(1, 900)}")
    doc = "\n".join(lines)
    q = ("Below is a server log.\n\n<log>\n" + doc + "\n</log>\n\nWhich value did host web-12 set for the key "
         "vault.rotation.window? Give the value exactly as written in the log.")
    return q, answer


# ---------------------------------------------------------------------------------------------- LC02
def lc02():
    rng = random.Random(202)
    frags = {k: "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(4)) for k in range(1, 7)}
    revoked = {3: "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(4)),
               5: "".join(rng.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(4))}
    paragraphs = [filler_paragraph(rng, rng.randint(4, 8)) for _ in range(120)]
    inserts = []
    for k in range(1, 7):
        if k in revoked:
            inserts.append((f"Note from the security office: recovery-code fragment #{k} is {revoked[k]}.", k, "old"))
            inserts.append((f"Correction from the security office: the earlier recovery-code fragment #{k} has been "
                            f"revoked and must not be used; the valid fragment #{k} is {frags[k]}.", k, "new"))
        else:
            inserts.append((f"Note from the security office: recovery-code fragment #{k} is {frags[k]}.", k, "only"))
    # positions: shuffled, but every correction after its revoked original
    pos = sorted(rng.sample(range(5, 118), len(inserts)))
    order = inserts[:]
    rng.shuffle(order)
    # fix order so 'old' comes before 'new' for same k
    for k in revoked:
        i_old = next(i for i, x in enumerate(order) if x[1] == k and x[2] == "old")
        i_new = next(i for i, x in enumerate(order) if x[1] == k and x[2] == "new")
        if i_old > i_new:
            order[i_old], order[i_new] = order[i_new], order[i_old]
    for p, ins in zip(pos, order):
        paragraphs[p] = paragraphs[p] + " " + ins[0]
    doc = "\n\n".join(paragraphs)
    answer = "-".join(frags[k] for k in range(1, 7))
    q = ("Below are meeting notes. Somewhere in them are fragments of a recovery code.\n\n<notes>\n" + doc +
         "\n</notes>\n\nAssemble the currently valid recovery code: give fragments #1 to #6 in numeric order, "
         "joined with hyphens (e.g. AAAA-BBBB-CCCC-DDDD-EEEE-FFFF).")
    return q, answer


# ---------------------------------------------------------------------------------------------- LC03
def lc03():
    rng = random.Random(303)
    names = set()
    while len(names) < 300:
        names.add("k_" + "".join(rng.choice("abcdefghjkmnpqrstuvwxyz") for _ in range(3)))
    names = sorted(names)
    rng.shuffle(names)
    values = {}
    lines = []
    defined = []
    chain = names[:9]  # chain[0] literal ... chain[8] target
    chain_pos = sorted(rng.sample(range(20, 280), 9))
    other = iter(names[9:])
    ci = 0
    for i in range(290):
        if ci < 9 and i == chain_pos[ci]:
            v = chain[ci]
            if ci == 0:
                values[v] = rng.randint(3, 9)
                lines.append(f"set {v} = {values[v]}")
            else:
                src = chain[ci - 1]
                op = rng.choice(["+", "-", "*"]) if ci not in (3, 6) else "*"
                k = rng.randint(2, 3) if op == "*" else rng.randint(4, 40)
                values[v] = values[src] + k if op == "+" else values[src] - k if op == "-" else values[src] * k
                lines.append(f"set {v} = {src} {op} {k}")
            defined.append(v)
            ci += 1
            continue
        v = next(other)
        if not defined or rng.random() < 0.3:
            values[v] = rng.randint(1, 99)
            lines.append(f"set {v} = {values[v]}")
        else:
            src = rng.choice(defined)
            op = rng.choice(["+", "-", "*"])
            k = rng.randint(2, 3) if op == "*" else rng.randint(1, 50)
            values[v] = values[src] + k if op == "+" else values[src] - k if op == "-" else values[src] * k
            lines.append(f"set {v} = {src} {op} {k}")
        defined.append(v)
        if rng.random() < 0.25:
            lines.append(f"# {filler_sentence(rng)}")
    target = chain[-1]
    q = ("Below is a configuration script. Each `set` line assigns an integer to a variable; variables are only "
         "read after they have been assigned, and no variable is assigned twice. Lines starting with # are "
         "comments.\n\n<script>\n" + "\n".join(lines) + f"\n</script>\n\nWhat is the final value of {target}?")
    return q, values[target]


# ---------------------------------------------------------------------------------------------- LC04
def lc04():
    rng = random.Random(404)
    rows = []
    custs = [f"C-{i:03d}" for i in range(1, 90)]
    start = datetime(2026, 1, 1)
    for i in range(420):
        d = start + timedelta(days=rng.randint(0, 150))
        c = rng.choice(custs)
        if rng.random() < 0.04:
            c = "C-017"
        if rng.random() < 0.02:
            c = "C-071"
        amt = round(rng.uniform(5, 900), 2)
        st = rng.choices(["settled", "pending", "refunded", "failed"], [70, 15, 10, 5])[0]
        rows.append((d, f"T{100000 + i}", c, amt, st))
    rows.sort()
    total = sum(r[3] for r in rows if r[2] == "C-017" and r[4] == "settled" and r[0].month == 3)
    n_match = sum(1 for r in rows if r[2] == "C-017" and r[4] == "settled" and r[0].month == 3)
    assert n_match >= 4, n_match
    csv = "date,txn_id,customer,amount_eur,status\n" + "\n".join(
        f"{d:%Y-%m-%d},{t},{c},{a:.2f},{s}" for d, t, c, a, s in rows)
    q = ("Below is a CSV export of transactions.\n\n<csv>\n" + csv + "\n</csv>\n\nWhat is the total amount_eur of "
         "all transactions for customer C-017 with status 'settled' and a date in March 2026? Give the number with "
         "two decimals.")
    return q, round(total, 2)


# ---------------------------------------------------------------------------------------------- LC05
def lc05():
    rng = random.Random(505)
    users = [f"u{i:02d}" for i in range(1, 41)]
    events = []
    day = datetime(2026, 5, 4, 9, 0, 0)
    for u in users:
        t = day + timedelta(minutes=rng.randint(0, 240))
        for _ in range(rng.randint(1, 4)):
            dur = timedelta(minutes=rng.randint(3, 150), seconds=rng.randint(0, 59))
            events.append((t, "LOGIN", u))
            events.append((t + dur, "LOGOUT", u))
            t = t + dur + timedelta(minutes=rng.randint(2, 90), seconds=rng.randint(0, 59))
    events.sort()
    probe = datetime(2026, 5, 4, 14, 37, 0)
    assert all(e[0] != probe for e in events)
    active = set()
    for t, kind, u in events:
        if t > probe:
            break
        if kind == "LOGIN":
            active.add(u)
        else:
            active.discard(u)
    log = "\n".join(f"{t:%Y-%m-%d %H:%M:%S} {k} user={u}" for t, k, u in events)
    q = ("Below is an authentication log for one day, in chronological order. A user is logged in between a LOGIN "
         "and their next LOGOUT.\n\n<log>\n" + log + "\n</log>\n\nHow many distinct users were logged in at exactly "
         "14:37:00 on 2026-05-04?")
    return q, len(active)


# ---------------------------------------------------------------------------------------------- LC06
def lc06():
    rng = random.Random(606)
    whs = ["WH-A", "WH-B", "WH-C", "WH-D"]
    skus = [f"SKU-{n}" for n in rng.sample(range(100, 999), 24)] + ["SKU-118"]
    stock = {(s, w): 0 for s in skus for w in whs}
    ops = []
    for i in range(330):
        s = "SKU-118" if rng.random() < 0.12 else rng.choice(skus)
        kind = rng.choices(["RECEIVE", "SHIP", "TRANSFER", "COUNT"], [40, 30, 22, 8])[0]
        w = rng.choice(whs)
        if kind == "RECEIVE":
            q = rng.randint(5, 60)
            stock[(s, w)] += q
            ops.append(f"RECEIVE {q} x {s} at {w}")
        elif kind == "SHIP":
            if stock[(s, w)] == 0:
                continue
            q = rng.randint(1, stock[(s, w)])
            stock[(s, w)] -= q
            ops.append(f"SHIP {q} x {s} from {w}")
        elif kind == "TRANSFER":
            if stock[(s, w)] == 0:
                continue
            w2 = rng.choice([x for x in whs if x != w])
            q = rng.randint(1, stock[(s, w)])
            stock[(s, w)] -= q
            stock[(s, w2)] += q
            ops.append(f"TRANSFER {q} x {s} from {w} to {w2}")
        else:
            q = max(0, stock[(s, w)] + rng.randint(-4, 4))
            stock[(s, w)] = q
            ops.append(f"COUNT CORRECTION: {s} at {w} is set to {q}")
    n_rel = sum(1 for o in ops if "SKU-118" in o)
    assert n_rel >= 25, n_rel
    lines = [f"{i + 1:03d}. {o}" for i, o in enumerate(ops)]
    q = ("Below is a warehouse operations journal, applied in order. All warehouses start empty. RECEIVE adds stock, "
         "SHIP removes stock, TRANSFER moves stock between warehouses, and COUNT CORRECTION overwrites the stock of "
         "that SKU at that warehouse with the stated number.\n\n<journal>\n" + "\n".join(lines) +
         "\n</journal>\n\nHow many units of SKU-118 are at WH-C after the last operation?")
    return q, stock[("SKU-118", "WH-C")]


# ---------------------------------------------------------------------------------------------- LC07
def lc07():
    rng = random.Random(707)
    sections = {
        "2.1": ("daily meal allowance for domestic trips", 45, "EUR"),
        "2.2": ("daily meal allowance for international trips", 70, "EUR"),
        "3.1": ("maximum hotel rate per night in capital cities", 180, "EUR"),
        "3.2": ("maximum hotel rate per night elsewhere", 120, "EUR"),
        "4.1": ("mileage reimbursement for private cars", 30, "cents per km"),
        "4.2": ("maximum taxi fare per single ride", 60, "EUR"),
        "5.1": ("advance booking requirement for flights", 14, "days"),
        "5.2": ("maximum flight duration for economy class", 6, "hours"),
    }
    base = []
    for sec, (desc, val, unit) in sections.items():
        base.append(f"Section {sec}. The {desc} is {val} {unit}. " + filler_paragraph(rng, 3))
    # amendments: (number, effective date, section, new value, repeals)
    amends = [
        (1, "2026-02-01", "3.1", 190, None),
        (2, "2026-04-15", "3.1", 210, None),
        (3, "2026-03-01", "3.1", 200, None),
        (4, "2026-01-10", "2.2", 75, None),
        (5, "2026-05-20", "3.1", 230, None),
        (6, "2026-05-01", None, None, 2),
        (7, "2026-06-01", "4.1", 32, None),
        (8, "2026-06-15", None, None, 5),
        (9, "2026-03-20", "3.2", 125, None),
        (10, "2026-07-01", "3.1", 240, None),
    ]
    rng.shuffle(amends)
    am_text = []
    for n, d, sec, val, rep in amends:
        if rep:
            am_text.append(f"Amendment {n} (effective {d}): Amendment {rep} is repealed. " + filler_paragraph(rng, 2))
        else:
            desc, _, unit = sections[sec]
            am_text.append(f"Amendment {n} (effective {d}): Section {sec} is replaced; the {desc} becomes {val} "
                           f"{unit}. " + filler_paragraph(rng, 2))
    rules = ("Rules of interpretation: (a) a repealed amendment is treated as if it had never been adopted, for "
             "every date (the effective date of the repealing amendment does not matter); "
             "(b) for any date, a section's value is given by the non-repealed amendment with the latest effective "
             "date on or before that date that replaces the section, or by the base policy if there is none; "
             "(c) the amendment number has no bearing on precedence.")
    doc = ("TRAVEL POLICY - BASE TEXT\n\n" + "\n\n".join(base) + "\n\nAMENDMENTS\n\n" + "\n\n".join(am_text) +
           "\n\n" + rules)

    def value_at(sec, date):
        repealed = {a[4] for a in amends if a[4] and a[1] <= "9999"}
        cands = [a for a in amends if a[2] == sec and a[0] not in repealed and a[1] <= date]
        if not cands:
            return sections[sec][1]
        return max(cands, key=lambda a: a[1])[3]

    ans = value_at("3.1", "2026-06-10")
    assert ans == 200, ans
    q = ("Below is a company travel policy with amendments.\n\n<policy>\n" + doc + "\n</policy>\n\nWhat is the "
         "maximum hotel rate per night in capital cities (in EUR) for a stay on 2026-06-10?")
    return q, ans


# ---------------------------------------------------------------------------------------------- LC08
def lc08():
    rng = random.Random(808)
    syll = ["ka", "lo", "mi", "ra", "ven", "dor", "sa", "tel", "bri", "no", "qua", "zen", "fa", "lin", "gor", "ush"]
    cities = set()
    while len(cities) < 42:
        cities.add("".join(rng.choice(syll) for _ in range(rng.randint(2, 3))).capitalize())
    cities = sorted(cities)
    rng.shuffle(cities)
    # grid-ish graph for long paths: 6x7 lattice with random diagonals
    idx = {c: i for i, c in enumerate(cities)}
    edges = {}
    W, H = 7, 6
    for i, c in enumerate(cities):
        x, y = i % W, i // W
        for dx, dy in ((1, 0), (0, 1), (1, 1), (-1, 1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < W and 0 <= ny < H and (dx * dy == 0 or rng.random() < 0.35):
                j = ny * W + nx
                edges[(i, j)] = rng.randint(18, 75)
    adj = {i: [] for i in range(len(cities))}
    for (a, b), w in edges.items():
        adj[a].append((b, w))
        adj[b].append((a, w))

    def dijkstra(s):
        dist = {s: 0}
        pq = [(0, s)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist[u]:
                continue
            for v, w in adj[u]:
                if d + w < dist.get(v, 1e18):
                    dist[v] = d + w
                    heapq.heappush(pq, (d + w, v))
        return dist

    src, dst = 0, len(cities) - 1  # opposite corners
    dist = dijkstra(src)
    ans = dist[dst]
    descr = []
    for (a, b), w in edges.items():
        A, B = cities[a], cities[b]
        if rng.random() < 0.5:
            A, B = B, A
        tpl = rng.choice([
            "A direct train connects {A} and {B}; the ride takes {w} minutes in either direction.",
            "Travellers between {A} and {B} can take the regional line, which needs {w} minutes.",
            "From {A} you can reach {B} by express train in {w} minutes (the same holds in reverse).",
            "The {A}-{B} shuttle runs every hour and the journey lasts {w} minutes.",
        ])
        descr.append(tpl.format(A=A, B=B, w=w))
    rng.shuffle(descr)
    paras = []
    for d in descr:
        paras.append(filler_paragraph(rng, rng.randint(2, 5)).replace("team", "tourism board") + " " + d)
    doc = "\n\n".join(paras)
    q = ("Below is a long travel guide. Every direct train connection is mentioned exactly once; there are no "
         "other connections, transfers take no time, and trains can be used in both directions.\n\n<guide>\n" + doc +
         f"\n</guide>\n\nWhat is the shortest possible total travel time, in minutes, from {cities[src]} to "
         f"{cities[dst]}?")
    return q, ans


def tasks():
    out = []
    q, a = lc01()
    out.append(T("LONG-01", C, 2, "Needle in a server log", q, exact(a), 0.93, fa(a), wrong=fa("36h")))
    q, a = lc02()
    out.append(T("LONG-02", C, 3, "Multi-needle with corrections", q, exact(a, ignore_spaces=True), 0.65, fa(a),
                 wrong=fa(a[:-1] + ("A" if a[-1] != "A" else "B"))))
    q, a = lc03()
    out.append(T("LONG-03", C, 3, "Variable chasing in a long script", q, num(a, exact=True), 0.60, fa(a),
                 wrong=fa(a + 1)))
    q, a = lc04()
    out.append(T("LONG-04", C, 3, "Filtered aggregation over a CSV", q, num(f"{a:.2f}", abs_tol=0.005), 0.60,
                 fa(f"{a:.2f}"), wrong=fa(f"{a + 1:.2f}")))
    q, a = lc05()
    out.append(T("LONG-05", C, 4, "Concurrent sessions at a timestamp", q, num(a, exact=True), 0.35, fa(a),
                 wrong=fa(a + 1)))
    q, a = lc06()
    out.append(T("LONG-06", C, 4, "Inventory state tracking", q, num(a, exact=True), 0.30, fa(a), wrong=fa(a + 3)))
    q, a = lc07()
    out.append(T("LONG-07", C, 4, "Policy with conflicting amendments", q, num(a, exact=True), 0.40, fa(a),
                 wrong=fa(230)))
    q, a = lc08()
    out.append(T("LONG-08", C, 5, "Shortest route hidden in a travel guide", q, num(a, exact=True), 0.15, fa(a),
                 wrong=fa(a + 4)))
    return out


if __name__ == "__main__":
    for t in tasks():
        print(t["id"], t["tier"], "words:", len(t["prompt"].split()), "answer:", t["grader"].get("value") or t["grader"].get("answers"))
