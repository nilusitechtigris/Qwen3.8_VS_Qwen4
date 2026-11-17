#!/usr/bin/env python3
"""Audit a run's grading by hand: what was extracted vs. what was expected, task by task.

    python3 tools/audit_run.py results/qwen3.8-27b-nvfp4-ollama            # one line per sample
    python3 tools/audit_run.py results/qwen3.8-27b-nvfp4-ollama --failed   # failures only, with the reply's tail
    python3 tools/audit_run.py results/qwen3.8-27b-nvfp4-ollama --only LONG-01 --full

Use it after every run, before trusting the score: for each failure, decide whether the model was really wrong or
the task / grader is at fault (ambiguous prompt, accepted-answer list too narrow, format not recognised).
Grading is re-done from the stored raw responses, so fixing a grader never requires re-running the model.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from bench.common import load_tasks, strip_thinking  # noqa: E402
from bench.graders import grade  # noqa: E402


def expected(task):
    g = task["grader"]
    for key in ("value", "answers", "items", "pattern"):
        if key in g:
            return g[key]
    return g["type"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--failed", action="store_true", help="show failures only, with the tail of the visible reply")
    ap.add_argument("--only", help="comma-separated task ids")
    ap.add_argument("--full", action="store_true", help="print the whole visible reply (and reasoning length)")
    ap.add_argument("--tail", type=int, default=600, help="characters of the reply tail to show for failures")
    args = ap.parse_args()

    tasks = {t["id"]: t for t in load_tasks()}
    only = {x.strip() for x in args.only.split(",")} if args.only else None
    n = n_pass = 0
    with open(Path(args.run_dir) / "responses.jsonl", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if only and r["id"] not in only:
                continue
            t = tasks[r["id"]]
            g = grade(t, r)
            n += 1
            n_pass += g["passed"]
            if args.failed and g["passed"]:
                continue
            usage = r.get("usage") or {}
            status = "PASS" if g["passed"] else "FAIL"
            print(f"{status} {r['id']}#{r['sample']} T{t['tier']} est_p={t['est_p']:.2f} finish={r.get('finish_reason')} "
                  f"tokens={usage.get('completion_tokens')} err={r.get('error')!r}")
            extracted = g["extracted"]
            if isinstance(extracted, str) and len(extracted) > 160:
                extracted = extracted[:160] + "..."
            print(f"     extracted: {extracted!r}")
            print(f"     expected:  {str(expected(t))[:160]}")
            if g.get("detail"):
                print(f"     detail:    {g['detail'][:300]}")
            if not g["passed"] or args.full:
                visible = strip_thinking(r.get("content") or "")
                if t["mode"] == "agent":
                    visible = "\n".join(str(m.get("content", ""))[-300:] for m in (r.get("transcript") or [])[-4:])
                shown = visible if args.full else visible[-args.tail:]
                print("     reply" + ("" if args.full else " (tail)") + ":\n       " + shown.replace("\n", "\n       "))
                if args.full:
                    print(f"     reasoning: {len(r.get('reasoning') or '')} chars")
            print()
    print(f"{n_pass}/{n} samples passed")


if __name__ == "__main__":
    main()
