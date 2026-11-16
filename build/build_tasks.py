"""Assemble all categories into tasks/tasks.jsonl (+ references for the self-test, an index and a checksum).

    python3 build/build_tasks.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

import cat_agent  # noqa: E402
import cat_code  # noqa: E402
import cat_if  # noqa: E402
import cat_know  # noqa: E402
import cat_logic  # noqa: E402
import cat_long  # noqa: E402
import cat_math  # noqa: E402
import cat_sci_lang  # noqa: E402
import cat_struct  # noqa: E402
import cat_trace  # noqa: E402

FINAL_SUFFIX = "\n\nThink it through, then end your response with a line of the form:\nFINAL ANSWER: <answer>"
BENCH_VERSION = "1.0.0"


def collect():
    tasks = []
    for mod in (cat_math, cat_logic, cat_code, cat_if, cat_know, cat_long, cat_trace, cat_agent, cat_struct,
                cat_sci_lang):
        tasks += mod.tasks()
    ids = [t["id"] for t in tasks]
    assert len(ids) == len(set(ids)), [i for i, c in Counter(ids).items() if c > 1]
    assert len(tasks) == 100, len(tasks)
    for t in tasks:
        if t["mode"] == "final":
            t["prompt"] += FINAL_SUFFIX
    return tasks


def expected_score(tasks):
    W = sum(t["weight"] for t in tasks)
    E = sum(t["weight"] * t["est_p"] for t in tasks)
    return 100 * E / W, sum(t["est_p"] for t in tasks), W


def main():
    tasks = collect()
    out_dir = ROOT / "tasks"
    out_dir.mkdir(exist_ok=True)
    public_keys = ["id", "category", "tier", "weight", "title", "mode", "skills", "est_p", "prompt", "grader", "notes"]
    with open(out_dir / "tasks.jsonl", "w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps({k: t[k] for k in public_keys}, ensure_ascii=False) + "\n")
    with open(out_dir / "selftest_refs.jsonl", "w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps({"id": t["id"], "reference": t["reference"], "wrong": t["wrong"]},
                               ensure_ascii=False) + "\n")
    digest = hashlib.sha256((out_dir / "tasks.jsonl").read_bytes()).hexdigest()
    (out_dir / "tasks.sha256").write_text(f"{digest}  tasks.jsonl\n")

    score, exp_count, W = expected_score(tasks)
    by_tier = defaultdict(list)
    by_cat = defaultdict(list)
    for t in tasks:
        by_tier[t["tier"]].append(t)
        by_cat[t["category"]].append(t)

    lines = ["# Task index", "",
             f"Benchmark version {BENCH_VERSION} - 100 tasks - total weight {W} points - tasks.jsonl sha256 `{digest[:16]}...`",
             "", "Answers live in `tasks.jsonl` (grader specs). This index intentionally lists no answers.", "",
             "## Calibration prior (Qwen3.8-27B 4-bit, thinking on)", "",
             f"Expected weighted score: **{score:.1f} / 100** - expected tasks solved: {exp_count:.1f} / 100", "",
             "| Tier | Weight | Tasks | Points | Mean est. pass rate | Expected points |",
             "|---|---:|---:|---:|---:|---:|"]
    names = {1: "T1 warm-up", 2: "T2 standard", 3: "T3 hard", 4: "T4 very hard", 5: "T5 frontier"}
    for tier in sorted(by_tier):
        ts = by_tier[tier]
        pts = sum(t["weight"] for t in ts)
        ep = sum(t["weight"] * t["est_p"] for t in ts)
        lines.append(f"| {names[tier]} | {tier} | {len(ts)} | {pts} | {sum(t['est_p'] for t in ts) / len(ts):.2f} | {ep:.1f} |")
    lines += ["", "| Category | Tasks | Points | Expected points | Expected % |", "|---|---:|---:|---:|---:|"]
    for cat, ts in sorted(by_cat.items()):
        pts = sum(t["weight"] for t in ts)
        ep = sum(t["weight"] * t["est_p"] for t in ts)
        lines.append(f"| {cat} | {len(ts)} | {pts} | {ep:.1f} | {100 * ep / pts:.0f}% |")
    lines += ["", "## Tasks", "", "| ID | Category | Tier | Weight | Est. pass (Qwen3.8) | Mode | Title |",
              "|---|---|---:|---:|---:|---|---|"]
    for t in tasks:
        lines.append(f"| {t['id']} | {t['category']} | {t['tier']} | {t['weight']} | {t['est_p']:.2f} | {t['mode']} | {t['title']} |")
    (out_dir / "TASKS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"wrote {len(tasks)} tasks, total weight {W}, sha256 {digest[:16]}")
    print(f"expected weighted score for Qwen3.8 prior: {score:.1f}  (expected solved: {exp_count:.1f})")
    for tier in sorted(by_tier):
        print(f"  tier {tier}: {len(by_tier[tier])} tasks")
    size = (out_dir / "tasks.jsonl").stat().st_size
    print(f"tasks.jsonl size: {size / 1024:.0f} KiB")


if __name__ == "__main__":
    main()
