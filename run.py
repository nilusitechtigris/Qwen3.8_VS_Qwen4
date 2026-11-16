#!/usr/bin/env python3
"""Run the benchmark against an OpenAI-compatible endpoint and store raw responses.

    python3 run.py --config configs/qwen3.8-27b-4bit.json
    python3 run.py --config configs/qwen3.8-27b-4bit.json --only MATH-01,CODE-03 --samples 1
    python3 run.py --config configs/qwen3.8-27b-4bit.json --list-models

Results go to results/<run_name>/responses.jsonl (one line per task x sample) plus meta.json.
Runs are resumable: re-running the same command skips (task, sample) pairs that already succeeded.
Grading happens automatically at the end (or run grade.py yourself).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from bench.client import ChatError, chat, list_models
from bench.common import ROOT, TASKS_PATH, load_tasks
from bench.envs import run_episode


def select(tasks, only=None, categories=None, tiers=None):
    if only:
        ids = {x.strip() for x in only.split(",") if x.strip()}
        tasks = [t for t in tasks if t["id"] in ids]
    if categories:
        cs = {x.strip() for x in categories.split(",")}
        tasks = [t for t in tasks if t["category"] in cs]
    if tiers:
        ts = {int(x) for x in tiers.split(",")}
        tasks = [t for t in tasks if t["tier"] in ts]
    return tasks


def load_done(path):
    done = set()
    if path.exists():
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not r.get("error"):
                    done.add((r["id"], r["sample"]))
    return done


def run_one(cfg, task, sample):
    if task["mode"] == "agent":
        meta = {}

        def respond(messages):
            r = chat(cfg, messages)
            meta.setdefault("finish_reasons", []).append(r["finish_reason"])
            meta["model"] = r["model"]
            meta["latency_s"] = meta.get("latency_s", 0) + r["latency_s"]
            return r["content"], r["reasoning"], r["usage"]

        rec = run_episode(task, respond)
        rec.update(finish_reason=(meta.get("finish_reasons") or [None])[-1], latency_s=round(meta.get("latency_s", 0), 2),
                   model=meta.get("model"), finish_reasons=meta.get("finish_reasons"))
        return rec
    r = chat(cfg, [{"role": "user", "content": task["prompt"]}])
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True, help="model config JSON (see configs/)")
    ap.add_argument("--run-name", help="results/<run-name>; default: config 'name'")
    ap.add_argument("--samples", type=int, default=None, help="samples per task (default from config, else 1)")
    ap.add_argument("--only", help="comma-separated task ids")
    ap.add_argument("--categories", help="comma-separated categories")
    ap.add_argument("--tiers", help="comma-separated tiers, e.g. 1,2")
    ap.add_argument("--concurrency", type=int, default=None, help="parallel requests (default from config, else 1)")
    ap.add_argument("--max-tokens", type=int, help="override params.max_tokens")
    ap.add_argument("--no-thinking", action="store_true", help="set chat_template_kwargs.enable_thinking=false")
    ap.add_argument("--list-models", action="store_true", help="print the model ids the server exposes and exit")
    ap.add_argument("--no-grade", action="store_true", help="do not grade at the end")
    args = ap.parse_args()

    cfg = json.loads(open(args.config, encoding="utf-8").read())
    if args.list_models:
        print("\n".join(list_models(cfg)))
        return 0
    if args.max_tokens:
        cfg.setdefault("params", {})["max_tokens"] = args.max_tokens
    if args.no_thinking:
        cfg.setdefault("extra_body", {}).setdefault("chat_template_kwargs", {})["enable_thinking"] = False
    samples = args.samples or cfg.get("samples", 1)
    concurrency = args.concurrency or cfg.get("concurrency", 1)
    run_name = args.run_name or cfg["name"]
    out_dir = ROOT / "results" / run_name
    out_dir.mkdir(parents=True, exist_ok=True)
    resp_path = out_dir / "responses.jsonl"

    tasks = select(load_tasks(), args.only, args.categories, args.tiers)
    tasks_sha = hashlib.sha256(TASKS_PATH.read_bytes()).hexdigest()
    meta_path = out_dir / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    if meta.get("tasks_sha256") and meta["tasks_sha256"] != tasks_sha:
        print("WARNING: tasks.jsonl changed since this run started - results will mix task versions!", file=sys.stderr)
    meta.update({
        "run_name": run_name, "config": {k: v for k, v in cfg.items() if k != "api_key"},
        "tasks_sha256": tasks_sha, "samples": samples, "python": sys.version.split()[0],
        "platform": platform.platform(), "started": meta.get("started") or datetime.now(timezone.utc).isoformat(),
    })
    meta_path.write_text(json.dumps(meta, indent=2))

    done = load_done(resp_path)
    todo = [(t, s) for t in tasks for s in range(samples) if (t["id"], s) not in done]
    print(f"{run_name}: {len(tasks)} tasks x {samples} samples, {len(todo)} to run ({len(done)} already done)")
    lock = threading.Lock()
    t_start = time.time()

    def work(item):
        t, s = item
        try:
            rec = run_one(cfg, t, s)
            err = None
        except ChatError as e:
            rec, err = {}, str(e)
        line = {"id": t["id"], "sample": s, "error": err, "timestamp": datetime.now(timezone.utc).isoformat(), **rec}
        with lock:
            with open(resp_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(line, ensure_ascii=False) + "\n")
        return t["id"], s, err, rec.get("finish_reason"), rec.get("latency_s")

    n = 0
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = [ex.submit(work, it) for it in todo]
        for fut in as_completed(futs):
            n += 1
            tid, s, err, fr, lat = fut.result()
            status = "ERROR " + err[:120] if err else f"finish={fr} {lat}s"
            print(f"[{n}/{len(todo)}] {tid}#{s} {status}  (elapsed {(time.time() - t_start) / 60:.1f} min)", flush=True)

    meta["finished"] = datetime.now(timezone.utc).isoformat()
    meta_path.write_text(json.dumps(meta, indent=2))
    if not args.no_grade:
        import grade
        grade.grade_run(out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
