"""MATH: 14 tasks. Every answer is computed here by brute force / exact arithmetic."""
from __future__ import annotations

import math
from fractions import Fraction
from itertools import permutations, product

from util import T, fa, num

C = "math"


def sigma(n):
    return sum(d for d in range(1, n + 1) if n % d == 0)


def dice_prob():
    good = sum(1 for r in product(range(1, 7), repeat=3) if max(r) == 5 and sum(r) % 2 == 0)
    return Fraction(good, 216)


def subsets_mod7():
    dp = [0] * 7
    dp[0] = 1
    for k in range(1, 21):
        dp = [dp[r] + dp[(r - k) % 7] for r in range(7)]
    return dp[0]


def hg_squared():
    B, Cc, A = (Fraction(0), Fraction(0)), (Fraction(14), Fraction(0)), (Fraction(5), Fraction(12))
    assert (A[0] - B[0]) ** 2 + (A[1] - B[1]) ** 2 == 169 and (A[0] - Cc[0]) ** 2 + (A[1] - Cc[1]) ** 2 == 225
    G = ((A[0] + B[0] + Cc[0]) / 3, (A[1] + B[1] + Cc[1]) / 3)
    # orthocenter: altitude from A is x = 5 (BC horizontal); altitude from B is perpendicular to AC
    dx, dy = Cc[0] - A[0], Cc[1] - A[1]
    hx = A[0]
    hy = -dx * hx / dy  # (x, y)·(dx, dy) = 0 through B=(0,0)
    return (hx - G[0]) ** 2 + (hy - G[1]) ** 2


def tilings_2xn(n):
    # cells (r, c); fill first empty cell in column-major order
    from functools import lru_cache

    @lru_cache(None)
    def go(filled):  # filled: frozenset of cells
        for c in range(n):
            for r in range(2):
                if (r, c) not in filled:
                    total = go(filled | {(r, c)})  # 1x1
                    if r == 0 and (1, c) not in filled:
                        total += go(filled | {(0, c), (1, c)})
                    if c + 1 < n and (r, c + 1) not in filled:
                        total += go(filled | {(r, c), (r, c + 1)})
                    return total
        return 1

    return go(frozenset())


def abc_strings():
    cnt = 0
    for s in product("ABC", repeat=10):
        if any(s[i] == s[i + 1] for i in range(9)):
            continue
        if "ABC" in "".join(s):
            cnt += 1
    return cnt


def trailing_zero_gaps(K=2026):
    vals, n = set(), 1
    while True:
        z, p = 0, 5
        while p <= n:
            z += n // p
            p *= 5
        vals.add(z)
        if z > K:
            break
        n += 1
    return sum(1 for k in range(1, K + 1) if k not in vals)


def die_until_sum10():
    # states: 'o' (last roll 1-3), 4, 5, 6. Unknowns E_o, E4, E5, E6 = expected additional rolls.
    # Solve linear system with Fractions by Gaussian elimination.
    S = ["o", 4, 5, 6]

    def nxt(state, r):
        if state != "o" and state + r == 10:
            return None
        return "o" if r <= 3 else r

    n = len(S)
    M = [[Fraction(0)] * (n + 1) for _ in range(n)]
    for i, s in enumerate(S):
        M[i][i] += 1
        M[i][n] = Fraction(1)
        for r in range(1, 7):
            t = nxt(s, r)
            if t is not None:
                M[i][S.index(t)] -= Fraction(1, 6)
    for i in range(n):
        piv = next(k for k in range(i, n) if M[k][i] != 0)
        M[i], M[piv] = M[piv], M[i]
        M[i] = [v / M[i][i] for v in M[i]]
        for k in range(n):
            if k != i and M[k][i] != 0:
                f = M[k][i]
                M[k] = [a - f * b for a, b in zip(M[k], M[i])]
    E = {s: M[i][n] for i, s in enumerate(S)}
    first = 1 + Fraction(1, 6) * (3 * E["o"] + E[4] + E[5] + E[6])
    return first


def eisenstein_count(n):
    lim = int(math.isqrt(4 * n // 3)) + 2
    return sum(1 for x in range(-lim, lim + 1) for y in range(-lim, lim + 1) if x * x + x * y + y * y == n)


def far_perms(n=9):
    return sum(1 for p in permutations(range(1, n + 1)) if all(abs(p[i] - (i + 1)) >= 2 for i in range(n)))


def f3_eq_f2(n=6):
    cnt = 0
    for f in product(range(n), repeat=n):
        if all(f[f[f[x]]] == f[f[x]] for x in range(n)):
            cnt += 1
    return cnt


def digit_sum_3n():
    def s(m):
        t = 0
        while m:
            t += m % 10
            m //= 10
        return t

    return sum(1 for n in range(1, 1_000_000) if s(n) == s(3 * n))


def seq_floor_sqrt(N=1000):
    a = 1
    for _ in range(N - 1):
        a += math.isqrt(a)
    return a


def tasks():
    out = []
    v = sigma(360)
    out.append(T("MATH-01", C, 1, "Sum of divisors",
                 "What is the sum of all positive divisors of 360 (including 1 and 360)?",
                 num(v, exact=True), 0.98, fa(v), wrong=fa(v - 360)))
    v = pow(7, 2026, 1000)
    out.append(T("MATH-02", C, 2, "Last three digits of a power",
                 "What are the last three digits of 7^2026? Give them as an integer between 0 and 999.",
                 num(v, exact=True), 0.90, fa(v), wrong=fa((v + 400) % 1000)))
    v = dice_prob()
    out.append(T("MATH-03", C, 2, "Dice: max and parity",
                 "Three fair six-sided dice are rolled. What is the probability that the largest value shown is "
                 "exactly 5 AND the sum of the three dice is even? Give the answer as a reduced fraction.",
                 num(v, exact=True), 0.85, fa(v), wrong=fa(Fraction(61, 432))))
    v = subsets_mod7()
    out.append(T("MATH-04", C, 3, "Subset sums mod 7",
                 "How many subsets of {1, 2, ..., 20} (the empty set included) have an element sum divisible by 7?",
                 num(v, exact=True), 0.75, fa(v), wrong=fa(2 ** 20 // 7)))
    v = hg_squared()
    out.append(T("MATH-05", C, 3, "Orthocenter-centroid distance",
                 "Triangle ABC has side lengths AB = 13, BC = 14 and CA = 15. Let H be its orthocenter and G its "
                 "centroid. Compute HG^2 and give it as a reduced fraction.",
                 num(v, exact=True), 0.70, fa(v), wrong=fa(Fraction(65, 64))))
    v = tilings_2xn(12)
    out.append(T("MATH-06", C, 3, "Board coverings",
                 "A 2x12 board must be covered completely, with no overlaps, using 1x1 squares and 1x2 dominoes "
                 "(dominoes may be placed horizontally or vertically, and any number of each piece may be used). "
                 "How many different coverings are there?",
                 num(v, exact=True), 0.65, fa(v), wrong=fa(233)))
    v = abc_strings()
    out.append(T("MATH-07", C, 3, "Constrained strings with a pattern",
                 "How many strings of length 10 over the alphabet {A, B, C} have no two adjacent equal letters AND "
                 "contain 'ABC' as a contiguous substring at least once?",
                 num(v, exact=True), 0.50, fa(v), wrong=fa(v + 6)))
    v = trailing_zero_gaps()
    out.append(T("MATH-08", C, 3, "Unreachable trailing-zero counts",
                 "For a positive integer n let z(n) be the number of trailing zeros of n! written in base 10. "
                 "How many integers k with 1 <= k <= 2026 are NOT equal to z(n) for any positive integer n?",
                 num(v, exact=True), 0.50, fa(v), wrong=fa(v + 1)))
    v = die_until_sum10()
    out.append(T("MATH-09", C, 3, "Waiting time for a pair sum",
                 "A fair six-sided die is rolled repeatedly. You stop as soon as the two most recent rolls add up "
                 "to 10. What is the expected total number of rolls (counting all rolls, including the first)? "
                 "Give the exact value.",
                 num(v, exact=True), 0.55, fa(v), wrong=fa(13)))
    n = 7 ** 3 * 13 * 19
    v = eisenstein_count(n)
    out.append(T("MATH-10", C, 4, "Representations by x^2+xy+y^2",
                 f"How many ordered pairs of integers (x, y) satisfy x^2 + x*y + y^2 = {n}?",
                 num(v, exact=True), 0.50, fa(v), wrong=fa(v // 2)))
    v = far_perms(9)
    out.append(T("MATH-11", C, 4, "Permutations that move every element far",
                 "How many permutations p of {1, 2, ..., 9} satisfy |p(i) - i| >= 2 for every i in {1, ..., 9}?",
                 num(v, exact=True), 0.25, fa(v), wrong=fa(v + 2)))
    v = f3_eq_f2(6)
    out.append(T("MATH-12", C, 4, "Functional equation on a finite set",
                 "How many functions f from {1, 2, 3, 4, 5, 6} to itself satisfy f(f(f(x))) = f(f(x)) for every x?",
                 num(v, exact=True), 0.30, fa(v), wrong=fa(1057)))
    v = digit_sum_3n()
    out.append(T("MATH-13", C, 5, "Digit sum preserved by tripling",
                 "Let s(m) denote the sum of the decimal digits of m. How many integers n with 1 <= n <= 999999 "
                 "satisfy s(n) = s(3n)?",
                 num(v, exact=True), 0.08, fa(v), wrong=fa(v - 9)))
    v = seq_floor_sqrt(1000)
    out.append(T("MATH-14", C, 5, "Floor-sqrt recursion",
                 "Define a_1 = 1 and a_(k+1) = a_k + floor(sqrt(a_k)) for k >= 1. Find a_1000.",
                 num(v, exact=True), 0.10, fa(v), wrong=fa(v - 1)))
    return out


if __name__ == "__main__":
    for t in tasks():
        print(t["id"], t["tier"], t["grader"]["value"])
