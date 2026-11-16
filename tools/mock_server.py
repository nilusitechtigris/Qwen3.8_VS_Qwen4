#!/usr/bin/env python3
"""A fake OpenAI-compatible server for smoke-testing the pipeline without a real model.

    python3 tools/mock_server.py --port 8799 --accuracy 1.0   # oracle: answers every task correctly
    python3 tools/mock_server.py --port 8799 --accuracy 0.5   # answers ~50% of tasks correctly

It recognises each task by its prompt and replies with the self-test reference (or the known-wrong answer),
wrapped in a fake <think> block. Use configs/mock.json to point run.py at it.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from bench.common import load_tasks  # noqa: E402

TASKS = {t["prompt"]: t for t in load_tasks()}
REFS = {}
with open(ROOT / "tasks" / "selftest_refs.jsonl", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        REFS[r["id"]] = r
ARGS = None


def decide_correct(task_id):
    rnd = random.Random(f"{ARGS.seed}-{task_id}")
    return rnd.random() < ARGS.accuracy


def reply_for(messages):
    first = messages[0]["content"]
    task = TASKS.get(first)
    if task is None:
        return "I do not recognise this task.\nFINAL ANSWER: ?"
    ref = REFS[task["id"]]
    use = ref["reference"] if decide_correct(task["id"]) or ref.get("wrong") is None else ref["wrong"]
    if task["mode"] == "agent":
        script = use["script"]
        n_assistant = sum(1 for m in messages if m["role"] == "assistant")
        return script[n_assistant] if n_assistant < len(script) else "FINAL ANSWER: ?"
    return use


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, obj, code=200):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.rstrip("/").endswith("/models"):
            self._send({"data": [{"id": "mock-model"}]})
        else:
            self._send({"error": "not found"}, 404)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        text = reply_for(body["messages"])
        content = "<think>\nLet me work through this carefully.\n</think>\n\n" + text
        self._send({"model": body.get("model"), "choices": [{"index": 0, "finish_reason": "stop",
                    "message": {"role": "assistant", "content": content}}],
                    "usage": {"prompt_tokens": len(body["messages"][0]["content"]) // 4,
                              "completion_tokens": len(content) // 4}})


def main():
    global ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8799)
    ap.add_argument("--accuracy", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=0)
    ARGS = ap.parse_args()
    print(f"mock server on http://127.0.0.1:{ARGS.port}/v1 (accuracy {ARGS.accuracy})", flush=True)
    ThreadingHTTPServer(("127.0.0.1", ARGS.port), H).serve_forever()


if __name__ == "__main__":
    main()
