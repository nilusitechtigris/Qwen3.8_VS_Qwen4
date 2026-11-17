#!/usr/bin/env python3
"""Grade a run directory produced by run.py.

    python3 grade.py results/qwen3.8-27b-4bit

Writes grades.jsonl, summary.json and summary.md into the run directory.
Score = 100 * sum(weight * pass_rate) / sum(weight), where pass_rate is averaged over samples.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

from bench import TIER_NAMES
from bench.common import TASKS_PATH, WEIGHTS_PATH, load_tasks
from bench.graders import grade


def load_responses(run_dir: Path):
    recs = {}
    with open(run_dir / "responses.jsonl", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            key = (r["id"], r["sample"])
            # keep the latest successful record for each (task, sample)
            if key not in recs or not r.get("error"):
                recs[key] = r
    return recs


def weighted(tasks, rate):
    W = sum(t["weight"] for t in tasks)
    return 100.0 * sum(t["weight"] * rate.get(t["id"], 0.0) for t in tasks) / W if W else 0.0


def grade_run(run_dir: Path, quiet=False):
    run_dir = Path(run_dir)
    tasks = load_tasks()
    meta_path = run_dir / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    sha = hashlib.sha256(TASKS_PATH.read_bytes()).hexdigest()
    if meta.get("tasks_sha256") and meta["tasks_sha256"] != sha:
        print("WARNING: responses were produced with a different tasks.jsonl version", file=sys.stderr)
    recs = load_responses(run_dir)
    by_id = defaultdict(list)
    grades = []
    for (tid, s), rec in sorted(recs.items()):
        task = next((t for t in tasks if t["id"] == tid), None)
        if task is None:
            continue
        g = grade(task, rec)
        usage = rec.get("usage") or {}
        g.update(id=tid, sample=s, tier=task["tier"], weight=task["weight"], category=task["category"],
                 finish_reason=rec.get("finish_reason"), completion_tokens=usage.get("completion_tokens"),
                 error=rec.get("error"))
        grades.append(g)
        by_id[tid].append(g["passed"])
    with open(run_dir / "grades.jsonl", "w", encoding="utf-8") as f:
        for g in grades:
            f.write(json.dumps(g, ensure_ascii=False) + "\n")

    attempted = [t for t in tasks if t["id"] in by_id]
    rate = {tid: sum(v) / len(v) for tid, v in by_id.items()}
    summary = {
        "run": run_dir.name,
        "model": (meta.get("config") or {}).get("model"),
        "tasks_attempted": len(attempted),
        "tasks_total": len(tasks),
        "samples_graded": len(grades),
        "weights": ("tasks/weights.json sha256 " + hashlib.sha256(WEIGHTS_PATH.read_bytes()).hexdigest()
                    if WEIGHTS_PATH.exists() else "tier weights (1-5)"),
        "weighted_score": round(weighted(tasks, rate), 2),
        "weighted_score_attempted_only": round(weighted(attempted, rate), 2) if attempted else 0.0,
        "tasks_solved": round(sum(rate.values()), 2),
        "truncated_samples": sum(1 for g in grades if g["finish_reason"] == "length"),
        "error_samples": sum(1 for g in grades if g["error"]),
        "mean_completion_tokens": round(sum(g["completion_tokens"] or 0 for g in grades) / max(1, len(grades))),
        "by_tier": {}, "by_category": {}, "per_task": rate,
    }
    for tier in sorted({t["tier"] for t in tasks}):
        ts = [t for t in tasks if t["tier"] == tier]
        summary["by_tier"][str(tier)] = {"tasks": len(ts), "solved": round(sum(rate.get(t["id"], 0) for t in ts), 2),
                                         "score": round(weighted(ts, rate), 1)}
    for cat in sorted({t["category"] for t in tasks}):
        ts = [t for t in tasks if t["category"] == cat]
        summary["by_category"][cat] = {"tasks": len(ts), "solved": round(sum(rate.get(t["id"], 0) for t in ts), 2),
                                       "score": round(weighted(ts, rate), 1)}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    md = [f"# {run_dir.name}", "",
          f"- Model: `{summary['model']}`",
          f"- **Weighted score: {summary['weighted_score']:.1f} / 100** (tasks attempted: {len(attempted)}/{len(tasks)})",
          f"- Tasks solved: {summary['tasks_solved']} / {len(tasks)}",
          f"- Weights: {summary['weights']}",
          f"- Truncated samples (finish_reason=length): {summary['truncated_samples']}; request errors: {summary['error_samples']}",
          f"- Mean completion tokens per sample: {summary['mean_completion_tokens']}", "",
          "| Tier | Tasks | Solved | Score |", "|---|---:|---:|---:|"]
    for tier, v in summary["by_tier"].items():
        md.append(f"| {TIER_NAMES[int(tier)]} | {v['tasks']} | {v['solved']} | {v['score']} |")
    md += ["", "| Category | Tasks | Solved | Score |", "|---|---:|---:|---:|"]
    for cat, v in summary["by_category"].items():
        md.append(f"| {cat} | {v['tasks']} | {v['solved']} | {v['score']} |")
    md += ["", "## Failed samples", "", "| Task | Sample | Detail |", "|---|---:|---|"]
    for g in grades:
        if not g["passed"]:
            md.append(f"| {g['id']} | {g['sample']} | {str(g['detail'])[:140].replace('|', '/').replace(chr(10), ' ')} |")
    (run_dir / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    if not quiet:
        print(f"{run_dir.name}: weighted score {summary['weighted_score']:.1f} / 100, "
              f"solved {summary['tasks_solved']} / {len(tasks)}, truncated {summary['truncated_samples']}, "
              f"errors {summary['error_samples']}  -> {run_dir / 'summary.md'}")
    return summary


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    for d in sys.argv[1:]:
        grade_run(Path(d))
