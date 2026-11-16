#!/usr/bin/env python3
"""Compare two graded runs (e.g. Qwen3.8 vs Qwen4) and write a Markdown report.

    python3 compare.py results/qwen3.8-27b-4bit results/qwen4-27b-4bit
    python3 compare.py results/A results/B --out reports/A_vs_B.md

Reports the weighted-score difference with a paired bootstrap 95% CI over tasks, an exact McNemar test on
tasks that flipped, per-tier / per-category deltas, and the list of flipped tasks.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

from bench import TIER_NAMES
from bench.common import ROOT, load_tasks
from grade import grade_run, weighted


def binom_two_sided(k, n):
    if n == 0:
        return 1.0
    k = min(k, n - k)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_a")
    ap.add_argument("run_b")
    ap.add_argument("--out")
    ap.add_argument("--bootstrap", type=int, default=10000)
    args = ap.parse_args()

    tasks = load_tasks()
    A, B = Path(args.run_a), Path(args.run_b)
    sa, sb = grade_run(A, quiet=True), grade_run(B, quiet=True)
    ra, rb = sa["per_task"], sb["per_task"]
    common = [t for t in tasks if t["id"] in ra and t["id"] in rb]
    if len(common) < len(tasks):
        print(f"note: comparing on {len(common)} tasks attempted by both runs")
    score_a, score_b = weighted(common, ra), weighted(common, rb)
    diff = score_b - score_a

    rng = random.Random(0)
    diffs = []
    for _ in range(args.bootstrap):
        sample = [common[rng.randrange(len(common))] for _ in common]
        diffs.append(weighted(sample, rb) - weighted(sample, ra))
    diffs.sort()
    lo, hi = diffs[int(0.025 * len(diffs))], diffs[int(0.975 * len(diffs)) - 1]
    p_better = sum(d > 0 for d in diffs) / len(diffs)

    won = [t for t in common if rb[t["id"]] >= 0.5 > ra[t["id"]]]
    lost = [t for t in common if ra[t["id"]] >= 0.5 > rb[t["id"]]]
    p_mcnemar = binom_two_sided(len(won), len(won) + len(lost))

    name_a, name_b = A.name, B.name
    md = [f"# {name_a} vs {name_b}", "",
          f"Tasks compared: {len(common)} - samples per task: A={sa['samples_graded'] / max(1, sa['tasks_attempted']):.0f}, "
          f"B={sb['samples_graded'] / max(1, sb['tasks_attempted']):.0f}", "",
          "| | " + name_a + " | " + name_b + " | Delta (B - A) |", "|---|---:|---:|---:|",
          f"| **Weighted score** | **{score_a:.1f}** | **{score_b:.1f}** | **{diff:+.1f}** |",
          f"| Tasks solved | {sum(ra[t['id']] for t in common):.1f} | {sum(rb[t['id']] for t in common):.1f} | "
          f"{sum(rb[t['id']] - ra[t['id']] for t in common):+.1f} |",
          f"| Truncated samples | {sa['truncated_samples']} | {sb['truncated_samples']} | |",
          f"| Mean completion tokens | {sa['mean_completion_tokens']} | {sb['mean_completion_tokens']} | |", "",
          f"Paired bootstrap over tasks ({args.bootstrap} resamples): 95% CI of the score delta "
          f"**[{lo:+.1f}, {hi:+.1f}]**, P(B > A) = {p_better:.3f}.  ",
          f"McNemar exact test on flipped tasks: B-only wins {len(won)}, A-only wins {len(lost)}, p = {p_mcnemar:.3f}.",
          "", "## By tier", "", f"| Tier | {name_a} | {name_b} | Delta |", "|---|---:|---:|---:|"]
    for tier in sorted({t["tier"] for t in common}):
        ts = [t for t in common if t["tier"] == tier]
        a, b = weighted(ts, ra), weighted(ts, rb)
        md.append(f"| {TIER_NAMES[tier]} | {a:.1f} | {b:.1f} | {b - a:+.1f} |")
    md += ["", "## By category", "", f"| Category | {name_a} | {name_b} | Delta |", "|---|---:|---:|---:|"]
    for cat in sorted({t["category"] for t in common}):
        ts = [t for t in common if t["category"] == cat]
        a, b = weighted(ts, ra), weighted(ts, rb)
        md.append(f"| {cat} | {a:.1f} | {b:.1f} | {b - a:+.1f} |")
    md += ["", f"## Tasks only {name_b} solves", ""]
    md += [f"- {t['id']} (T{t['tier']}, {t['category']}): {t['title']}" for t in won] or ["- none"]
    md += ["", f"## Tasks only {name_a} solves (regressions)", ""]
    md += [f"- {t['id']} (T{t['tier']}, {t['category']}): {t['title']}" for t in lost] or ["- none"]
    md += ["", "_A difference is only meaningful if both runs used the same tasks.jsonl, the same quantization "
               "family, the same max_tokens and their recommended sampling settings (see README)._"]

    out = Path(args.out) if args.out else ROOT / "reports" / f"{name_a}_vs_{name_b}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"{name_a}: {score_a:.1f}  {name_b}: {score_b:.1f}  delta {diff:+.1f}  95% CI [{lo:+.1f}, {hi:+.1f}]  -> {out}")
    json.dump({"a": name_a, "b": name_b, "score_a": score_a, "score_b": score_b, "delta": diff, "ci95": [lo, hi],
               "p_b_better": p_better, "mcnemar_p": p_mcnemar, "b_only": [t["id"] for t in won],
               "a_only": [t["id"] for t in lost]}, open(out.with_suffix(".json"), "w"), indent=2)


if __name__ == "__main__":
    main()
