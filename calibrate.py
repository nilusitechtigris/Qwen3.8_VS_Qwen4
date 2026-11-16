#!/usr/bin/env python3
"""Calibration helper.

    python3 calibrate.py                          # show the prior (expected Qwen3.8 score from est_p)
    python3 calibrate.py results/qwen3.8-27b-4bit # compare a pilot run against the prior

Use it on a Qwen3.8 pilot run BEFORE Qwen4 is released: if the observed score is far from 50, retune tiers or
est_p in build/cat_*.py, rebuild, and only then freeze tasks.jsonl (its sha256 is recorded in every run).
"""
from __future__ import annotations

import sys
from pathlib import Path

from bench import TIER_NAMES
from bench.common import load_tasks
from grade import grade_run, weighted


def main():
    tasks = load_tasks()
    prior = {t["id"]: t["est_p"] for t in tasks}
    print(f"Prior expected weighted score: {weighted(tasks, prior):.1f}  (expected solved {sum(prior.values()):.1f})")
    if len(sys.argv) < 2:
        for tier in range(1, 6):
            ts = [t for t in tasks if t["tier"] == tier]
            print(f"  {TIER_NAMES[tier]:<14} {len(ts):>3} tasks  mean est_p {sum(prior[t['id']] for t in ts) / len(ts):.2f}")
        return
    s = grade_run(Path(sys.argv[1]), quiet=True)
    obs = s["per_task"]
    done = [t for t in tasks if t["id"] in obs]
    print(f"Observed weighted score: {weighted(done, obs):.1f} on {len(done)} tasks "
          f"(prior on the same tasks: {weighted(done, prior):.1f})\n")
    print(f"{'Tier':<14} {'prior':>6} {'observed':>9}")
    for tier in range(1, 6):
        ts = [t for t in done if t["tier"] == tier]
        if ts:
            print(f"{TIER_NAMES[tier]:<14} {sum(prior[t['id']] for t in ts) / len(ts):>6.2f} "
                  f"{sum(obs[t['id']] for t in ts) / len(ts):>9.2f}")
    surprises_fail = [t for t in done if prior[t["id"]] >= 0.8 and obs[t["id"]] < 0.5]
    surprises_pass = [t for t in done if prior[t["id"]] <= 0.25 and obs[t["id"]] >= 0.5]
    if surprises_fail:
        print("\nExpected-easy tasks that FAILED (check the transcript: truncation? grader too strict?):")
        for t in surprises_fail:
            print(f"  {t['id']} T{t['tier']} est_p={prior[t['id']]:.2f}  {t['title']}")
    if surprises_pass:
        print("\nExpected-hard tasks that PASSED (candidates to move down a tier if the score is too high):")
        for t in surprises_pass:
            print(f"  {t['id']} T{t['tier']} est_p={prior[t['id']]:.2f}  {t['title']}")
    score = weighted(done, obs)
    if score > 55:
        print("\nScore is above 55: consider making a few T3/T4 tasks harder or raising tiers of failed-hard tasks.")
    elif score < 45:
        print("\nScore is below 45: consider simplifying a few T4/T5 tasks or lowering their tiers.")
    else:
        print("\nScore is within 45-55: calibration target met. Freeze tasks.jsonl now.")


if __name__ == "__main__":
    main()
