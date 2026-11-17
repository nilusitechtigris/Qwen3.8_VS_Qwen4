"""Shared text utilities: thinking removal, answer extraction, normalisation, number parsing."""
from __future__ import annotations

import json
import re
import unicodedata
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS_PATH = ROOT / "tasks" / "tasks.jsonl"
# Calibrated scoring weights (tools/calibrate_weights.py). Kept outside tasks.jsonl so the task file and its sha256
# do not change; when present, every task's "weight" is taken from here and the tier weight moves to "tier_weight".
WEIGHTS_PATH = ROOT / "tasks" / "weights.json"

_THINK_BLOCK = re.compile(r"<think>.*?</think>", re.S | re.I)
_FINAL = re.compile(r"FINAL\s*ANSWER\s*[*_`]*\s*[:：]", re.I)  # also "**FINAL ANSWER**: x"
_BOXED = re.compile(r"\\boxed\{")


def load_tasks(path: Path | str = TASKS_PATH, calibrated_weights: bool = True) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        tasks = [json.loads(line) for line in f if line.strip()]
    if calibrated_weights and Path(path) == TASKS_PATH and WEIGHTS_PATH.exists():
        weights = json.loads(WEIGHTS_PATH.read_text(encoding="utf-8"))["weights"]
        missing = [t["id"] for t in tasks if t["id"] not in weights]
        if missing:
            raise ValueError(f"{WEIGHTS_PATH} has no weight for {missing}")
        for t in tasks:
            t["tier_weight"], t["weight"] = t["weight"], weights[t["id"]]
    return tasks


def strip_thinking(text: str | None) -> str:
    """Remove <think>...</think> blocks. An unterminated <think> means no visible answer."""
    if not text:
        return ""
    text = _THINK_BLOCK.sub("", text)
    if re.search(r"</think>", text, re.I):
        text = re.split(r"</think>", text, flags=re.I)[-1]
    if re.search(r"<think>", text, re.I):
        text = re.split(r"<think>", text, flags=re.I)[0]
    return text.strip()


def _boxed_contents(text: str) -> list[str]:
    out = []
    for m in _BOXED.finditer(text):
        i, depth, start = m.end(), 1, m.end()
        while i < len(text) and depth:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        if depth == 0:
            out.append(text[start:i - 1])
    return out


def clean_answer(ans: str) -> str:
    ans = ans.strip()
    boxed = _boxed_contents(ans)
    if boxed:
        ans = boxed[-1]
    ans = ans.strip()
    # strip markdown / latex wrappers
    for _ in range(3):
        ans = ans.strip()
        if ans.endswith(("`.", "*.", "$.")):  # sentence period after a closing wrapper is never part of the answer
            ans = ans[:-1]
        ans = ans.strip("*").strip("`").strip()
        if len(ans) >= 2 and ans[0] == ans[-1] and ans[0] in "\"'$":
            ans = ans[1:-1]
        if ans.startswith("\\(") and ans.endswith("\\)"):
            ans = ans[2:-2]
        if ans.startswith("\\[") and ans.endswith("\\]"):
            ans = ans[2:-2]
    ans = re.sub(r"\\text\{([^}]*)\}", r"\1", ans)
    ans = ans.strip()
    if ans.endswith("."):
        ans = ans[:-1]
    return ans.strip()


def extract_final(text: str | None) -> str | None:
    """Return the content after the LAST 'FINAL ANSWER:' marker (same line, or the next
    non-empty line if the marker line is empty). Falls back to the last \\boxed{}."""
    visible = strip_thinking(text)
    matches = list(_FINAL.finditer(visible))
    if matches:
        rest = visible[matches[-1].end():]
        lines = rest.split("\n")
        first = lines[0].strip()
        if first:
            return clean_answer(first)
        for ln in lines[1:]:
            if ln.strip() and not ln.strip().startswith("```"):
                return clean_answer(ln)
        return ""
    boxed = _boxed_contents(visible)
    if boxed:
        return clean_answer(boxed[-1])
    return None


def norm_text(s: str, *, keep_case: bool = False, remove_spaces: bool = False) -> str:
    s = unicodedata.normalize("NFC", s)
    if not keep_case:
        s = s.replace("\u0130", "i").lower()  # Turkish capital İ: str.lower() would give "i" + combining dot
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    s = re.sub(r"\s+", " ", s).strip()
    s = s.strip(" .;:!\"'`*")
    if remove_spaces:
        s = s.replace(" ", "")
    return s


_LATEX_FRAC = re.compile(r"\\[dt]?frac\{([^{}]+)\}\{([^{}]+)\}")


def parse_number(s: str | None):
    """Parse an int / decimal / fraction / scientific string into Fraction (exact) if possible.
    Returns None when the string does not look like a single number."""
    if s is None:
        return None
    t = s.strip()
    t = _LATEX_FRAC.sub(r"(\1)/(\2)", t)
    t = t.replace("\u2212", "-").replace("\u2013", "-").replace("−", "-")
    t = t.replace("\\,", "").replace("\\!", "").replace("{,}", "")
    t = re.sub(r"(?<=\d)[,_ ](?=\d{3}\b)", "", t)  # thousands separators
    t = re.sub(r"(?<=\d)[,_ ](?=\d{3}\b)", "", t)
    t = t.replace("\\times10^", "e").replace("×10^", "e").replace("x10^", "e")
    t = re.sub(r"e\{(-?\d+)\}", r"e\1", t)
    # strip trailing units / words
    m = re.match(r"^\s*\(?\s*([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s*\)?\s*(?:/\s*\(?\s*([-+]?\d+(?:\.\d+)?)\s*\)?)?", t)
    if not m:
        m2 = re.match(r"^\s*([-+]?\.\d+)", t)
        if not m2:
            return None
        return Fraction(m2.group(1))
    try:
        num = Fraction(m.group(1))
        if m.group(2):
            den = Fraction(m.group(2))
            if den == 0:
                return None
            return num / den
        return num
    except (ValueError, ZeroDivisionError):
        return None


def words(text: str) -> list[str]:
    """A word = whitespace-separated token containing at least one letter or digit."""
    return [t for t in text.split() if re.search(r"[^\W_]", t)]


def sentences(text: str) -> list[str]:
    """A sentence = maximal run of text ending with one or more of . ! ?"""
    parts = re.findall(r"[^.!?]+[.!?]+", text.replace("\n", " "))
    return [p.strip() for p in parts if words(p)]
