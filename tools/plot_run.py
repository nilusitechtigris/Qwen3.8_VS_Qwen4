#!/usr/bin/env python3
"""Draw the result charts for one graded run (plain SVG, no dependencies).

    python3 tools/plot_run.py results/qwen3.8-27b-nvfp4-ollama
    python3 tools/plot_run.py results/<run> --out some/dir --title "Qwen4-27B"

Reads grades.jsonl (run grade.py first) and writes into <run>/charts/:
    score.svg        headline score and where the weight was lost
    by_tier.svg      outcome per difficulty tier
    by_category.svg  outcome per category
    task_map.svg     every task, coloured by outcome, labelled with its tier
    tokens.svg       completion tokens per task (log scale) against the max_tokens limit

Every task ends in one of three outcomes: passed, wrong answer (the model answered and was wrong), or truncated
(finish_reason=length: it ran out of tokens before answering). The SVGs carry their own light and dark colours and
follow the viewer's colour scheme.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from bench import TIER_NAMES  # noqa: E402
from bench.common import load_tasks  # noqa: E402

OUTCOMES = ["passed", "wrong", "truncated"]
OUTCOME_LABEL = {"passed": "Passed", "wrong": "Wrong answer", "truncated": "Truncated (hit the token limit)"}

# Categorical slots 1-3 of the reference palette (validated all-pairs in both modes); chrome and ink tokens.
STYLE = """
<style>
  svg { --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781; --grid:#e1e0d9; --axis:#c3c2b7;
        --passed:#2a78d6; --wrong:#eb6834; --truncated:#1baf7a; }
  @media (prefers-color-scheme: dark) {
    svg { --surface:#1a1a19; --ink:#f0efec; --ink2:#c3c2b7; --muted:#898781; --grid:#2c2c2a; --axis:#383835;
          --passed:#3987e5; --wrong:#d95926; --truncated:#199e70; }
  }
  text { font-family: system-ui, -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; fill: var(--ink); }
  .t { font-size: 17px; font-weight: 600; }
  .s { font-size: 12.5px; fill: var(--ink2); }
  .l { font-size: 13px; }
  .m { font-size: 12px; fill: var(--muted); }
  .v { font-size: 12.5px; fill: var(--ink2); font-variant-numeric: tabular-nums; }
  .in { font-size: 12px; font-weight: 600; fill: #ffffff; }
  .hero { font-size: 60px; font-weight: 600; }
  .tile { font-size: 22px; font-weight: 600; }
  .bg { fill: var(--surface); }
  .grid { stroke: var(--grid); stroke-width: 1; }
  .axis { stroke: var(--axis); stroke-width: 1; }
  .passed { fill: var(--passed); } .wrong { fill: var(--wrong); } .truncated { fill: var(--truncated); }
  .ring { stroke: var(--surface); stroke-width: 2; }
</style>
"""


def text_w(s: str, size: float) -> float:
    """Rough rendered width of a system-ui string."""
    return sum(0.33 if c in " .,:;|il1()'" else 0.62 if c.isupper() or c.isdigit() else 0.54 for c in s) * size


def svg(width, height, body, title, desc):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="ti de">\n'
            f'<title id="ti">{escape(title)}</title>\n<desc id="de">{escape(desc)}</desc>\n{STYLE}'
            f'<rect class="bg" x="0" y="0" width="{width}" height="{height}" rx="10"/>\n' + "\n".join(body) + "\n</svg>\n")


def t(x, y, s, cls="l", anchor="start", extra=""):
    return f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}"{extra}>{escape(str(s))}</text>'


def bar(x, y, w, h, cls, round_right=False, round_left=False, r=4):
    """A rectangle with 4px rounding only on the requested ends (square at the baseline)."""
    if w <= 0:
        return ""
    r = min(r, w / 2, h / 2)
    rl, rr = (r if round_left else 0), (r if round_right else 0)
    d = (f"M{x + rl:.2f},{y:.2f} H{x + w - rr:.2f} " + (f"A{rr},{rr} 0 0 1 {x + w:.2f},{y + rr:.2f} " if rr else "")
         + f"V{y + h - rr:.2f} " + (f"A{rr},{rr} 0 0 1 {x + w - rr:.2f},{y + h:.2f} " if rr else "")
         + f"H{x + rl:.2f} " + (f"A{rl},{rl} 0 0 1 {x:.2f},{y + h - rl:.2f} " if rl else "")
         + f"V{y + rl:.2f} " + (f"A{rl},{rl} 0 0 1 {x + rl:.2f},{y:.2f} " if rl else "") + "Z")
    return f'<path class="{cls}" d="{d}"/>'


def legend(x, y, items, counts=None):
    out, cx = [], x
    for key in items:
        label = OUTCOME_LABEL[key] + (f" ({counts[key]})" if counts else "")
        out.append(f'<rect class="{key}" x="{cx:.1f}" y="{y - 10:.1f}" width="12" height="12" rx="3"/>')
        out.append(t(cx + 18, y, label, "l"))
        cx += 18 + text_w(label, 13) + 22
    return out


def load(run_dir: Path):
    tasks = {t["id"]: t for t in load_tasks()}
    grades = [json.loads(line) for line in open(run_dir / "grades.jsonl", encoding="utf-8") if line.strip()]
    rows = {}
    for g in grades:  # one row per task; with several samples, outcome = majority, tokens = mean
        rows.setdefault(g["id"], []).append(g)
    out = []
    for tid, gs in rows.items():
        task = tasks[tid]
        passed = sum(g["passed"] for g in gs) / len(gs)
        trunc = sum(g.get("finish_reason") == "length" for g in gs if not g["passed"])
        outcome = "passed" if passed >= 0.5 else ("truncated" if trunc * 2 >= sum(not g["passed"] for g in gs) else "wrong")
        toks = [g.get("completion_tokens") for g in gs if isinstance(g.get("completion_tokens"), int)]
        out.append({"id": tid, "tier": task["tier"], "category": task["category"], "weight": task["weight"],
                    "title": task["title"], "mode": task["mode"], "pass_rate": passed, "outcome": outcome,
                    "tokens": sum(toks) / len(toks) if toks else None})
    out.sort(key=lambda r: (r["category"], r["id"]))
    return out


def stacked_rows(rows, groups, label_of, sub_of, title, subtitle, desc):
    """100% stacked horizontal bars, one per group, segments in OUTCOMES order."""
    W, left, right = 780, 170, 120
    plot_w = W - left - right
    top, row_h, bar_h = 92, 38, 22
    H = top + row_h * len(groups) + 40
    body = [t(24, 34, title, "t"), t(24, 54, subtitle, "s")]
    counts = {k: sum(r["outcome"] == k for r in rows) for k in OUTCOMES}
    body += legend(24, 80, OUTCOMES, counts)
    for frac in (0, 0.25, 0.5, 0.75, 1.0):
        x = left + frac * plot_w
        body.append(f'<line class="{"axis" if frac == 0 else "grid"}" x1="{x:.1f}" y1="{top - 6}" x2="{x:.1f}" '
                    f'y2="{top + row_h * len(groups) - 10}"/>')
        body.append(t(x, top + row_h * len(groups) + 6, f"{int(frac * 100)}%", "m", "middle"))
    for i, (key, members) in enumerate(groups):
        y = top + i * row_h
        n = len(members)
        c = {k: sum(r["outcome"] == k for r in members) for k in OUTCOMES}
        body.append(t(left - 12, y + bar_h / 2 + 1, label_of(key), "l", "end"))
        sub = sub_of(key, members)
        if sub:
            body.append(t(left - 12, y + bar_h / 2 + 14, sub, "m", "end"))
        x = left
        segs = [(k, c[k]) for k in OUTCOMES if c[k]]
        for j, (k, cnt) in enumerate(segs):
            w = plot_w * cnt / n
            last = j == len(segs) - 1
            gap = 0 if last else 2
            body.append(bar(x, y, w - gap, bar_h, k, round_right=last))
            if text_w(str(cnt), 12) + 12 <= w - gap:
                body.append(t(x + 7, y + bar_h / 2 + 4.5, cnt, "in"))
            x += w
        rate = c["passed"] / n
        body.append(t(left + plot_w + 12, y + bar_h / 2 + 4.5, f"{rate * 100:.0f}%  ·  {c['passed']}/{n}", "v"))
    return svg(W, H, body, title, desc)


def chart_by_tier(rows, name):
    groups = [(tier, [r for r in rows if r["tier"] == tier]) for tier in range(1, 6)]
    groups = [g for g in groups if g[1]]
    desc = "; ".join(f"{TIER_NAMES[k]}: {sum(r['outcome'] == 'passed' for r in m)} of {len(m)} passed, "
                     f"{sum(r['outcome'] == 'wrong' for r in m)} wrong, {sum(r['outcome'] == 'truncated' for r in m)} truncated"
                     for k, m in groups)
    return stacked_rows(rows, groups, lambda k: TIER_NAMES[k],
                        lambda k, m: f"{len(m)} tasks · base weight {k}",
                        f"{name}: outcome by difficulty tier", "Share of tasks per tier; label = passed / tasks", desc)


def chart_by_category(rows, name):
    cats = sorted({r["category"] for r in rows})
    groups = [(c, [r for r in rows if r["category"] == c]) for c in cats]
    groups.sort(key=lambda g: (-sum(r["outcome"] == "passed" for r in g[1]) / len(g[1]), g[0]))
    desc = "; ".join(f"{k}: {sum(r['outcome'] == 'passed' for r in m)} of {len(m)} passed" for k, m in groups)
    return stacked_rows(rows, groups, lambda k: k.replace("_", " "), lambda k, m: f"{len(m)} tasks",
                        f"{name}: outcome by category", "Share of tasks per category, sorted by pass rate", desc)


def chart_task_map(rows, name):
    cats = sorted({r["category"] for r in rows})
    by_cat = {c: sorted((r for r in rows if r["category"] == c), key=lambda r: r["id"]) for c in cats}
    ncol = max(len(v) for v in by_cat.values())
    left, top, cw, ch, gap = 150, 116, 40, 28, 2
    W = left + ncol * (cw + gap) + 24
    H = top + len(cats) * (ch + gap) + 30
    body = [t(24, 34, f"{name}: every task", "t"),
            t(24, 54, "One cell per task, in id order; the number in the cell is its difficulty tier (1–5)", "s")]
    counts = {k: sum(r["outcome"] == k for r in rows) for k in OUTCOMES}
    body += legend(24, 80, OUTCOMES, counts)
    for j in range(ncol):
        body.append(t(left + j * (cw + gap) + cw / 2, top - 10, f"{j + 1:02d}", "m", "middle"))
    for i, c in enumerate(cats):
        y = top + i * (ch + gap)
        prefix = by_cat[c][0]["id"].rsplit("-", 1)[0]
        body.append(t(24, y + ch / 2 + 4.5, c.replace("_", " "), "l"))
        body.append(t(left - 10, y + ch / 2 + 4.5, prefix, "m", "end"))
        for j, r in enumerate(by_cat[c]):
            x = left + j * (cw + gap)
            body.append(f'<g><title>{escape(r["id"])} · T{r["tier"]} · {escape(OUTCOME_LABEL[r["outcome"]])} · '
                        f'{escape(r["title"])}</title>' + bar(x, y, cw, ch, r["outcome"], True, True)
                        + t(x + cw / 2, y + ch / 2 + 4.5, r["tier"], "in", "middle") + "</g>")
    desc = "Failed tasks: " + ", ".join(f"{r['id']} ({OUTCOME_LABEL[r['outcome']].split(' (')[0].lower()})"
                                        for r in rows if r["outcome"] != "passed")
    return svg(W, H, body, f"{name}: every task", desc)


def chart_tokens(rows, name, max_tokens):
    pts = [r for r in rows if r["tokens"]]
    W, left, right, top, row_h = 780, 130, 30, 112, 92
    plot_w = W - left - right
    lo = 10 ** math.floor(math.log10(min(r["tokens"] for r in pts)))
    top_v = max(r["tokens"] for r in pts) * 1.15
    hi = min(m * 10 ** e for e in range(1, 9) for m in (1, 2, 5) if m * 10 ** e >= top_v)
    sx = lambda v: left + plot_w * (math.log10(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))  # noqa: E731
    tiers = [k for k in range(1, 6) if any(r["tier"] == k for r in pts)]
    H = top + row_h * len(tiers) + 50
    body = [t(24, 34, f"{name}: completion tokens per task", "t"),
            t(24, 54, "Reasoning + answer tokens per task, log scale; agent tasks count the whole episode", "s")]
    counts = {k: sum(r["outcome"] == k for r in pts) for k in OUTCOMES}
    body += legend(24, 80, OUTCOMES, counts)
    y0, y1 = top, top + row_h * len(tiers)
    v = lo
    while v <= hi * 1.0001:
        x = sx(v)
        body.append(f'<line class="{"axis" if v == lo else "grid"}" x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y1}"/>')
        body.append(t(x, y1 + 18, f"{v // 1000:.0f}K" if v >= 1000 else f"{v:.0f}", "m", "middle"))
        v *= 10
    if max_tokens:
        x = sx(max_tokens)
        body.append(f'<line class="axis" x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y1}" style="stroke:var(--ink2)"/>')
        body.append(t(x + 6, y0 + 12, f"max_tokens {max_tokens:,}", "m"))
    body.append(t(left + plot_w / 2, y1 + 38, "completion tokens (log scale)", "m", "middle"))
    r_dot = 5
    for i, k in enumerate(tiers):
        yc = top + i * row_h + row_h / 2
        body.append(t(left - 14, yc + 4.5, TIER_NAMES[k], "l", "end"))
        placed = []  # simple beeswarm: nearest free vertical offset
        for r in sorted((r for r in pts if r["tier"] == k), key=lambda r: r["tokens"]):
            x = sx(r["tokens"])
            yy = yc
            for off in [0] + [s * d for d in range(1, 40) for s in (1, -1)]:
                cand = yc + off * (r_dot * 2 + 1) / 2
                if abs(cand - yc) > row_h / 2 - r_dot:
                    continue
                if all((x - px) ** 2 + (cand - py) ** 2 >= (2 * r_dot + 1.5) ** 2 for px, py in placed):
                    yy = cand
                    break
            placed.append((x, yy))
            body.append(f'<circle class="{r["outcome"]} ring" cx="{x:.1f}" cy="{yy:.1f}" r="{r_dot}">'
                        f'<title>{escape(r["id"])} · {r["tokens"]:,.0f} tokens · {escape(OUTCOME_LABEL[r["outcome"]])}'
                        f'</title></circle>')
            if r["tokens"] > (max_tokens or hi) * 1.5:
                body.append(t(x, yy + 20, r["id"], "m", "middle"))
                body.append(t(x, yy + 34, f"{r['tokens']:,.0f}", "m", "middle"))
    desc = (f"Median {sorted(r['tokens'] for r in pts)[len(pts) // 2]:,.0f} tokens per task; "
            f"{counts['truncated']} tasks stopped at the limit without an answer.")
    return svg(W, H, body, f"{name}: completion tokens per task", desc)


def chart_score(rows, name, summary, base_score):
    W, H = 780, 318
    total = sum(r["weight"] for r in rows)
    part = {k: sum(r["weight"] for r in rows if r["outcome"] == k) for k in OUTCOMES}
    counts = {k: sum(r["outcome"] == k for r in rows) for k in OUTCOMES}
    score = summary.get("weighted_score", 100 * sum(r["weight"] * r["pass_rate"] for r in rows) / total)
    body = [t(24, 34, f"{name}: weighted score", "t"), t(24, 54, summary.get("_setup", ""), "s")]
    body.append(t(24, 124, f"{score:.1f}", "hero"))
    body.append(t(24 + text_w(f"{score:.1f}", 60) + 8, 124, "/ 100", "s"))
    tiles = [("Tasks solved", f"{counts['passed']}/{len(rows)}"),
             ("Truncated", str(counts["truncated"])),
             ("Request errors", str(summary.get("error_samples", 0))),
             ("Model time", summary.get("_hours", "–"))]
    tx = 300
    for label, value in tiles:
        body.append(t(tx, 98, value, "tile"))
        body.append(t(tx, 120, label, "m"))
        tx += 120
    x0, y0, bw, bh = 24, 160, W - 48, 28
    body.append(t(x0, y0 - 10, f"Where the {total:.0f} weight points went", "l"))
    x = x0
    segs = [k for k in OUTCOMES if part[k] > 0]
    for j, k in enumerate(segs):
        w = bw * part[k] / total
        last = j == len(segs) - 1
        body.append(bar(x, y0, w - (0 if last else 2), bh, k, round_right=True, round_left=True))
        lab = f"{100 * part[k] / total:.1f}%"
        if text_w(lab, 12) + 14 <= w:
            body.append(t(x + 8, y0 + bh / 2 + 4.5, lab, "in"))
        x += w
    ly, lx = y0 + bh + 26, x0
    for k in segs:
        verb = "earned" if k == "passed" else "lost"
        label = f"{OUTCOME_LABEL[k]}: {counts[k]} tasks, {part[k]:.1f} points {verb}"
        body.append(f'<rect class="{k}" x="{lx:.1f}" y="{ly - 10:.1f}" width="12" height="12" rx="3"/>')
        body.append(t(lx + 18, ly, label, "l"))
        lx += 18 + text_w(label, 13) + 22
        if lx > W - 200:
            lx, ly = x0, ly + 22
    if base_score is not None:
        body.append(t(x0, H - 38, f"With plain tier weights (1–5) the same answers score {base_score:.1f}.", "m"))
        body.append(t(x0, H - 20, "The calibrated weights (tasks/weights.json) count each task the pilot failed "
                                  "2.6× more, so the pilot sits at 50.", "m"))
    desc = (f"Weighted score {score:.1f} of 100. {counts['passed']} of {len(rows)} tasks passed; "
            + ", ".join(f"{OUTCOME_LABEL[k].lower()}: {part[k]:.1f} of {total:.0f} weight points" for k in segs))
    return svg(W, H, body, f"{name}: weighted score", desc)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--out", help="output directory (default: <run_dir>/charts)")
    ap.add_argument("--title", help="model name shown in chart titles (default: the run's model name)")
    args = ap.parse_args()
    run = Path(args.run_dir)
    out = Path(args.out) if args.out else run / "charts"
    out.mkdir(parents=True, exist_ok=True)
    rows = load(run)
    summary = json.loads((run / "summary.json").read_text(encoding="utf-8")) if (run / "summary.json").exists() else {}
    meta = json.loads((run / "meta.json").read_text(encoding="utf-8")) if (run / "meta.json").exists() else {}
    cfg = meta.get("config", {})
    params = cfg.get("params", {})
    name = args.title or cfg.get("model") or run.name
    max_tokens = params.get("max_tokens")
    setup = [run.name]
    if params.get("reasoning_effort"):
        setup.append(f"reasoning effort {params['reasoning_effort']}")
    if max_tokens:
        setup.append(f"max_tokens {max_tokens:,}")
    setup.append(f"{meta.get('samples', 1)} sample(s) per task")
    summary["_setup"] = " · ".join(setup)
    lat = [json.loads(line).get("latency_s") or 0 for line in open(run / "responses.jsonl", encoding="utf-8") if line.strip()]
    summary["_hours"] = f"{sum(lat) / 3600:.1f} h" if any(lat) else "–"
    tier_w = {t["id"]: t["tier"] for t in load_tasks(calibrated_weights=False)}
    base = 100 * sum(tier_w[r["id"]] * r["pass_rate"] for r in rows) / sum(tier_w[r["id"]] for r in rows)
    base = None if abs(base - summary.get("weighted_score", base)) < 0.05 else base
    charts = {"score.svg": chart_score(rows, name, summary, base),
              "by_tier.svg": chart_by_tier(rows, name),
              "by_category.svg": chart_by_category(rows, name),
              "task_map.svg": chart_task_map(rows, name),
              "tokens.svg": chart_tokens(rows, name, max_tokens)}
    for fname, content in charts.items():
        (out / fname).write_text(content, encoding="utf-8")
        print(f"wrote {out / fname}")


if __name__ == "__main__":
    main()
