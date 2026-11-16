"""Reference solutions for the CODE tasks. Each REF_* string is exec'd at build time to compute expected
outputs, cross-checked against brute force where possible, and used as the self-test reference answer."""

LCG = '''
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x

def _ints(seed, n, lo, hi):
    g = _lcg(seed)
    return [lo + next(g) % (hi - lo + 1) for _ in range(n)]

def _norm(x):
    if isinstance(x, (list, tuple)):
        return [_norm(v) for v in x]
    return x

def _digest(x):
    import hashlib
    return "sha256:" + hashlib.sha256(repr(_norm(x)).encode()).hexdigest()

def _word(seed, n, alphabet):
    g = _lcg(seed)
    return "".join(alphabet[next(g) % len(alphabet)] for _ in range(n))
'''

REF_PALINDROME = '''
def is_palindrome(s: str) -> bool:
    t = [c.lower() for c in s if c.isascii() and c.isalnum()]
    return t == t[::-1]
'''

REF_MERGE = '''
def merge_intervals(intervals):
    out = []
    for a, b in sorted(intervals):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out
'''

REF_EVAL = '''
def evaluate(expr: str) -> int:
    toks = []
    i = 0
    while i < len(expr):
        c = expr[i]
        if c.isspace():
            i += 1
        elif c.isdigit():
            j = i
            while j < len(expr) and expr[j].isdigit():
                j += 1
            toks.append(int(expr[i:j]))
            i = j
        else:
            toks.append(c)
            i += 1
    pos = 0

    def peek():
        return toks[pos] if pos < len(toks) else None

    def take():
        nonlocal pos
        pos += 1
        return toks[pos - 1]

    def expr_():
        v = term()
        while peek() in ("+", "-"):
            op = take()
            r = term()
            v = v + r if op == "+" else v - r
        return v

    def term():
        v = unary()
        while peek() in ("*", "/"):
            op = take()
            r = unary()
            if op == "*":
                v = v * r
            else:
                q = abs(v) // abs(r)
                v = q if (v >= 0) == (r >= 0) else -q
        return v

    def unary():
        if peek() in ("+", "-"):
            op = take()
            v = unary()
            return -v if op == "-" else v
        return atom()

    def atom():
        t = take()
        if t == "(":
            v = expr_()
            take()
            return v
        return t

    return expr_()
'''

REF_LRU = '''
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity: int):
        self.cap = capacity
        self.d = OrderedDict()

    def get(self, key: int) -> int:
        if key not in self.d:
            return -1
        self.d.move_to_end(key)
        return self.d[key]

    def put(self, key: int, value: int) -> None:
        if key in self.d:
            self.d.move_to_end(key)
        self.d[key] = value
        if len(self.d) > self.cap:
            self.d.popitem(last=False)
'''

REF_ALIEN = '''
import heapq

def alien_order(words):
    letters = sorted({c for w in words for c in w})
    adj = {c: set() for c in letters}
    indeg = {c: 0 for c in letters}
    for w1, w2 in zip(words, words[1:]):
        for a, b in zip(w1, w2):
            if a != b:
                if b not in adj[a]:
                    adj[a].add(b)
                    indeg[b] += 1
                break
        else:
            if len(w1) > len(w2):
                return ""
    heap = [c for c in letters if indeg[c] == 0]
    heapq.heapify(heap)
    out = []
    while heap:
        c = heapq.heappop(heap)
        out.append(c)
        for d in adj[c]:
            indeg[d] -= 1
            if indeg[d] == 0:
                heapq.heappush(heap, d)
    return "".join(out) if len(out) == len(letters) else ""
'''

REF_KEYS = '''
from collections import deque

def shortest_path_all_keys(grid):
    R, Cn = len(grid), len(grid[0])
    nkeys = 0
    for r in range(R):
        for c in range(Cn):
            ch = grid[r][c]
            if ch == "@":
                sr, sc = r, c
            elif "a" <= ch <= "f":
                nkeys = max(nkeys, ord(ch) - 96)
    target = (1 << nkeys) - 1
    seen = {(sr, sc, 0)}
    q = deque([(sr, sc, 0, 0)])
    while q:
        r, c, m, d = q.popleft()
        if m == target:
            return d
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if not (0 <= nr < R and 0 <= nc < Cn):
                continue
            ch = grid[nr][nc]
            if ch == "#":
                continue
            nm = m
            if "a" <= ch <= "f":
                nm |= 1 << (ord(ch) - 97)
            elif "A" <= ch <= "F" and not (m >> (ord(ch) - 65)) & 1:
                continue
            if (nr, nc, nm) not in seen:
                seen.add((nr, nc, nm))
                q.append((nr, nc, nm, d + 1))
    return -1
'''

REF_NONDEC = '''
from functools import lru_cache

def count_special(N: int) -> int:
    digits = list(map(int, str(N)))
    L = len(digits)

    @lru_cache(None)
    def go(i, last, mod, tight, started):
        if i == L:
            return 1 if started and mod == 0 else 0
        hi = digits[i] if tight else 9
        total = 0
        for d in range(0, hi + 1):
            nt = tight and d == hi
            if not started:
                if d == 0:
                    total += go(i + 1, 0, 0, nt, False)
                else:
                    total += go(i + 1, d, d % 7, nt, True)
            elif d >= last:
                total += go(i + 1, d, (mod + d) % 7, nt, True)
        return total

    return go(0, 0, 0, True, False)
'''

REF_DURATION = '''
import re

_NUM = r"(\\d+(?:[.,]\\d+)?)"
_RX = re.compile(r"P(?:" + _NUM + r"Y)?(?:" + _NUM + r"M)?(?:" + _NUM + r"W)?(?:" + _NUM + r"D)?"
                 r"(?:T(?:" + _NUM + r"H)?(?:" + _NUM + r"M)?(?:" + _NUM + r"S)?)?")
_MULT = [365 * 86400, 30 * 86400, 7 * 86400, 86400, 3600, 60, 1]

def parse_duration(s: str) -> float:
    if not isinstance(s, str):
        raise ValueError("not a string")
    m = _RX.fullmatch(s)
    if not m:
        raise ValueError("bad format")
    groups = list(m.groups())
    present = [i for i, g in enumerate(groups) if g is not None]
    if not present:
        raise ValueError("no components")
    if "T" in s and not any(groups[i] is not None for i in (4, 5, 6)):
        raise ValueError("T without time components")
    for i in present[:-1]:
        if "." in groups[i] or "," in groups[i]:
            raise ValueError("fraction only allowed on last component")
    return float(sum(float(groups[i].replace(",", ".")) * _MULT[i] for i in present))
'''

REF_REC = '''
MOD = 1_000_000_007

def _mat_mult(A, B):
    n, m, p = len(A), len(B), len(B[0])
    out = [[0] * p for _ in range(n)]
    for i in range(n):
        Ai = A[i]
        for k in range(m):
            a = Ai[k]
            if a:
                Bk = B[k]
                row = out[i]
                for j in range(p):
                    row[j] = (row[j] + a * Bk[j]) % MOD
    return out

def rec_nth(n: int) -> int:
    base = [1, 1, 2]
    if n < 3:
        return base[n] % MOD
    # state at step k (k>=2): [F(k), F(k-1), F(k-2), (k+1)^2, k+1, 1]
    M = [
        [1, 2, 3, 1, 0, 0],
        [1, 0, 0, 0, 0, 0],
        [0, 1, 0, 0, 0, 0],
        [0, 0, 0, 1, 2, 1],
        [0, 0, 0, 0, 1, 1],
        [0, 0, 0, 0, 0, 1],
    ]
    v = [[2], [1], [1], [9], [3], [1]]
    e = n - 2
    R = [[int(i == j) for j in range(6)] for i in range(6)]
    while e:
        if e & 1:
            R = _mat_mult(R, M)
        M = _mat_mult(M, M)
        e >>= 1
    return _mat_mult(R, v)[0][0]
'''

REF_PALSUB = '''
def count_distinct_palindromes(s: str) -> int:
    # eertree (palindromic tree)
    length = [-1, 0]
    link = [0, 0]
    nxt = [{}, {}]
    last = 1
    for i, ch in enumerate(s):
        cur = last
        while True:
            L = length[cur]
            if i - 1 - L >= 0 and s[i - 1 - L] == ch:
                break
            cur = link[cur]
        if ch in nxt[cur]:
            last = nxt[cur][ch]
            continue
        node = len(length)
        length.append(length[cur] + 2)
        nxt.append({})
        if length[node] == 1:
            link.append(1)
        else:
            p = link[cur]
            while True:
                L = length[p]
                if i - 1 - L >= 0 and s[i - 1 - L] == ch:
                    break
                p = link[p]
            link.append(nxt[p][ch])
        nxt[cur][ch] = node
        last = node
    return len(length) - 2
'''

REF_KNIGHT = '''
def knight_moves(x: int, y: int) -> int:
    x, y = abs(x), abs(y)
    if x < y:
        x, y = y, x
    if x == 1 and y == 0:
        return 3
    if x == 2 and y == 2:
        return 4
    delta = x - y
    if y > delta:
        return delta - 2 * ((delta - y) // 3)
    return delta - 2 * ((delta - y) // 4)
'''

REF_REGEX = '''
def regex_match(text: str, pattern: str) -> bool:
    # parse pattern into atoms: (matcher, quant)
    atoms = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "[":
            j = i + 1
            neg = False
            if pattern[j] == "^":
                neg = True
                j += 1
            chars = set()
            first = True
            while pattern[j] != "]" or first:
                first = False
                if j + 2 < len(pattern) and pattern[j + 1] == "-" and pattern[j + 2] != "]":
                    for o in range(ord(pattern[j]), ord(pattern[j + 2]) + 1):
                        chars.add(chr(o))
                    j += 3
                else:
                    chars.add(pattern[j])
                    j += 1
            m = (lambda ch, chars=frozenset(chars), neg=neg: (ch in chars) != neg)
            i = j + 1
        elif c == ".":
            m = (lambda ch: True)
            i += 1
        else:
            m = (lambda ch, c=c: ch == c)
            i += 1
        q = ""
        if i < len(pattern) and pattern[i] in "*+?":
            q = pattern[i]
            i += 1
        atoms.append((m, q))
    # NFA simulation over positions in atom list
    def closure(states):
        stack = list(states)
        seen = set(states)
        while stack:
            k = stack.pop()
            if k < len(atoms) and atoms[k][1] in ("*", "?"):
                if k + 1 not in seen:
                    seen.add(k + 1)
                    stack.append(k + 1)
        return seen
    cur = closure({0})
    for ch in text:
        nxt = set()
        for k in cur:
            if k < len(atoms):
                m, q = atoms[k]
                if m(ch):
                    if q in ("*", "+"):
                        nxt.add(k)
                    nxt.add(k + 1)
        cur = closure(nxt)
        if not cur:
            return False
    return len(atoms) in cur
'''

REF_KTH = '''
def kth_distinct_substring(s: str, k: int) -> str:
    n = len(s)
    if n == 0:
        return ""
    # suffix array by prefix doubling
    rank = [ord(c) for c in s]
    sa = list(range(n))
    step = 1
    while True:
        key = [(rank[i], rank[i + step] if i + step < n else -1) for i in range(n)]
        sa.sort(key=lambda i: key[i])
        new = [0] * n
        for t in range(1, n):
            new[sa[t]] = new[sa[t - 1]] + (key[sa[t]] != key[sa[t - 1]])
        rank = new
        if rank[sa[-1]] == n - 1:
            break
        step <<= 1
    # kasai lcp: lcp[t] = lcp(sa[t-1], sa[t])
    lcp = [0] * n
    h = 0
    for i in range(n):
        if rank[i] > 0:
            j = sa[rank[i] - 1]
            while i + h < n and j + h < n and s[i + h] == s[j + h]:
                h += 1
            lcp[rank[i]] = h
            if h:
                h -= 1
        else:
            h = 0
    for t in range(n):
        i = sa[t]
        new_count = (n - i) - lcp[t]
        if k <= new_count:
            return s[i:i + lcp[t] + k]
        k -= new_count
    return ""
'''

REF_SLOPE = '''
import heapq

def min_cost_strictly_increasing(a):
    heap = []  # max-heap via negatives
    cost = 0
    for i, v in enumerate(a):
        c = v - i
        heapq.heappush(heap, -c)
        top = -heap[0]
        if top > c:
            cost += top - c
            heapq.heapreplace(heap, -c)
    return cost
'''
