#!/usr/bin/env python3
"""Self-test of the benchmark itself (no model needed).

For every task it checks that:
  1. the reference answer PASSES the grader,
  2. the reference still passes when wrapped after a <think> block that contains a wrong answer,
  3. the known-wrong answer (if any) FAILS,
  4. an empty response FAILS.
Agent tasks are driven through the real episode loop with a scripted "model".

    python3 selftest.py            # all tasks
    python3 selftest.py CODE-10    # selected ids
"""
from __future__ import annotations

import json
import sys
import time

from bench.common import ROOT, load_tasks
from bench.envs import run_episode
from bench.graders import grade


def scripted(script):
    msgs = list(script)

    def respond(_messages):
        return (msgs.pop(0) if msgs else "FINAL ANSWER: (script exhausted)"), "", {}

    return respond


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
        if r.get("wrong") is not None:
            res3 = grade(t, record_for(t, r["wrong"]))
            if res3["passed"]:
                failures.append((t["id"], "WRONG answer passed", res3["detail"]))
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
