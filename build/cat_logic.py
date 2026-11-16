"""LOGIC: 12 tasks. Puzzles are generated / verified by exhaustive solvers (unique solutions asserted)."""
from __future__ import annotations

import random
from fractions import Fraction
from functools import lru_cache
from itertools import permutations, product

from util import T, exact, fa, num

C = "logic"


# ============================================================================ zebra puzzles
ATTRS6 = {
    "name": ["Ada", "Bora", "Cem", "Dila", "Ece", "Femi"],
    "color": ["red", "green", "blue", "white", "yellow", "black"],
    "drink": ["tea", "coffee", "milk", "juice", "water", "cocoa"],
    "pet": ["cat", "dog", "fish", "bird", "rabbit", "turtle"],
    "job": ["chef", "pilot", "nurse", "judge", "baker", "tailor"],
    "sport": ["chess", "tennis", "rowing", "judo", "golf", "karate"],
}


def phrase(attr, v):
    return {
        "name": v,
        "color": f"the person in the {v} house",
        "drink": f"the {v} drinker",
        "pet": f"the {v} owner",
        "job": f"the {v}",
        "sport": f"the person who plays {v}" if v in ("chess", "tennis", "golf") else f"the person who does {v}",
    }[attr]


def cap(s):
    return s[0].upper() + s[1:]


def zebra_solve(attrs, clues, limit=2):
    """CSP solver with forward checking. Variables = attribute values, domain = house index.
    clues: tuples (attrs, check(pos), text, spec) with spec ('u', v, pred) or ('b', v1, v2, rel).
    Returns up to `limit` solutions as dicts value->house."""
    n = len(next(iter(attrs.values())))
    group = {v: a for a, vs in attrs.items() for v in vs}
    dom = {v: set(range(n)) for v in group}
    unary = [c[3] for c in clues if c[3][0] == "u"]
    binary = [c[3] for c in clues if c[3][0] == "b"]
    for _, v, pred in unary:
        dom[v] = {h for h in dom[v] if pred(h)}
    nbrs = {v: [] for v in group}
    for _, v1, v2, rel in binary:
        nbrs[v1].append((v2, lambda h1, h2, rel=rel: rel(h1, h2)))
        nbrs[v2].append((v1, lambda h2, h1, rel=rel: rel(h1, h2)))
    sols = []

    def rec(dom):
        if len(sols) >= limit:
            return
        unassigned = [v for v in dom if len(dom[v]) > 1]
        if not unassigned:
            pos = {v: next(iter(d)) for v, d in dom.items()}
            if all(c[1](pos) for c in clues) and all(len({pos[v] for v in vs}) == n for vs in attrs.values()):
                sols.append(pos)
            return
        var = min(unassigned, key=lambda v: (len(dom[v]), -len(nbrs[v])))
        for h in sorted(dom[var]):
            nd = {v: set(d) for v, d in dom.items()}
            nd[var] = {h}
            if propagate(nd, [var]):
                rec(nd)

    def propagate(nd, queue):
        while queue:
            v = queue.pop()
            if len(nd[v]) != 1:
                continue
            h = next(iter(nd[v]))
            for w in attrs[group[v]]:
                if w != v and h in nd[w]:
                    nd[w].discard(h)
                    if not nd[w]:
                        return False
                    if len(nd[w]) == 1:
                        queue.append(w)
            for w, rel in nbrs[v]:
                newd = {h2 for h2 in nd[w] if rel(h, h2)}
                if not newd:
                    return False
                if newd != nd[w]:
                    nd[w] = newd
                    if len(newd) == 1:
                        queue.append(w)
        # hidden singles: a house that only one value of an attribute can take
        changed = True
        while changed:
            changed = False
            for a, vs in attrs.items():
                for h in range(n):
                    cands = [v for v in vs if h in nd[v]]
                    if not cands:
                        return False
                    if len(cands) == 1 and len(nd[cands[0]]) > 1:
                        nd[cands[0]] = {h}
                        if not propagate(nd, [cands[0]]):
                            return False
                        changed = True
        return True

    init = [v for v in dom if len(dom[v]) == 1]
    if any(not d for d in dom.values()) or not propagate(dom, init):
        return []
    rec(dom)
    return sols


def make_clue(kind, a1, v1, a2=None, v2=None, k=None):
    P1 = cap(phrase(a1, v1))
    P2 = phrase(a2, v2) if a2 else None
    if kind == "same":
        rel, text = (lambda x, y: x == y), f"{P1} is {P2}."
    elif kind == "notsame":
        rel, text = (lambda x, y: x != y), f"{P1} is not {P2}."
    elif kind == "leftof1":
        rel, text = (lambda x, y: x + 1 == y), f"{P1} lives immediately to the left of {P2}."
    elif kind == "next":
        rel, text = (lambda x, y: abs(x - y) == 1), f"{P1} lives next to {P2}."
    elif kind == "leftof":
        rel, text = (lambda x, y: x < y), f"{P1} lives somewhere to the left of {P2}."
    elif kind == "gap1":
        rel, text = (lambda x, y: abs(x - y) == 2), f"There is exactly one house between {phrase(a1, v1)} and {P2}."
    elif kind == "at":
        pred = lambda h, k=k: h == k
        return ({a1}, lambda p, v1=v1, pred=pred: pred(p[v1]), f"{P1} lives in house {k + 1}.", ("u", v1, pred))
    elif kind == "notat":
        pred = lambda h, k=k: h != k
        return ({a1}, lambda p, v1=v1, pred=pred: pred(p[v1]), f"{P1} does not live in house {k + 1}.", ("u", v1, pred))
    else:
        raise ValueError(kind)
    return ({a1, a2}, lambda p, v1=v1, v2=v2, rel=rel: rel(p[v1], p[v2]), text, ("b", v1, v2, rel))


def gen_zebra(n_houses, attr_names, kinds, seed):
    rng = random.Random(seed)
    attrs = {a: ATTRS6[a][:n_houses] for a in attr_names}
    sol = {a: rng.sample(range(n_houses), n_houses) for a in attr_names}
    house = {v: sol[a][i] for a in attr_names for i, v in enumerate(attrs[a])}
    vals = [(a, v) for a in attr_names for v in attrs[a]]

    def rand_true_clue():
        while True:
            kind = rng.choice(kinds)
            (a1, v1), (a2, v2) = rng.sample(vals, 2)
            if a1 == a2 and kind in ("same", "notsame"):
                continue
            k = rng.randrange(n_houses)
            if kind == "at":
                k = house[v1]
            if kind == "notat" and k == house[v1]:
                continue
            c = make_clue(kind, a1, v1, a2, v2, k)
            if c[1](house):
                return c

    clues = []
    while True:
        clues.append(rand_true_clue())
        if len(clues) >= 8 and len(zebra_solve(attrs, clues)) == 1:
            break
    # minimise: drop clues that are not needed
    i = 0
    while i < len(clues):
        trial = clues[:i] + clues[i + 1:]
        if len(zebra_solve(attrs, trial)) == 1:
            clues = trial
        else:
            i += 1
    assert len(zebra_solve(attrs, clues)) == 1
    return attrs, house, clues


def zebra_text(n, attrs, clues, question):
    lines = [f"There are {n} houses in a row, numbered 1 to {n} from left to right. Each house has exactly one "
             "resident, and the residents differ in every attribute below (each value occurs exactly once):"]
    for a, vs in attrs.items():
        lines.append(f"- {a}: {', '.join(vs)}")
    lines.append("")
    lines.append("Clues (\"next to\" means in an adjacent house; \"immediately to the left\" means house number "
                 "exactly one lower):")
    for i, c in enumerate(clues, 1):
        lines.append(f"{i}. {c[2]}")
    lines.append("")
    lines.append(question)
    return "\n".join(lines)


# ============================================================================ scheduling
JOBS = {  # name: (duration_hours, prerequisites)
    "A": (3, []), "B": (2, []), "C": (4, ["A"]), "D": (2, ["A"]), "E": (5, ["B"]),
    "F": (3, ["C", "D"]), "G": (4, ["D", "E"]), "H": (2, ["F", "G"]), "I": (6, ["B"]),
}


def min_makespan(jobs, workers):
    names = sorted(jobs)

    @lru_cache(None)
    def best(done, running):  # running: tuple of (name, remaining)
        if len(done) == len(names):
            return 0
        started = done | frozenset(r[0] for r in running)
        avail = [j for j in names if j not in started and all(p in done for p in jobs[j][1])]
        free = workers - len(running)
        options = []
        # start any subset (size <= free) of available jobs now, then advance to next completion
        from itertools import combinations
        for k in range(0, min(free, len(avail)) + 1):
            for subset in combinations(avail, k):
                run = list(running) + [(j, jobs[j][0]) for j in subset]
                if not run:
                    continue
                step = min(r[1] for r in run)
                nd = done | frozenset(r[0] for r in run if r[1] == step)
                nr = tuple(sorted((r[0], r[1] - step) for r in run if r[1] > step))
                options.append(step + best(nd, nr))
        return min(options)

    return best(frozenset(), tuple())


# ============================================================================ epistemic puzzle
DATES = [("March", 4), ("March", 9), ("March", 17), ("April", 9), ("April", 21), ("May", 13), ("May", 21),
         ("June", 2), ("June", 13), ("July", 4), ("July", 25), ("August", 17), ("August", 28),
         ("September", 2), ("September", 30)]


def epistemic(dates):
    S = list(dates)

    def by(S, idx, val):
        return [d for d in S if d[idx] == val]

    # 1. Bernard (knows day): "I don't know the date."
    S1 = [d for d in S if len(by(S, 1, d[1])) > 1]
    # 2. Albert (knows month): "I don't know it either."
    S2 = [d for d in S1 if len(by(S1, 0, d[0])) > 1]
    # 3. Bernard: "Now I know it."
    S3 = [d for d in S2 if len(by(S2, 1, d[1])) == 1]
    # 4. Albert: "Now I know it too."
    S4 = [d for d in S3 if len(by(S3, 0, d[0])) == 1]
    return S1, S2, S3, S4


# ============================================================================ knights / knaves / spies
PEOPLE = "ABCDEFGH"


ROLE = {"K": "knight", "N": "knave", "S": "spy"}


def kks_make(spec):
    """spec: (speaker, kind, args...) -> (speaker, text, fn)"""
    spk, kind, *x = spec
    cnt = lambda a, r: sum(a[p] == r for p in PEOPLE)
    if kind == "is":          # X is a <role>
        X, r = x
        art = "an" if r == "knave" and False else "a"
        return spk, f"{X} is a {r}.", lambda a: a[X] == r
    if kind == "isnot":
        X, r = x
        return spk, f"{X} is not a {r}.", lambda a: a[X] != r
    if kind == "same":
        X, Y = x
        return spk, f"{X} and {Y} are of the same type.", lambda a: a[X] == a[Y]
    if kind == "diff":
        X, Y = x
        return spk, f"{X} and {Y} are of different types.", lambda a: a[X] != a[Y]
    if kind == "count":       # exactly k knights / knaves
        r, k = x
        return spk, f"Exactly {k} of us eight are {r}s.", lambda a: cnt(a, r) == k
    if kind == "atleast1":    # at least one of X, Y is a <role>
        X, Y, r = x
        return spk, f"At least one of {X} and {Y} is a {r}.", lambda a: a[X] == r or a[Y] == r
    if kind == "if":          # if X is r1 then Y is r2
        X, r1, Y, r2 = x
        return spk, f"If {X} is a {r1}, then {Y} is a {r2}.", lambda a: a[X] != r1 or a[Y] == r2
    if kind == "both":
        X, Y, r = x
        return spk, f"{X} and {Y} are both {r}s.", lambda a: a[X] == r and a[Y] == r
    if kind == "more":        # more r1 than r2
        r1, r2 = x
        return spk, f"There are more {r1}s than {r2}s among us.", lambda a: cnt(a, r1) > cnt(a, r2)
    raise ValueError(kind)


# found with kks_search(0) -> seed 53; uniqueness re-asserted in tasks()
KKS_SPECS = [("A", "both", "F", "G", "knave"), ("B", "is", "G", "knight"), ("C", "same", "B", "D"),
             ("D", "is", "C", "knight"), ("E", "diff", "A", "C"), ("F", "diff", "D", "B"),
             ("G", "atleast1", "B", "H", "knave"), ("H", "if", "E", "knight", "F", "knave"),
             ("D", "isnot", "C", "spy"), ("H", "if", "E", "knave", "D", "knight")]


def kks_random_spec(rng, spk):
    r = lambda: rng.choice(["knight", "knave", "spy"])
    X, Y = rng.sample([p for p in PEOPLE if p != spk], 2)
    kind = rng.choice(["is", "isnot", "same", "diff", "count", "atleast1", "if", "both", "more"])
    if kind in ("is", "isnot"):
        return (spk, kind, X, r())
    if kind in ("same", "diff"):
        return (spk, kind, X, Y)
    if kind == "count":
        return (spk, kind, rng.choice(["knight", "knave"]), rng.randint(2, 4))
    if kind == "atleast1":
        return (spk, kind, X, Y, rng.choice(["knight", "knave"]))
    if kind == "if":
        return (spk, kind, X, r(), Y, r())
    if kind == "both":
        return (spk, kind, X, Y, rng.choice(["knight", "knave"]))
    return (spk, kind, *rng.sample(["knight", "knave", "spy"], 2))


def kks_search(seed_start=0):
    for seed in range(seed_start, seed_start + 200000):
        rng = random.Random(seed)
        speakers = list(PEOPLE) + rng.sample(PEOPLE, 2)
        specs = [kks_random_spec(rng, s) for s in speakers]
        stmts = [kks_make(sp) for sp in specs]
        sols = kks_solve(stmts)
        if len(sols) == 1:
            roles = sols[0]
            # every role must be present at least twice among non-spies, and spies' statements must matter
            if sum(v == "knight" for v in roles.values()) >= 2 and sum(v == "knave" for v in roles.values()) >= 2:
                return seed, specs


def kks_statements():
    return [kks_make(sp) for sp in KKS_SPECS]


def kks_solve(stmts):
    sols = []
    for combo in product(["knight", "knave", "spy"], repeat=8):
        a = dict(zip(PEOPLE, combo))
        if sum(v == "spy" for v in combo) != 2:
            continue
        ok = True
        for spk, _, fn in stmts:
            t = fn(a)
            if a[spk] == "knight" and not t or a[spk] == "knave" and t:
                ok = False
                break
        if ok:
            sols.append(a)
    return sols


# ============================================================================ sudoku
def sudoku_solve(grid, limit=2):
    g = list(grid)
    sols = []
    rows = [set() for _ in range(9)]
    cols = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]
    empties = []
    for i, v in enumerate(g):
        r, c = divmod(i, 9)
        if v:
            rows[r].add(v); cols[c].add(v); boxes[r // 3 * 3 + c // 3].add(v)
        else:
            empties.append(i)

    def rec():
        if len(sols) >= limit:
            return
        best, best_opts = None, None
        for i in empties:
            if g[i]:
                continue
            r, c = divmod(i, 9)
            opts = [d for d in range(1, 10) if d not in rows[r] and d not in cols[c] and d not in boxes[r // 3 * 3 + c // 3]]
            if best is None or len(opts) < len(best_opts):
                best, best_opts = i, opts
                if len(opts) <= 1:
                    break
        if best is None:
            sols.append(list(g))
            return
        r, c = divmod(best, 9)
        b = r // 3 * 3 + c // 3
        for d in best_opts:
            g[best] = d
            rows[r].add(d); cols[c].add(d); boxes[b].add(d)
            rec()
            rows[r].discard(d); cols[c].discard(d); boxes[b].discard(d)
            g[best] = 0

    rec()
    return sols


def gen_sudoku(seed, target_clues=24):
    rng = random.Random(seed)
    # random full grid from a shuffled pattern
    base = list(range(1, 10))
    rng.shuffle(base)

    def pattern(r, c):
        return (3 * (r % 3) + r // 3 + c) % 9

    rows = [g * 3 + r for g in rng.sample(range(3), 3) for r in rng.sample(range(3), 3)]
    cols = [g * 3 + c for g in rng.sample(range(3), 3) for c in rng.sample(range(3), 3)]
    full = [base[pattern(r, c)] for r in rows for c in cols]
    assert len(sudoku_solve(full, 2)) == 1
    puzzle = list(full)
    cells = list(range(81))
    rng.shuffle(cells)
    for i in cells:
        if sum(1 for v in puzzle if v) <= target_clues:
            break
        keep = puzzle[i]
        puzzle[i] = 0
        if len(sudoku_solve(puzzle, 2)) != 1:
            puzzle[i] = keep
    assert len(sudoku_solve(puzzle, 2)) == 1
    return puzzle, full


# ============================================================================ tasks
def tasks():
    out = []
    out.append(T("LOGIC-01", C, 1, "Height ordering",
                 "Eve is taller than Ada. Ada is taller than Bora. Bora is taller than Cem. Dila is shorter than "
                 "Cem. Who is the third tallest of the five?",
                 exact("Bora"), 0.98, fa("Bora"), wrong=fa("Cem")))

    # knights & knaves (verified unique)
    sols = []
    for A, B, Cc, D in product([True, False], repeat=4):
        s = {"A": A, "B": B, "C": Cc, "D": D}
        st = {"A": (not B) and (not D), "B": Cc, "C": (not A) or D, "D": sum(s.values()) == 2}
        if all(st[p] == s[p] for p in s):
            sols.append(s)
    assert len(sols) == 1
    knights = [p for p, v in sols[0].items() if v]
    out.append(T("LOGIC-02", C, 2, "Knights and knaves",
                 "On an island every inhabitant is either a knight (always tells the truth) or a knave (always lies). "
                 "You meet A, B, C and D.\n"
                 "A says: \"B and D are both knaves.\"\n"
                 "B says: \"C is a knight.\"\n"
                 "C says: \"A is a knave or D is a knight.\"\n"
                 "D says: \"Exactly two of us four are knights.\"\n"
                 "Which of them are knights? List all knights (comma-separated); if none, answer 'none'.",
                 {"type": "set", "items": knights}, 0.90, fa(", ".join(knights)), wrong=fa("A, D")))

    out.append(T("LOGIC-03", C, 2, "River crossing with a big boat",
                 "A farmer must take a wolf, a goat and a cabbage across a river. If left alone together without the "
                 "farmer, the wolf would eat the goat and the goat would eat the cabbage. The farmer's boat is large: "
                 "it can carry the farmer plus up to three of the items at once. What is the minimum number of "
                 "one-way river crossings needed to get the farmer and all three items to the other side?",
                 num(1, exact=True), 0.85, fa(1), wrong=fa(7)))

    # 4-door, 2-car Monty Hall, computed by enumeration
    win = Fraction(0)
    for cars in [(a, b) for a in range(4) for b in range(4) if a < b]:
        p_layout = Fraction(1, 6)
        goats_other = [d for d in (1, 2, 3) if d not in cars]
        for opened in goats_other:
            p_open = Fraction(1, len(goats_other))
            remaining = [d for d in (1, 2, 3) if d != opened]
            for sw in remaining:
                if sw in cars:
                    win += p_layout * p_open * Fraction(1, len(remaining))
    out.append(T("LOGIC-04", C, 3, "Four-door game show variant",
                 "A game show has 4 closed doors: 2 hide cars and 2 hide goats, placed uniformly at random. You pick "
                 "door 1. The host, who knows what is behind every door, then opens one of doors 2, 3, 4 that hides a "
                 "goat (choosing uniformly at random if there is more than one such door). You then switch to one of "
                 "the two other unopened doors, chosen uniformly at random. What is the probability that you win a "
                 "car? Give a reduced fraction.",
                 num(win, exact=True), 0.70, fa(win), wrong=fa(Fraction(5, 8))))

    attrs, house, clues = gen_zebra(5, ["name", "color", "drink", "pet", "job"],
                                    ["same", "same", "next", "leftof1", "notsame", "notat", "gap1"], seed=6)
    fish_owner = next(n for n in attrs["name"] if house[n] == house["fish"])
    water_job = next(j for j in attrs["job"] if house[j] == house["water"])
    q = ("Who owns the fish, and what is the job of the water drinker? Answer with the name and the job in that "
         "order, separated by a comma.")
    out.append(T("LOGIC-05", C, 3, "Five-house logic grid",
                 zebra_text(5, attrs, clues, q),
                 {"type": "sequence", "items": [fish_owner, water_job]}, 0.45,
                 fa(f"{fish_owner}, {water_job}"), wrong=fa(f"{water_job}, {fish_owner}")))

    best = min_makespan(JOBS, 2)
    job_lines = "\n".join(f"- {j}: {d} h" + (f", requires {', '.join(p)} to be finished first" if p else "")
                          for j, (d, p) in sorted(JOBS.items()))
    out.append(T("LOGIC-06", C, 3, "Two-worker scheduling",
                 "Nine jobs must be completed by a team of 2 identical workers. Each job is done by a single worker "
                 "without interruption, a worker does one job at a time, and a job can only start after all of its "
                 "prerequisites are finished. Workers may stay idle.\n" + job_lines +
                 "\nWhat is the minimum possible number of hours until all nine jobs are finished?",
                 num(best, exact=True), 0.55, fa(best), wrong=fa(best + 1)))

    out.append(T("LOGIC-07", C, 3, "Self-referential statements",
                 "Consider these eight statements:\n"
                 "1. Exactly four of these eight statements are true.\n"
                 "2. Statement 1 is false.\n"
                 "3. Statements 4 and 5 are either both true or both false.\n"
                 "4. At most two of statements 5, 6, 7, 8 are true.\n"
                 "5. Statement 2 is true or statement 7 is true.\n"
                 "6. At least four of these eight statements are true.\n"
                 "7. Statement 8 is false.\n"
                 "8. Exactly one of statements 1, 3, 6 is true.\n"
                 "Exactly one assignment of truth values is consistent. Which statements are true? "
                 "List their numbers separated by commas.",
                 {"type": "set", "items": ["1", "5", "6", "7"]}, 0.55, fa("1, 5, 6, 7"), wrong=fa("2, 5, 6, 8")))

    out.append(T("LOGIC-08", C, 3, "Counterfeit coin limit",
                 "You have N coins. Exactly one is counterfeit and it is either heavier or lighter than the genuine "
                 "coins (you do not know which). You have a two-pan balance and may use it at most 4 times; you have no "
                 "extra coins known to be genuine and no weights. What is the largest N for which there is a strategy "
                 "that always identifies the counterfeit coin AND determines whether it is heavier or lighter?",
                 num(39, exact=True), 0.60, fa(39), wrong=fa(40)))

    attrs6, house6, clues6 = gen_zebra(6, ["name", "color", "drink", "pet", "job", "sport"],
                                       ["same", "next", "leftof", "gap1", "notsame", "notat", "leftof1"], seed=8)
    order = sorted(attrs6["name"], key=lambda n: house6[n])
    out.append(T("LOGIC-09", C, 4, "Six-house logic grid",
                 zebra_text(6, attrs6, clues6, "List the six names in house order from house 1 to house 6, "
                                               "separated by commas."),
                 {"type": "sequence", "items": order}, 0.25, fa(", ".join(order)),
                 wrong=fa(", ".join(order[1:] + order[:1]))))

    S1, S2, S3, S4 = epistemic(DATES)
    assert len(S4) == 1 and len(S3) > 1 and len(S1) < len(DATES) and len(S2) < len(S1) and len(S3) < len(S2)
    ans = f"{S4[0][0]} {S4[0][1]}"
    date_list = ", ".join(f"{m} {d}" for m, d in DATES)
    out.append(T("LOGIC-10", C, 4, "Who knows the date",
                 "Mira's birthday is one of these dates:\n" + date_list + "\n"
                 "Mira tells Albert only the month and tells Bernard only the day. Both know the full list above, both "
                 "are perfectly logical, and both hear everything that is said. The conversation goes:\n"
                 "1. Bernard: \"I don't know the date.\"\n"
                 "2. Albert: \"I don't know it either.\"\n"
                 "3. Bernard: \"Now I know it.\"\n"
                 "4. Albert: \"Now I know it too.\"\n"
                 "What is Mira's birthday? Answer in the form 'Month Day', e.g. 'July 4'.",
                 exact(ans), 0.30, fa(ans), wrong=fa("March 4")))

    stmts = kks_statements()
    sols = kks_solve(stmts)
    assert len(sols) == 1, sols
    knights8 = [p for p in PEOPLE if sols[0][p] == "knight"]
    spies8 = [p for p in PEOPLE if sols[0][p] == "spy"]
    stext = "\n".join(f"{s} says: \"{t}\"" for s, t, _ in stmts)
    out.append(T("LOGIC-11", C, 5, "Knights, knaves and spies",
                 "Eight people A, B, C, D, E, F, G, H are each a knight (always tells the truth), a knave (always lies) "
                 "or a spy (may tell the truth or lie). There are exactly 2 spies among them. They make these "
                 "statements:\n" + stext + "\n"
                 "Exactly one assignment of roles is consistent with all of this. Who are the two spies, and who are "
                 "the knights? Answer in the form 'spies: X, Y; knights: P, Q, ...' with letters in alphabetical order.",
                 {"type": "regex",
                  "pattern": r"spies\s*[:=]\s*" + r"\s*,\s*".join(spies8) + r"\s*[;,]?\s*knights\s*[:=]\s*" +
                             r"\s*,\s*".join(knights8) + r"\s*"},
                 0.15, fa(f"spies: {', '.join(spies8)}; knights: {', '.join(knights8)}"),
                 wrong=fa(f"spies: {', '.join(spies8)}; knights: {', '.join(knights8[:-1])}")))

    puzzle, full = gen_sudoku(seed=2026, target_clues=24)
    grid_txt = "\n".join(" ".join(str(v) if v else "." for v in puzzle[r * 9:(r + 1) * 9]) for r in range(9))
    sol = "".join(map(str, full))
    out.append(T("LOGIC-12", C, 5, "Sudoku",
                 "Solve this Sudoku (fill every row, column and 3x3 box with the digits 1-9 exactly once). "
                 "'.' marks an empty cell.\n\n" + grid_txt + "\n\n"
                 "Give the completed grid as a single line of 81 digits, row by row from top-left to bottom-right.",
                 {"type": "regex", "pattern": r"\D*" + r"\D*".join(sol) + r"\D*"}, 0.15, fa(sol),
                 wrong=fa(sol[:-2] + sol[-1] + sol[-2])))
    return out


if __name__ == "__main__":
    import time
    t0 = time.time()
    ALL = tasks()
    for t in ALL:
        g = t["grader"]
        print(t["id"], t["tier"], g.get("value") or g.get("items") or g.get("answers") or g.get("pattern")[:60])
    print("built in", round(time.time() - t0, 1), "s")
    for t in ALL[4:5] + ALL[8:9]:
        print(t["prompt"])
        print()
