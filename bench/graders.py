"""Deterministic graders. No LLM judge anywhere: every task is pass/fail by code.

grade(task, record) -> {"passed": bool, "extracted": str|None, "detail": str}

`record` is one line of a responses.jsonl file produced by run.py; graders use
record["content"] (the visible answer, reasoning stripped) and, for agent tasks,
record["transcript"].
"""
from __future__ import annotations

import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from fractions import Fraction

from . import checkers, envs
from .common import extract_final, norm_text, parse_number, strip_thinking

ALL_PASSED = "ALL_TESTS_PASSED_7f3a"


# ----------------------------------------------------------------------------- helpers
def _result(passed: bool, extracted, detail: str = "") -> dict:
    return {"passed": bool(passed), "extracted": extracted, "detail": detail}


def extract_code(text: str, lang: str = "python") -> str | None:
    visible = strip_thinking(text)
    blocks = re.findall(r"```[ \t]*([A-Za-z0-9_+-]*)[^\n]*\n(.*?)```", visible, re.S)
    if blocks:
        tagged = [b for tag, b in blocks if tag.lower() in (lang, "py" if lang == "python" else lang)]
        return (tagged or [b for _, b in blocks])[-1]
    if lang == "python" and re.search(r"^\s*(def|class) ", visible, re.M):
        return visible
    if lang == "sql" and re.search(r"\bselect\b", visible, re.I):
        return visible
    return None


def run_python_tests(code: str, test_code: str, timeout: float) -> tuple[bool, str]:
    src = code + "\n\n# ---- hidden tests ----\n" + test_code + f"\nprint({ALL_PASSED!r})\n"
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "candidate_with_tests.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
        try:
            proc = subprocess.run([sys.executable, "-I", path], cwd=d, capture_output=True, text=True,
                                  timeout=timeout, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            return False, f"timeout after {timeout}s"
    if proc.returncode == 0 and ALL_PASSED in proc.stdout:
        return True, "all tests passed"
    err = (proc.stderr or proc.stdout or "").strip().splitlines()
    return False, "tests failed: " + (" | ".join(err[-4:])[:600] if err else f"exit {proc.returncode}")


# ----------------------------------------------------------------------------- answer graders
def _g_exact(spec, ans):
    if ans is None:
        return _result(False, None, "no FINAL ANSWER found")
    kw = dict(keep_case=spec.get("case_sensitive", False), remove_spaces=spec.get("ignore_spaces", False))
    got = norm_text(ans, **kw)
    for a in spec["answers"]:
        if got == norm_text(a, **kw):
            return _result(True, ans)
    return _result(False, ans, "expected one of " + repr(spec["answers"][:3]))


def _g_number(spec, ans):
    val = parse_number(ans)
    if val is None:
        return _result(False, ans, "could not parse a number")
    target = Fraction(str(spec["value"]))
    if spec.get("exact", False):
        return _result(val == target, ans, f"expected exactly {spec['value']}")
    rel, abs_ = spec.get("rel_tol", 0.0), spec.get("abs_tol", 0.0)
    ok = abs(float(val) - float(target)) <= max(abs_, rel * abs(float(target)))
    return _result(ok, ans, f"expected {spec['value']} (rel_tol={rel}, abs_tol={abs_})")


def _split_items(ans: str, sep: str | None):
    s = ans.strip().strip("[](){}")
    parts = re.split(sep or r"\s*[,;]\s*|\s+and\s+", s)
    return [p for p in (norm_text(x) for x in parts) if p]


def _g_set(spec, ans):
    if ans is None:
        return _result(False, None, "no FINAL ANSWER found")
    got = _split_items(ans, spec.get("sep"))
    want = [norm_text(x) for x in spec["items"]]
    ok = sorted(got) == sorted(want)
    return _result(ok, ans, f"expected set {spec['items']}")


def _g_sequence(spec, ans):
    if ans is None:
        return _result(False, None, "no FINAL ANSWER found")
    got = _split_items(ans, spec.get("sep"))
    want = [norm_text(x) for x in spec["items"]]
    if spec.get("ignore_spaces"):
        got = [g.replace(" ", "") for g in got]
        want = [w.replace(" ", "") for w in want]
    return _result(got == want, ans, f"expected sequence {spec['items']}")


def _g_regex(spec, ans):
    if ans is None:
        return _result(False, None, "no FINAL ANSWER found")
    ok = re.fullmatch(spec["pattern"], ans.strip(), re.I if spec.get("ignore_case", True) else 0) is not None
    return _result(ok, ans, f"must fully match /{spec['pattern']}/")


def _g_code(spec, content):
    code = extract_code(content, "python")
    if not code:
        return _result(False, None, "no python code block found")
    ok, detail = run_python_tests(code, spec["test_code"], spec.get("timeout", 20))
    return _result(ok, code[:200] + ("..." if len(code) > 200 else ""), detail)


def _g_sql(spec, content):
    query = extract_code(content, "sql")
    if not query:
        return _result(False, None, "no SQL code block found")
    query = query.strip().rstrip(";").strip()
    con = sqlite3.connect(":memory:")
    try:
        con.executescript(spec["setup_sql"])
        rows = con.execute(query).fetchall()
    except Exception as e:  # noqa: BLE001
        return _result(False, query[:200], f"sql error: {e}")
    finally:
        con.close()

    def norm_row(r):
        out = []
        for v in r:
            if isinstance(v, float):
                v = round(v, spec.get("round", 2))
            out.append(v)
        return tuple(out)

    got = [norm_row(r) for r in rows]
    want = [norm_row(r) for r in spec["expected_rows"]]
    if not spec.get("ordered", True):
        got, want = sorted(got, key=repr), sorted(want, key=repr)
    ok = got == want
    return _result(ok, query[:200], "result rows match" if ok else f"rows differ: got {got[:5]} ... expected {want[:5]} ...")


ANSWER_GRADERS = {
    "exact": _g_exact,
    "number": _g_number,
    "set": _g_set,
    "sequence": _g_sequence,
    "regex": _g_regex,
}


def grade(task: dict, record: dict) -> dict:
    spec = task["grader"]
    gtype = spec["type"]
    content = record.get("content") or ""
    if record.get("error"):
        return _result(False, None, "request error: " + str(record["error"])[:200])
    if gtype in ANSWER_GRADERS:
        return ANSWER_GRADERS[gtype](spec, extract_final(content))
    if gtype == "code":
        return _g_code(spec, content)
    if gtype == "sql":
        return _g_sql(spec, content)
    if gtype == "checker":
        fn = checkers.REGISTRY[spec["name"]]
        ok, detail = fn(strip_thinking(content), **spec.get("params", {}))
        return _result(ok, strip_thinking(content)[:200], detail)
    if gtype == "agent":
        return envs.grade_agent(task, record)
    raise ValueError(f"unknown grader type {gtype}")
