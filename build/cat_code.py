"""CODE: 14 tasks graded by hidden unit tests (incl. large inputs with time limits).
Expected outputs come from the reference solutions in code_refs.py, which are cross-checked against brute force."""
from __future__ import annotations

import random
import re
from collections import deque
from itertools import product

import code_refs as R
from util import T

C = "code"

CODE_RULES = ("\n\nWrite the solution in Python 3 using only the standard library. Return exactly one "
              "```python code block containing the complete implementation (no example usage needed). The code "
              "will be run against hidden tests, including large inputs, with a total time limit of {t} seconds.")


def load(ref_src: str, name: str):
    ns: dict = {}
    exec(R.LCG + ref_src, ns)
    return ns[name], ns


def ref_answer(ref_src: str) -> str:
    return "Here is the solution.\n```python\n" + ref_src.strip() + "\n```"


def std_tests(fn_name: str, cases, big=(), timeout_note=""):
    """cases: list of (args_tuple, expected). big: list of (python_expr_returning_args_tuple, expected)."""
    lines = [R.LCG, f"_CASES = {cases!r}",
             "for _i, (_a, _e) in enumerate(_CASES):",
             f"    _g = {fn_name}(*_a)",
             "    assert _g == _e, f'case {_i}: args={str(_a)[:120]} expected={str(_e)[:80]} got={str(_g)[:80]}'"]
    if big:
        lines += [f"_BIG = {list(big)!r}",
                  "for _expr, _e in _BIG:",
                  "    _a = eval(_expr)",
                  f"    _g = {fn_name}(*_a)",
                  "    if isinstance(_e, str) and _e.startswith('sha256:'):",
                  "        _g = _digest(_g)",
                  "    assert _g == _e, f'large case {_expr[:60]}: expected={str(_e)[:60]} got={str(_g)[:60]}'"]
    return "\n".join(lines)


def eval_big(ns, expr):
    return eval(expr, ns)


def big_expect(ns, f, expr):
    """Expected value for a large case: small results stored literally, large ones as a digest."""
    v = f(*eval(expr, ns))
    return ns["_digest"](v) if len(repr(v)) > 200 else v


# ---------------------------------------------------------------------------- brute forces
def bf_merge(iv):
    pts = {}
    for a, b in iv:
        for x in range(2 * a, 2 * b + 1):
            pts[x] = True
    xs = sorted(pts)
    out = []
    for x in xs:
        if out and x == out[-1][1] + 1:
            out[-1][1] = x
        else:
            out.append([x, x])
    return [[a // 2, b // 2] for a, b in out]


def gen_expr(rng, depth=0):
    if depth > 3 or rng.random() < 0.3:
        v = str(rng.randint(0, 30))
        return ("-" + v) if rng.random() < 0.15 else v
    kind = rng.random()
    if kind < 0.15:
        return "-(" + gen_expr(rng, depth + 1) + ")"
    a, b = gen_expr(rng, depth + 1), gen_expr(rng, depth + 1)
    op = rng.choice(["+", "-", "*", "/", "+", "*"])
    s = f"{a} {op} {b}" if rng.random() < 0.5 else f"{a}{op}{b}"
    return f"({s})" if rng.random() < 0.4 else s


def bf_count_special(N):
    c = 0
    for x in range(1, N + 1):
        s = str(x)
        if all(s[i] <= s[i + 1] for i in range(len(s) - 1)) and sum(map(int, s)) % 7 == 0:
            c += 1
    return c


def bf_knight(maxc=60):
    S = 2 * maxc + 20
    dist = {(0, 0): 0}
    q = deque([(0, 0)])
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)):
            nx, ny = x + dx, y + dy
            if abs(nx) <= S and abs(ny) <= S and (nx, ny) not in dist:
                dist[(nx, ny)] = dist[(x, y)] + 1
                q.append((nx, ny))
    return dist


def bf_distinct_pal(s):
    return len({s[i:j] for i in range(len(s)) for j in range(i + 1, len(s) + 1) if s[i:j] == s[i:j][::-1]})


def bf_kth(s, k):
    subs = sorted({s[i:j] for i in range(len(s)) for j in range(i + 1, len(s) + 1)})
    return subs[k - 1] if k <= len(subs) else ""


def bf_slope(a):
    # DP over candidate values (b_i - i takes values among a_j - j)
    n = len(a)
    c = [a[i] - i for i in range(n)]
    vals = sorted(set(c))
    INF = float("inf")
    dp = [abs(c[0] - v) for v in vals]
    for i in range(1, n):
        best = INF
        nd = []
        for j, v in enumerate(vals):
            best = min(best, dp[j])
            nd.append(best + abs(c[i] - v))
        dp = nd
    return min(dp)


def bf_regex(text, pattern):
    pyre = ""
    i = 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "[":
            j = pattern.index("]", i + 1)
            pyre += pattern[i:j + 1]
            i = j + 1
        elif ch in ".*+?":
            pyre += ch
            i += 1
        else:
            pyre += re.escape(ch)
            i += 1
    return re.fullmatch(pyre, text) is not None


def rand_pattern(rng):
    atoms = []
    for _ in range(rng.randint(1, 6)):
        r = rng.random()
        if r < 0.5:
            a = rng.choice("abc")
        elif r < 0.7:
            a = "."
        else:
            neg = "^" if rng.random() < 0.3 else ""
            a = "[" + neg + rng.choice(["a-b", "bc", "a", "b-c", "ac"]) + "]"
        if rng.random() < 0.5:
            a += rng.choice("*+?")
        atoms.append(a)
    return "".join(atoms)


def rand_grid(rng, R_, C_, nkeys, wall_p):
    g = [["#" if rng.random() < wall_p else "." for _ in range(C_)] for _ in range(R_)]
    cells = [(r, c) for r in range(R_) for c in range(C_)]
    rng.shuffle(cells)
    r, c = cells.pop()
    g[r][c] = "@"
    for k in range(nkeys):
        r, c = cells.pop()
        g[r][c] = chr(97 + k)
        r, c = cells.pop()
        g[r][c] = chr(65 + k)
    return ["".join(row) for row in g]


def alien_words(rng, alphabet_size, n, maxlen):
    letters = list("abcdefghijklmnopqrstuvwxyz"[:alphabet_size])
    order = letters[:]
    rng.shuffle(order)
    rank = {c: i for i, c in enumerate(order)}
    words = {"".join(rng.choice(letters) for _ in range(rng.randint(1, maxlen))) for _ in range(n)}
    return sorted(words, key=lambda w: [rank[c] for c in w])


# ---------------------------------------------------------------------------- tasks
def tasks():
    out = []
    rng = random.Random(4242)

    # C01 palindrome ---------------------------------------------------------
    f, _ = load(R.REF_PALINDROME, "is_palindrome")
    inputs = ["A man, a plan, a canal: Panama", "race a car", "", ".,,", "0P", "Ab1bA", "ab_a", "No 'x' in Nixon",
              "Was it a car or a cat I saw?", "abcdba", "1a2", "a", "Zz", "été", "Madam, I'm Adam.", "çab ba", "²xy yx"]
    cases = [((s,), f(s)) for s in inputs]
    assert cases[0][1] and not cases[1][1] and cases[2][1] and not cases[4][1]
    out.append(T("CODE-01", C, 1, "Alphanumeric palindrome",
                 "Implement `is_palindrome(s: str) -> bool` that returns True if `s` reads the same forwards and "
                 "backwards after removing every character that is not an ASCII letter or ASCII digit and ignoring "
                 "letter case. The empty string counts as a palindrome." + CODE_RULES.format(t=10),
                 {"type": "code", "test_code": std_tests("is_palindrome", cases), "timeout": 10}, 0.98,
                 ref_answer(R.REF_PALINDROME),
                 wrong=ref_answer("def is_palindrome(s):\n    t = [c.lower() for c in s if c.isalnum()]\n    return t == t[::-1]")))

    # C02 merge intervals ------------------------------------------------------
    f, ns = load(R.REF_MERGE, "merge_intervals")
    cases = [(([[1, 3], [2, 6], [8, 10], [15, 18]],), [[1, 6], [8, 10], [15, 18]]), (([[1, 4], [4, 5]],), [[1, 5]]),
             (([],), []), (([[5, 5]],), [[5, 5]]), (([[1, 2], [3, 4]],), [[1, 2], [3, 4]])]
    for _ in range(40):
        iv = []
        for _ in range(rng.randint(0, 9)):
            a = rng.randint(-10, 20)
            iv.append([a, a + rng.randint(0, 6)])
        exp = f([list(x) for x in iv])
        assert exp == bf_merge(iv)
        cases.append(((iv,), exp))
    big_expr = "([[x, x + (x % 13)] for x in _ints(77, 200000, -10**9, 10**9)],)"
    big = [(big_expr, big_expect(ns, f, big_expr))]
    out.append(T("CODE-02", C, 2, "Merge intervals",
                 "Implement `merge_intervals(intervals: list[list[int]]) -> list[list[int]]`. Each interval [a, b] "
                 "(a <= b) is a closed interval of real numbers. Merge all intervals that share at least one point "
                 "(so [1, 4] and [4, 5] merge into [1, 5], but [1, 2] and [3, 4] stay separate). Return the merged "
                 "intervals sorted by start. The input may be unsorted or empty and must not be assumed sorted. "
                 "Inputs can contain up to 200000 intervals." + CODE_RULES.format(t=20),
                 {"type": "code", "test_code": std_tests("merge_intervals", cases, big), "timeout": 20}, 0.93,
                 ref_answer(R.REF_MERGE), wrong=ref_answer(R.REF_MERGE.replace("a <= out[-1][1]", "a < out[-1][1]"))))

    # C03 expression evaluator -------------------------------------------------
    f, _ = load(R.REF_EVAL, "evaluate")
    fixed = ["1 + 2 * 3", "(1 + 2) * 3", "-7 / 2", "7 / -2", "2 - -3", "-(2 + 3) * -4", "10 / 3 * 3", "+5 - +2",
             "((((3))))", "100 / (7 - 2*3)", "2*3-4*5", "-3*-3", "--4", "8 / 3 / 2", "-(-(1))", "0 - 2147483648",
             "1-2-3-4", "  12 *(  3+  4 ) ", "-10/3", "6/-4*-1"]
    cases = []
    for e in fixed:
        cases.append(((e,), f(e)))
    for _ in range(80):
        while True:
            e = gen_expr(rng)
            try:
                v = f(e)
                break
            except ZeroDivisionError:
                continue
        if "/" not in e:
            assert v == eval(e.replace("--", "- -")), e
        cases.append(((e,), v))
    assert f("-7 / 2") == -3 and f("7 / -2") == -3 and f("2 - -3") == 5 and f("-(2 + 3) * -4") == 20
    out.append(T("CODE-03", C, 2, "Arithmetic expression evaluator",
                 "Implement `evaluate(expr: str) -> int` that evaluates an arithmetic expression containing "
                 "non-negative integer literals, the binary operators + - * /, parentheses, unary + and unary - "
                 "(which may be stacked, e.g. '--4'), and arbitrary spaces. Use the usual precedence (unary operators "
                 "bind tightest, then * and /, then + and -) with left associativity for binary operators. '/' is "
                 "integer division that truncates toward zero (e.g. -7 / 2 == -3). Inputs never divide by zero. "
                 "Do not use eval() or exec()." + CODE_RULES.format(t=10),
                 {"type": "code", "test_code": std_tests("evaluate", cases), "timeout": 10}, 0.80, ref_answer(R.REF_EVAL)))

    # C04 LRU cache -------------------------------------------------------------
    _, ns = load(R.REF_LRU, "LRUCache")
    LRU = ns["LRUCache"]

    def run_ops(cap, ops):
        c = LRU(cap)
        res = []
        for op in ops:
            if op[0] == "put":
                c.put(op[1], op[2])
            else:
                res.append(c.get(op[1]))
        return res

    seqs = [(2, [("put", 1, 1), ("put", 2, 2), ("get", 1), ("put", 3, 3), ("get", 2), ("put", 4, 4), ("get", 1),
                 ("get", 3), ("get", 4)]),
            (1, [("put", 2, 1), ("get", 2), ("put", 3, 2), ("get", 2), ("get", 3)]),
            (2, [("put", 2, 1), ("put", 2, 2), ("get", 2), ("put", 1, 1), ("put", 4, 1), ("get", 2)])]
    for _ in range(15):
        cap = rng.randint(1, 5)
        ops = [("put", rng.randint(0, 8), rng.randint(0, 99)) if rng.random() < 0.5 else ("get", rng.randint(0, 8))
               for _ in range(60)]
        seqs.append((cap, ops))
    lru_cases = [(cap, ops, run_ops(cap, ops)) for cap, ops in seqs]
    big_ops_code = ("[('put', k % 5003, k) if k % 3 else ('get', k % 7919) for k in _ints(5, 300000, 0, 10**6)]")
    big_ns = {}
    exec(R.LCG, big_ns)
    big_exp = big_ns["_digest"](run_ops(5000, eval(big_ops_code, big_ns)))
    lru_test = R.LCG + f"""
_CASES = {lru_cases!r}
def _run(cap, ops):
    c = LRUCache(cap)
    res = []
    for op in ops:
        if op[0] == 'put':
            c.put(op[1], op[2])
        else:
            res.append(c.get(op[1]))
    return res
for _i, (_cap, _ops, _e) in enumerate(_CASES):
    _g = _run(_cap, _ops)
    assert _g == _e, f'sequence {{_i}} differs'
import time as _time
_t0 = _time.time()
_g = _run(5000, {big_ops_code})
assert _digest(_g) == {big_exp!r}, 'large sequence differs'
assert _time.time() - _t0 < 6, 'too slow: operations must be O(1)'
"""
    out.append(T("CODE-04", C, 2, "LRU cache",
                 "Implement a class `LRUCache` with `__init__(self, capacity: int)`, `get(self, key: int) -> int` "
                 "(return the value, or -1 if the key is absent) and `put(self, key: int, value: int) -> None`. Both "
                 "a successful get and any put make the key the most recently used. When a put inserts a new key and "
                 "the cache exceeds its capacity, evict the least recently used key. Both operations must run in O(1) "
                 "average time." + CODE_RULES.format(t=20),
                 {"type": "code", "test_code": lru_test, "timeout": 20}, 0.92, ref_answer(R.REF_LRU)))

    # C05 alien order -------------------------------------------------------------
    f, _ = load(R.REF_ALIEN, "alien_order")
    cases = [((["wrt", "wrf", "er", "ett", "rftt"],), f(["wrt", "wrf", "er", "ett", "rftt"])),
             ((["z", "x"],), "zx"), ((["z", "x", "z"],), ""), ((["abc", "ab"],), ""), ((["ab", "abc"],), "abc"),
             ((["z", "z"],), "z"), ((["ba", "bc", "ac", "cab"],), f(["ba", "bc", "ac", "cab"]))]
    assert f(["wrt", "wrf", "er", "ett", "rftt"]) == "wertf"
    for _ in range(25):
        w = alien_words(rng, rng.randint(3, 10), rng.randint(3, 30), 5)
        if rng.random() < 0.25 and len(w) > 2:  # corrupt: swap two words -> may become invalid
            i = rng.randrange(len(w) - 1)
            w[i], w[i + 1] = w[i + 1], w[i]
        cases.append(((w,), f(w)))
    assert any(c[1] == "" for c in cases[7:]) and any(c[1] for c in cases[7:])
    out.append(T("CODE-05", C, 3, "Alien dictionary order",
                 "A list of words is claimed to be sorted lexicographically according to an unknown ordering of the "
                 "letters that occur in it. Implement `alien_order(words: list[str]) -> str` that returns an ordering "
                 "of ALL distinct letters appearing in the words that is consistent with the list. If several "
                 "orderings are consistent, return the one that is smallest in normal (Unicode) string comparison. "
                 "If no ordering is consistent (contradictory constraints, or a word appears before a proper prefix "
                 "of itself), return the empty string. Only the first differing letter of two adjacent words gives "
                 "information." + CODE_RULES.format(t=10),
                 {"type": "code", "test_code": std_tests("alien_order", cases), "timeout": 10}, 0.60,
                 ref_answer(R.REF_ALIEN)))

    # C06 keys and locks BFS ---------------------------------------------------
    f, _ = load(R.REF_KEYS, "shortest_path_all_keys")
    cases = [((["@.a..", "###.#", "b.A.B"],), 8), ((["@..aA", "..B#.", "....b"],), 6), ((["@Aa"],), -1)]
    for args, e in cases:
        assert f(*args) == e
    for _ in range(30):
        g = rand_grid(rng, rng.randint(2, 12), rng.randint(2, 12), rng.randint(1, 4), rng.choice([0.1, 0.2, 0.3]))
        cases.append(((g,), f(g)))
    for seed in range(4):
        g = rand_grid(random.Random(900 + seed), 40, 40, 6, 0.18)
        cases.append(((g,), f(g)))
    assert any(c[1] == -1 for c in cases) and max(c[1] for c in cases) > 30
    out.append(T("CODE-06", C, 3, "Shortest path collecting all keys",
                 "Implement `shortest_path_all_keys(grid: list[str]) -> int`. The grid contains '@' (start, exactly "
                 "one), '.' (empty), '#' (wall), lowercase letters 'a'-'f' (keys) and uppercase 'A'-'F' (locks). If the "
                 "grid has k keys they are exactly the first k letters, and each key's lock may or may not be present. "
                 "Each move goes one cell up, down, left or right, staying inside the grid and never entering a wall. "
                 "Walking onto a key picks it up. You may enter a lock cell only if you already hold its key. Return "
                 "the minimum number of moves needed to hold all keys, or -1 if impossible. Grids are up to 40x40."
                 + CODE_RULES.format(t=20),
                 {"type": "code", "test_code": std_tests("shortest_path_all_keys", cases), "timeout": 20}, 0.70,
                 ref_answer(R.REF_KEYS)))

    # C07 digit DP ----------------------------------------------------------------
    f, _ = load(R.REF_NONDEC, "count_special")
    for N in [1, 7, 16, 100, 777, 1000, 4321, 9999, 54321]:
        assert f(N) == bf_count_special(N), N
    Ns = [1, 6, 7, 70, 1000, 54321, 10 ** 6, 123456789, 10 ** 12, 999999999999999999, 10 ** 18,
          314159265358979323, 111111111111111111, 899999999999999999]
    cases = [((N,), f(N)) for N in Ns]
    out.append(T("CODE-07", C, 3, "Counting special integers",
                 "Implement `count_special(N: int) -> int` returning how many integers x with 1 <= x <= N satisfy "
                 "both: (1) the decimal digits of x are non-decreasing from left to right (e.g. 1129 qualifies, 1219 "
                 "does not), and (2) the sum of the decimal digits of x is divisible by 7. N can be as large as "
                 "10^18." + CODE_RULES.format(t=20),
                 {"type": "code", "test_code": std_tests("count_special", cases), "timeout": 20}, 0.65,
                 ref_answer(R.REF_NONDEC)))

    # C08 ISO duration parsing ---------------------------------------------------------
    f, _ = load(R.REF_DURATION, "parse_duration")
    valid = ["P1Y2M10DT2H30M", "PT0,5S", "P1.5D", "P2W", "P1M", "PT1M", "P1W2D", "PT36H", "P0D", "PT1H0.25M",
             "P3Y6M4DT12H30M5S", "P10Y", "PT0.000001S", "P1DT1S", "P1Y1D"]
    invalid = ["", "P", "PT", "P1H", "PT1D", "P1Y1Y", "P1DT", "p1d", "P-1D", "P.5D", "P1.D", "PT1.5H30M", "1D",
               "P1D ", " P1D", "P1M1Y", "PT1S1M", "P1,5W2D", "P1D2W", "PT1HT1M", "P1Y2M10DT2H30M5S10S", "P1e3D"]
    vcases = [(s, f(s)) for s in valid]
    for s in invalid:
        try:
            f(s)
            raise AssertionError("reference accepted invalid " + s)
        except ValueError:
            pass
    assert abs(f("P1Y2M10DT2H30M") - ((365 + 60 + 10) * 86400 + 2 * 3600 + 30 * 60)) < 1e-9
    dur_test = f"""
_VALID = {vcases!r}
_INVALID = {invalid!r}
for _s, _e in _VALID:
    _g = parse_duration(_s)
    assert isinstance(_g, float), f'{{_s!r}}: result must be a float'
    assert abs(_g - _e) <= 1e-6 * max(1.0, abs(_e)), f'{{_s!r}}: expected {{_e}} got {{_g}}'
for _s in _INVALID:
    try:
        parse_duration(_s)
    except ValueError:
        continue
    raise AssertionError(f'{{_s!r}} should raise ValueError')
"""
    out.append(T("CODE-08", C, 3, "Strict ISO-8601 duration parser",
                 "Implement `parse_duration(s: str) -> float` for this exact subset of ISO-8601 durations and return "
                 "the total number of seconds as a float:\n"
                 "- The string starts with 'P', followed by an optional date part with components in this order: "
                 "nY, nM, nW, nD; then optionally 'T' followed by a time part with components in this order: nH, nM, "
                 "nS. Each component appears at most once and components must appear in the stated order.\n"
                 "- n is one or more ASCII digits, optionally followed by a decimal separator ('.' or ',') and one "
                 "or more digits. A decimal fraction is allowed ONLY on the last component in the whole string.\n"
                 "- At least one component must be present. If 'T' is present, at least one time component must "
                 "follow it.\n"
                 "- Units: Y = 365 days, M (date part) = 30 days, W = 7 days, D = 86400 s, H = 3600 s, M (time "
                 "part) = 60 s, S = 1 s.\n"
                 "- Anything else (lowercase letters, spaces, signs, exponents, empty string, wrong order, ...) must "
                 "raise ValueError." + CODE_RULES.format(t=10),
                 {"type": "code", "test_code": dur_test, "timeout": 10}, 0.45, ref_answer(R.REF_DURATION)))

    # C09 linear recurrence with polynomial term -----------------------------------------
    f, _ = load(R.REF_REC, "rec_nth")
    Fv = [1, 1, 2]
    for n in range(3, 3000):
        Fv.append((Fv[-1] + 2 * Fv[-2] + 3 * Fv[-3] + n * n) % 1_000_000_007)
    for n in list(range(0, 60)) + [999, 2999]:
        assert f(n) == Fv[n], n
    ns_ = [0, 1, 2, 3, 4, 5, 10, 50, 2999, 10 ** 6, 123456789012, 10 ** 18, 10 ** 18 - 1, 987654321987654321]
    cases = [((n,), f(n)) for n in ns_]
    out.append(T("CODE-09", C, 4, "Huge-index recurrence",
                 "Define F(0) = 1, F(1) = 1, F(2) = 2 and, for n >= 3, F(n) = F(n-1) + 2*F(n-2) + 3*F(n-3) + n^2. "
                 "Implement `rec_nth(n: int) -> int` returning F(n) modulo 1_000_000_007, for 0 <= n <= 10^18."
                 + CODE_RULES.format(t=15),
                 {"type": "code", "test_code": std_tests("rec_nth", cases), "timeout": 15}, 0.60,
                 ref_answer(R.REF_REC), wrong=ref_answer(R.REF_REC.replace("[0, 0, 0, 1, 2, 1]", "[0, 0, 0, 1, 1, 0]"))))

    # C10 distinct palindromic substrings ---------------------------------------------------
    f, ns = load(R.REF_PALSUB, "count_distinct_palindromes")
    for _ in range(200):
        s = "".join(rng.choice("ab" if rng.random() < 0.5 else "abc") for _ in range(rng.randint(0, 25)))
        assert f(s) == bf_distinct_pal(s), s
    small = ["", "a", "aaa", "abba", "abacaba", "banana", "racecar", "abcdef", "aabbaa"]
    cases = [((s,), f(s)) for s in small]
    bigs = ["(_word(3, 100000, 'ab'),)", "('a' * 100000,)", "(('abacabadabacaba' * 7000)[:100000],)",
            "(_word(11, 100000, 'abcdefghijklmnopqrstuvwxyz'),)"]
    big = [(e, big_expect(ns, f, e)) for e in bigs]
    out.append(T("CODE-10", C, 4, "Distinct palindromic substrings",
                 "Implement `count_distinct_palindromes(s: str) -> int` returning the number of DISTINCT non-empty "
                 "substrings of `s` that are palindromes. `s` consists of lowercase letters and has length up to "
                 "100000." + CODE_RULES.format(t=25),
                 {"type": "code", "test_code": std_tests("count_distinct_palindromes", cases, big), "timeout": 25},
                 0.55, ref_answer(R.REF_PALSUB)))

    # C11 knight distance -------------------------------------------------------------------------
    f, _ = load(R.REF_KNIGHT, "knight_moves")
    dist = bf_knight(60)
    for x in range(-60, 61):
        for y in range(-60, 61):
            assert f(x, y) == dist[(x, y)], (x, y)
    pts = [(0, 0), (1, 0), (2, 2), (1, 1), (3, 0), (-1, -2), (4, 4), (0, 1), (5, 5), (-7, 3), (2, 0)]
    pts += [(rng.randint(-60, 60), rng.randint(-60, 60)) for _ in range(40)]
    pts += [(10 ** 9, 10 ** 9), (-10 ** 9, 1), (999999999, -2), (123456789, 987654321), (10 ** 9, 0), (1, 10 ** 9),
            (500000001, 499999999), (-3, -10 ** 9)]
    cases = [((x, y), f(x, y)) for x, y in pts]
    out.append(T("CODE-11", C, 4, "Knight distance on an infinite board",
                 "A chess knight starts at (0, 0) on an infinite board. Implement `knight_moves(x: int, y: int) -> int` "
                 "returning the minimum number of knight moves needed to reach (x, y). Coordinates satisfy |x|, |y| "
                 "<= 10^9." + CODE_RULES.format(t=10),
                 {"type": "code", "test_code": std_tests("knight_moves", cases), "timeout": 10}, 0.35,
                 ref_answer(R.REF_KNIGHT), wrong=ref_answer(R.REF_KNIGHT.replace("if x == 2 and y == 2:\n        return 4", "if False:\n        return 4"))))

    # C12 regex matcher -----------------------------------------------------------------------------
    f, _ = load(R.REF_REGEX, "regex_match")
    cases = []
    for _ in range(400):
        p = rand_pattern(rng)
        t = "".join(rng.choice("abc") for _ in range(rng.randint(0, 7)))
        e = f(t, p)
        assert e == bf_regex(t, p), (t, p)
        if len(cases) < 120 or e:
            cases.append(((t, p), e))
    fixed = [("aab", "c*a*b"), ("mississippi", "mis*is*p*."), ("ab", ".*"), ("", "a*"), ("", "a+"),
             ("abc", "[a-c]+"), ("abd", "[^d]+"), ("abd", "[^d]+d"), ("a1b2", "[a-z][0-9][a-z][0-9]"), ("x", "x?x"),
             ("xx", "x?x"), ("xxx", "x?x"), ("zzz", "z+z+z+"), ("zz", "z+z+z+"), ("a]", "a]")]
    for t, p in fixed:
        cases.append(((t, p), f(t, p)))
    big = [("('a' * 60, 'a*' * 25 + 'b')", False), ("('a' * 60, 'a?' * 30 + 'a' * 30)", True),
           ("('ab' * 3000, '[ab]*' * 8 + 'c?')", True), ("('ab' * 2000 + 'c', '.*.*.*.*.*.*.*.*d')", False)]
    for e, v in big:
        assert f(*eval(e)) == v
    out.append(T("CODE-12", C, 4, "Regex matcher without backtracking blow-up",
                 "Implement `regex_match(text: str, pattern: str) -> bool` that returns True iff the WHOLE text "
                 "matches the pattern. Pattern syntax:\n"
                 "- a lowercase letter, digit or ']' matches itself;\n"
                 "- '.' matches any single character;\n"
                 "- '[...]' is a character class listing characters and/or ranges like 'a-c'; '[^...]' is its "
                 "negation (the '^' only has this meaning right after '[');\n"
                 "- '*', '+', '?' apply to the single preceding atom (literal, '.', or class): zero-or-more, "
                 "one-or-more, zero-or-one.\n"
                 "Patterns are always valid; there are no groups or escapes. Do not use the `re` or `fnmatch` "
                 "modules. Some tests use long texts with many quantifiers, so the running time must be polynomial."
                 + CODE_RULES.format(t=20),
                 {"type": "code", "test_code": std_tests("regex_match", cases, big), "timeout": 20}, 0.55,
                 ref_answer(R.REF_REGEX)))

    # C13 k-th distinct substring --------------------------------------------------------------------
    f, ns = load(R.REF_KTH, "kth_distinct_substring")
    for _ in range(150):
        s = "".join(rng.choice("abc") for _ in range(rng.randint(1, 12)))
        tot = len({s[i:j] for i in range(len(s)) for j in range(i + 1, len(s) + 1)})
        for k in (1, rng.randint(1, tot), tot, tot + 1):
            assert f(s, k) == bf_kth(s, k), (s, k)
    cases = [(("banana", 1), "a"), (("banana", 5), f("banana", 5)), (("banana", 15), f("banana", 15)),
             (("banana", 16), f("banana", 16)), (("aaaa", 3), "aaa"), (("aaaa", 5), ""), (("abcab", 7), f("abcab", 7))]
    big_exprs = ["(_word(21, 50000, 'ab'), 123456789)", "(_word(22, 50000, 'abcd'), 987654321)",
                 "('a' * 50000, 50000)", "('a' * 50000, 50001)", "(_word(23, 50000, 'xyz'), 1)",
                 "(('abcabcabd' * 6000)[:50000], 500000000)"]
    big = [(e, big_expect(ns, f, e)) for e in big_exprs]
    out.append(T("CODE-13", C, 5, "k-th distinct substring",
                 "Implement `kth_distinct_substring(s: str, k: int) -> str`. Consider the set of DISTINCT non-empty "
                 "substrings of `s`, sorted in ordinary lexicographic order (a proper prefix comes before the longer "
                 "string). Return the k-th one (1-indexed), or the empty string if there are fewer than k. `s` has "
                 "length up to 50000 and consists of lowercase letters; k can be up to 2*10^9." + CODE_RULES.format(t=40),
                 {"type": "code", "test_code": std_tests("kth_distinct_substring", cases, big), "timeout": 40}, 0.25,
                 ref_answer(R.REF_KTH)))

    # C14 slope trick ----------------------------------------------------------------------------------
    f, ns = load(R.REF_SLOPE, "min_cost_strictly_increasing")
    for _ in range(300):
        a = [rng.randint(-8, 8) for _ in range(rng.randint(1, 9))]
        assert f(a) == bf_slope(a), a
    cases = [(([1, 2, 3],), 0), (([3, 2, 1],), f([3, 2, 1])), (([5, 5, 5, 5],), 4), (([0],), 0),
             (([2, 1, 5, 11, 5, 9, 11],), f([2, 1, 5, 11, 5, 9, 11])), (([5, 4, 3, 2, 1],), 12)]
    for args, e in cases:
        assert f(*args) == e, args
    for _ in range(20):
        a = [rng.randint(-50, 50) for _ in range(rng.randint(1, 30))]
        cases.append(((a,), f(a)))
    big_exprs = ["(_ints(31, 100000, -10**9, 10**9),)", "(list(range(100000, 0, -1)),)",
                 "([x // 1000 for x in _ints(32, 100000, 0, 10**9)],)", "([7] * 100000,)"]
    big = [(e, big_expect(ns, f, e)) for e in big_exprs]
    out.append(T("CODE-14", C, 5, "Cheapest strictly increasing fix",
                 "Implement `min_cost_strictly_increasing(a: list[int]) -> int`. You may replace each a[i] by any "
                 "integer b[i]; the cost is the sum of |a[i] - b[i]|. Return the minimum cost such that b is strictly "
                 "increasing (b[0] < b[1] < ...). len(a) <= 100000 and |a[i]| <= 10^9." + CODE_RULES.format(t=20),
                 {"type": "code", "test_code": std_tests("min_cost_strictly_increasing", cases, big), "timeout": 20},
                 0.40, ref_answer(R.REF_SLOPE), wrong=ref_answer(R.REF_SLOPE.replace("c = v - i", "c = v"))))
    for t in out:
        t["mode"] = "code"
    return out


if __name__ == "__main__":
    import time
    t0 = time.time()
    ts = tasks()
    for t in ts:
        print(t["id"], t["tier"], len(t["grader"]["test_code"]), "chars of tests")
    print("built in", round(time.time() - t0, 1), "s")
