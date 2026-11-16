"""TRACE: 8 program-tracing / state-tracking tasks. Answers are produced by actually running the program
(Python) or by the reference interpreters below."""
from __future__ import annotations

import contextlib
import io
import random

from util import T, exact, fa, num

C = "trace"


def run_py(src):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(src, {})
    return buf.getvalue().strip()


PY1 = """a = [1, 2, 3]
b = a
c = a[:]
b.append(4)
c.append(5)
a += [6]
b = b + [7]
a.append(8)
print(len(a), len(b), len(c), a[-1], b[-1], c[-1])"""

PY2 = """def make(acc=[]):
    fs = []
    for i in range(3):
        acc.append(i)
        fs.append(lambda x, j=i: x * j + len(acc))
    fs.append(lambda x: x + i)
    return fs

r = []
for k in range(2):
    fs = make()
    r.append(sum(f(k + 1) for f in fs))
print(r)"""

STACK_PROG = """    PUSH 0
    PUSH 1
loop:
    DUP
    PUSH 7
    SUB
    JZ done
    DUP
    DUP
    MUL
    PUSH 5
    MOD
    ROT
    PUSH 2
    MUL
    ADD
    SWAP
    PUSH 1
    ADD
    JMP loop
done:
    POP
    PRINT"""


def run_stack(prog):
    lines = [ln.strip() for ln in prog.splitlines() if ln.strip()]
    labels, code = {}, []
    for ln in lines:
        if ln.endswith(":"):
            labels[ln[:-1]] = len(code)
        else:
            code.append(ln.split())
    st, pc, out = [], 0, []
    steps = 0
    while pc < len(code):
        steps += 1
        op, *arg = code[pc]
        pc += 1
        if op == "PUSH":
            st.append(int(arg[0]))
        elif op == "POP":
            st.pop()
        elif op == "DUP":
            st.append(st[-1])
        elif op == "SWAP":
            st[-1], st[-2] = st[-2], st[-1]
        elif op == "ROT":  # a b c -> b c a
            a, b, c = st[-3], st[-2], st[-1]
            st[-3:] = [b, c, a]
        elif op in ("ADD", "SUB", "MUL", "MOD"):
            b, a = st.pop(), st.pop()
            st.append(a + b if op == "ADD" else a - b if op == "SUB" else a * b if op == "MUL" else a % b)
        elif op == "JZ":
            if st.pop() == 0:
                pc = labels[arg[0]]
        elif op == "JMP":
            pc = labels[arg[0]]
        elif op == "PRINT":
            out.append(st.pop())
    return out


def xorshift32(x, n):
    for _ in range(n):
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= x >> 17
        x ^= (x << 5) & 0xFFFFFFFF
    return x


def life(grid, gens):
    n = len(grid)
    g = [list(r) for r in grid]
    for _ in range(gens):
        ng = [["."] * n for _ in range(n)]
        for r in range(n):
            for c in range(n):
                k = sum(g[(r + dr) % n][(c + dc) % n] == "#" for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                        if (dr, dc) != (0, 0))
                ng[r][c] = "#" if (k == 3 or (k == 2 and g[r][c] == "#")) else "."
        g = ng
    return ["".join(r) for r in g]


def rule110(s, steps):
    n = len(s)
    for _ in range(steps):
        s = "".join(str((110 >> int(s[(i - 1) % n] + s[i] + s[(i + 1) % n], 2)) & 1) for i in range(n))
    return s


def bf(prog, maxsteps=10 ** 7):
    tape, ptr, pc, out = [0] * 300, 0, 0, []
    stack, jump = [], {}
    for i, ch in enumerate(prog):
        if ch == "[":
            stack.append(i)
        elif ch == "]":
            j = stack.pop()
            jump[i], jump[j] = j, i
    steps = 0
    while pc < len(prog):
        ch = prog[pc]
        if ch == "+":
            tape[ptr] = (tape[ptr] + 1) % 256
        elif ch == "-":
            tape[ptr] = (tape[ptr] - 1) % 256
        elif ch == ">":
            ptr += 1
        elif ch == "<":
            ptr -= 1
        elif ch == ".":
            out.append(chr(tape[ptr]))
        elif ch == "[" and tape[ptr] == 0:
            pc = jump[pc]
        elif ch == "]" and tape[ptr] != 0:
            pc = jump[pc]
        pc += 1
        steps += 1
        assert steps < maxsteps
    return "".join(out)


# cell1 = 55, then a loop subtracting 7 per pass wraps around 0 several times before hitting 0 (81 passes)
BF_PROG = "+++++[>+++++++++++<-]>[>+<-------]>.>+++++[<----->-]<.>+++[<------->-]<--."


REG_PROG = """    MOV A, 63
    MOV C, 0
    MOV D, 0
top:
    JEQ A, 1, end
    MOV B, A
    MOD B, 2
    JZ B, half
    MUL A, 3
    ADD A, 1
    DIV A, 2
    ADD D, 1
    JMP count
half:
    DIV A, 2
count:
    ADD C, 1
    JMP top
end:
    HALT"""


def run_reg(prog):
    lines = [ln.strip() for ln in prog.splitlines() if ln.strip()]
    labels, code = {}, []
    for ln in lines:
        if ln.endswith(":"):
            labels[ln[:-1]] = len(code)
        else:
            op, _, rest = ln.partition(" ")
            code.append((op, [x.strip() for x in rest.split(",")] if rest else []))
    R = {}
    val = lambda x: R.get(x, 0) if x.isalpha() else int(x)
    pc = 0
    while True:
        op, a = code[pc]
        pc += 1
        if op == "MOV":
            R[a[0]] = val(a[1])
        elif op == "ADD":
            R[a[0]] = R.get(a[0], 0) + val(a[1])
        elif op == "MUL":
            R[a[0]] = R.get(a[0], 0) * val(a[1])
        elif op == "DIV":
            R[a[0]] = R.get(a[0], 0) // val(a[1])
        elif op == "MOD":
            R[a[0]] = R.get(a[0], 0) % val(a[1])
        elif op == "JZ":
            if R.get(a[0], 0) == 0:
                pc = labels[a[1]]
        elif op == "JEQ":
            if val(a[0]) == val(a[1]):
                pc = labels[a[2]]
        elif op == "JMP":
            pc = labels[a[0]]
        elif op == "HALT":
            return R


def tasks():
    out = []
    o = run_py(PY1)
    out.append(T("TRACE-01", C, 2, "List aliasing",
                 "What does this Python 3 program print? Give the printed line exactly.\n\n```python\n" + PY1 + "\n```",
                 exact(o, ignore_spaces=False), 0.85, fa(o), wrong=fa("6 7 4 8 7 5")))
    o = run_py(PY2)
    out.append(T("TRACE-02", C, 3, "Closures and mutable defaults",
                 "What does this Python 3 program print? Give the printed line exactly.\n\n```python\n" + PY2 + "\n```",
                 exact(o, ignore_spaces=True), 0.65, fa(o), wrong=fa("[14, 22]")))
    o = run_stack(STACK_PROG)
    assert len(o) == 1
    out.append(T("TRACE-03", C, 3, "Stack machine",
                 "A stack machine executes the program below from the first line. Instructions: PUSH n pushes n; POP "
                 "discards the top; DUP duplicates the top; SWAP swaps the top two; ROT rotates the top three so that "
                 "a b c (c on top) becomes b c a (a on top); ADD, SUB, MUL, MOD pop b (the top) then a and push a+b, "
                 "a-b, a*b, a mod b; JZ L pops a value and jumps to label L if it is 0; JMP L jumps to L; PRINT pops "
                 "and prints the top. Execution ends after the last instruction.\n\n```\n" + STACK_PROG +
                 "\n```\n\nWhat number is printed?",
                 num(o[0], exact=True), 0.60, fa(o[0]), wrong=fa(11)))
    seed = 20261116
    v = xorshift32(seed, 3)
    out.append(T("TRACE-04", C, 4, "xorshift32 by hand",
                 "Consider this function operating on unsigned 32-bit integers (all shifts discard bits beyond 32 "
                 "bits):\n\n```c\nuint32_t step(uint32_t x) {\n    x ^= x << 13;\n    x ^= x >> 17;\n    x ^= x << 5;\n"
                 "    return x;\n}\n```\n\nStarting from x = " + str(seed) + ", apply step three times. What is the "
                 "resulting value, in decimal?",
                 num(v, exact=True), 0.30, fa(v), wrong=fa(xorshift32(seed, 2))))
    rng = random.Random(55)
    grid = [["."] * 8 for _ in range(8)]
    for r, c in [(0, 1), (1, 2), (2, 0), (2, 1), (2, 2)]:  # glider
        grid[r][c] = "#"
    for r, c in [(5, 4), (5, 5), (5, 6)]:  # blinker
        grid[r][c] = "#"
    for r, c in [(6, 0), (7, 1), (4, 7), (6, 2)]:
        grid[r][c] = "#"
    g0 = ["".join(r) for r in grid]
    g4 = life(g0, 4)
    flat = "".join(g4)
    out.append(T("TRACE-05", C, 4, "Game of Life on a torus",
                 "Conway's Game of Life runs on an 8x8 board whose edges wrap around (a torus: row 0 neighbours row 7 "
                 "and column 0 neighbours column 7). A live cell with 2 or 3 live neighbours survives, a dead cell "
                 "with exactly 3 live neighbours becomes alive, and every other cell is dead in the next generation. "
                 "'#' is alive and '.' is dead. Initial board (generation 0):\n\n" + "\n".join(g0) + "\n\n"
                 "Give generation 4 as a single line of 64 characters (row 0 first, then row 1, ...), using # and . only.",
                 {"type": "regex", "pattern": r"\s*".join(re_escape(ch) for ch in flat)}, 0.30, fa(flat),
                 wrong=fa("".join(life(g0, 3)))))
    s0 = "000100000000010000001101"
    s10 = rule110(s0, 10)
    out.append(T("TRACE-06", C, 4, "Elementary cellular automaton",
                 "Apply elementary cellular automaton Rule 110 to a ring of 24 cells (the leftmost and rightmost cells "
                 "are neighbours). Rule 110 maps each neighbourhood (left, self, right) to the new state of the cell: "
                 "111->0, 110->1, 101->1, 100->0, 011->1, 010->1, 001->1, 000->0. All cells update simultaneously. "
                 "Starting state:\n\n" + s0 + "\n\nWhat is the state after exactly 10 steps? Answer with the 24-character "
                 "string of 0s and 1s.",
                 exact(s10, ignore_spaces=True), 0.35, fa(s10), wrong=fa(rule110(s0, 9))))
    R = run_reg(REG_PROG)
    ans = f"C={R['C']}, D={R['D']}"
    out.append(T("TRACE-07", C, 4, "Register machine",
                 "This register machine program uses integer registers (all start at 0). MOV r, x sets r to x; ADD, "
                 "MUL, DIV, MOD r, x set r to r+x, r*x, floor(r/x), r mod x; JZ r, L jumps to L if r is 0; "
                 "JEQ r, x, L jumps to L if r equals x; JMP L jumps; HALT stops.\n\n```\n" + REG_PROG + "\n```\n\n"
                 "What are the values of registers C and D when the program halts? Answer in the form 'C=..., D=...'.",
                 {"type": "regex", "pattern": rf"C\s*=\s*{R['C']}\s*,?\s*D\s*=\s*{R['D']}"}, 0.45, fa(ans),
                 wrong=fa(f"C={R['C'] + 1}, D={R['D']}")))
    o = bf(BF_PROG)
    assert o.isprintable() and len(o) == 3, repr(o)
    out.append(T("TRACE-08", C, 5, "Brainfuck with wrap-around",
                 "Execute this Brainfuck program. The tape has 8-bit cells that wrap around (0 - 1 = 255, 255 + 1 = 0), "
                 "all cells start at 0, and the pointer starts at cell 0. '.' outputs the current cell as an ASCII "
                 "character.\n\n```\n" + BF_PROG + "\n```\n\nWhat exact text does the program output? (It is three "
                 "printable characters.)",
                 exact(o, case_sensitive=True), 0.20, fa(o), wrong=fa(o[::-1])))
    return out


def re_escape(ch):
    import re
    return re.escape(ch)


if __name__ == "__main__":
    for t in tasks():
        g = t["grader"]
        print(t["id"], t["tier"], g.get("value") or g.get("answers") or g.get("pattern")[:80])
