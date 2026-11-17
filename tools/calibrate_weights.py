#!/usr/bin/env python3
"""Derive scoring weights from a Qwen3.8 pilot run so that the pilot scores exactly --target (default 50).

    python3 tools/calibrate_weights.py results/qwen3.8-27b-nvfp4-ollama           # dry run: show the result
    python3 tools/calibrate_weights.py results/qwen3.8-27b-nvfp4-ollama --write   # write tasks/weights.json

Rule: a task's weight is its tier (1-5) if the pilot passed it, and tier x F if the pilot failed it, with a single
factor F >= 1 chosen so that the pilot's weighted score equals the target. With several samples per task, a task
with pass rate r gets tier x (1 + (F - 1) x (1 - r)). tasks.jsonl is not changed; load_tasks() applies the weights.

Caveat: the weights are fitted to one pilot. Tasks the pilot failed by bad luck carry extra weight, so a fresh run of
the same model will usually score a little above the target. Compare Qwen4 with a fresh Qwen3.8 run scored with the
same weights, not with the calibration run itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from bench.common import TASKS_PATH, WEIGHTS_PATH, load_tasks  # noqa: E402
from bench.graders import grade  # noqa: E402
from grade import load_responses  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--target", type=float, default=50.0, help="weighted score the pilot should get (default 50)")
    ap.add_argument("--write", action="store_true", help=f"write {WEIGHTS_PATH.relative_to(ROOT)}")
    args = ap.parse_args()

    tasks = load_tasks(calibrated_weights=False)  # tier weights
    by_id = {}
    for (tid, _s), rec in load_responses(Path(args.run_dir)).items():
        task = next((t for t in tasks if t["id"] == tid), None)
        if task is not None and not rec.get("error"):
            by_id.setdefault(tid, []).append(grade(task, rec)["passed"])
    missing = [t["id"] for t in tasks if t["id"] not in by_id]
    if missing:
        sys.exit(f"the run has no graded response for {len(missing)} task(s): {missing[:10]}")
    rate = {tid: sum(v) / len(v) for tid, v in by_id.items()}

    t = args.target / 100
    a = {x["id"]: x["weight"] for x in tasks}
    sum_a = sum(a.values())
    sum_ar = sum(a[i] * rate[i] for i in a)
    sum_af = sum(a[i] * (1 - rate[i]) for i in a)
    sum_afr = sum(a[i] * (1 - rate[i]) * rate[i] for i in a)
    score_before = 100 * sum_ar / sum_a
    if score_before <= args.target:
        sys.exit(f"the pilot scores {score_before:.2f} with tier weights, already at or below the target")
    factor = 1 + (sum_ar - t * sum_a) / (t * sum_af - sum_afr)
    weights = {i: round(a[i] * (1 + (factor - 1) * (1 - rate[i])), 4) for i in a}
    score_after = 100 * sum(weights[i] * rate[i] for i in a) / sum(weights.values())

    print(f"pilot: {sum(rate.values()):.0f}/{len(a)} solved, {score_before:.2f} with tier weights")
    print(f"factor F = {factor:.4f} for failed tasks -> pilot scores {score_after:.2f}")
    print(f"total weight {sum(weights.values()):.1f}; failed tasks carry {sum(weights[i] for i in a if rate[i] < 1):.1f}")
    if args.write:
        out = {
            "method": "tier weight, multiplied by F for tasks the pilot failed (tools/calibrate_weights.py)",
            "target": args.target,
            "factor": round(factor, 6),
            "source_run": Path(args.run_dir).name,
            "tasks_sha256": hashlib.sha256(TASKS_PATH.read_bytes()).hexdigest(),
            "created": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "weights": weights,
        }
        WEIGHTS_PATH.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {WEIGHTS_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
