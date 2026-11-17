#!/usr/bin/env python3
"""Self-test of the benchmark itself (no model needed).

For every task it checks that:
  1. the reference answer PASSES the grader,
  2. the reference still passes when wrapped after a <think> block that contains a wrong answer,
  3. the known-wrong answer (if any) FAILS,
  4. an empty response FAILS,
  5. for FINAL-ANSWER tasks, the reference answer still passes in the formats real models use
     (bold marker or value, "Final Answer:", heading, next line, $...$, \\boxed{}, backticks, trailing period, ...),
  6. for exact-match tasks, a trailing clarification "X (Y)" still passes but a hedge "X (or Y)" fails.
Agent tasks are driven through the real episode loop with a scripted "model", and the loop's output-token budget
is checked with a "model" that never stops thinking.

    python3 selftest.py            # all tasks
    python3 selftest.py CODE-10    # selected ids
"""
from __future__ import annotations

import json
import sys
import time

from bench.common import ROOT, load_tasks
from bench.envs import EPISODE_TOKEN_BUDGET, run_episode
from bench.graders import grade


def scripted(script):
    msgs = list(script)

    def respond(_messages):
        return (msgs.pop(0) if msgs else "FINAL ANSWER: (script exhausted)"), "", {}

    return respond


# How real models format the last line. Every variant must still be graded as the reference answer.
FORMAT_VARIANTS = {
    "bold value": "FINAL ANSWER: **{a}**",
    "bold marker": "**FINAL ANSWER:** {a}",
    "bold marker, colon outside": "**FINAL ANSWER**: {a}",
    "bold line": "**FINAL ANSWER: {a}**",
    "title case marker": "Final Answer: {a}",
    "markdown heading": "### FINAL ANSWER: {a}",
    "answer on next line": "FINAL ANSWER:\n{a}",
    "inline latex": "FINAL ANSWER: ${a}$",
    "boxed": "FINAL ANSWER: $\\boxed{{{a}}}$",
    "trailing period": "FINAL ANSWER: {a}.",
    "backticks": "FINAL ANSWER: `{a}`",
    "capitalised": "FINAL ANSWER: {A}",
    "Turkish capital I": "FINAL ANSWER: {T}",
}


def format_variants(reference):
    """Yield (name, text) re-formattings of a single-line FINAL ANSWER reference."""
    body, sep, answer = reference.rpartition("FINAL ANSWER:")
    answer = answer.strip()
    if not sep or "\n" in answer:
        return
    cap = answer[:1].upper() + answer[1:]
    turkish = ("\u0130" + answer[1:]) if answer[:1] == "i" else cap
    for name, tpl in FORMAT_VARIANTS.items():
        yield name, body + tpl.format(a=answer, A=cap, T=turkish)


def check_token_budget(task):
    """A model that hits max_tokens on every turn must be stopped once the episode budget is spent."""
    per_turn = 32768

    def respond(_messages):
        return "", "thinking " * 10, {"completion_tokens": per_turn}

    rec = run_episode(task, respond)
    expected_turns = -(-EPISODE_TOKEN_BUDGET // per_turn)
    if rec["stopped"] != "token_budget" or rec["turns"] != expected_turns:
        return f"expected stop after {expected_turns} turns on the token budget, got {rec['turns']} turns ({rec['stopped']})"
    return None


def record_for(task, ref):
    if task["mode"] == "agent":
        return run_episode(task, scripted(ref["script"]))
    return {"content": ref}


def main(argv):
    tasks = load_tasks()
    refs = {}
    with open(ROOT / "tasks" / "selftest_refs.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            refs[r["id"]] = r
    if argv:
        tasks = [t for t in tasks if t["id"] in argv]
    failures = []
    t0 = time.time()
    for t in tasks:
        r = refs[t["id"]]
        res = grade(t, record_for(t, r["reference"]))
        if not res["passed"]:
            failures.append((t["id"], "reference failed", res["detail"]))
        if t["mode"] != "agent":
            wrapped = "<think>Maybe the answer is 0.\nFINAL ANSWER: 0\n```python\nx=1\n```</think>\n" + r["reference"]
            res2 = grade(t, {"content": wrapped})
            if not res2["passed"]:
                failures.append((t["id"], "reference after <think> failed", res2["detail"]))
        if t["mode"] == "final":
            for name, text in format_variants(r["reference"]):
                res_v = grade(t, {"content": text})
                if not res_v["passed"]:
                    failures.append((t["id"], f"reference in format '{name}' failed", res_v["detail"]))
        if t["grader"]["type"] == "exact":
            body, sep, answer = r["reference"].rpartition("FINAL ANSWER:")
            if sep and "\n" not in answer.strip():
                if not grade(t, {"content": f"{body}FINAL ANSWER: {answer.strip()} (as derived above)"})["passed"]:
                    failures.append((t["id"], "reference with a parenthetical clarification failed", ""))
                if grade(t, {"content": f"{body}FINAL ANSWER: zzz (or {answer.strip()})"})["passed"]:
                    failures.append((t["id"], "hedged answer 'zzz (or <reference>)' passed", ""))
                if grade(t, {"content": f"{body}FINAL ANSWER: {answer.strip()} (or zzz)"})["passed"]:
                    failures.append((t["id"], "hedged answer '<reference> (or zzz)' passed", ""))
        if r.get("wrong") is not None:
            res3 = grade(t, record_for(t, r["wrong"]))
            if res3["passed"]:
                failures.append((t["id"], "WRONG answer passed", res3["detail"]))
        if t["mode"] == "agent":
            problem = check_token_budget(t)
            if problem:
                failures.append((t["id"], "episode token budget", problem))
        empty = {"script": []} if t["mode"] == "agent" else ""
        if grade(t, record_for(t, empty))["passed"]:
            failures.append((t["id"], "empty response passed", ""))
        print(f"{t['id']:<10} ok" if not any(f[0] == t["id"] for f in failures) else f"{t['id']:<10} FAIL")
    print(f"\n{len(tasks)} tasks checked in {time.time() - t0:.1f}s, {len(failures)} problem(s)")
    for f in failures:
        print("  -", *f)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
