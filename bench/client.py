"""Minimal OpenAI-compatible chat client (standard library only).

Works with LM Studio, mlx_lm.server, llama.cpp server, vLLM, SGLang, Ollama (/v1), and hosted APIs.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request


class ChatError(RuntimeError):
    pass


def _post(url, body, headers, timeout):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _headers(cfg):
    h = {"Content-Type": "application/json"}
    key_env = cfg.get("api_key_env")
    key = os.environ.get(key_env, "") if key_env else ""
    if key:
        h["Authorization"] = f"Bearer {key}"
    return h


def list_models(cfg):
    url = cfg["base_url"].rstrip("/") + "/models"
    req = urllib.request.Request(url, headers=_headers(cfg))
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    return [m.get("id") for m in data.get("data", [])]


def chat(cfg: dict, messages: list[dict], retries: int = 3):
    """Returns dict(content, reasoning, usage, finish_reason, latency_s, model)."""
    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    body = {"model": cfg["model"], "messages": messages, "stream": False}
    body.update(cfg.get("params", {}))
    body.update(cfg.get("extra_body", {}))
    last_err = None
    for attempt in range(retries):
        t0 = time.time()
        try:
            data = _post(url, body, _headers(cfg), cfg.get("timeout_s", 7200))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            last_err = f"HTTP {e.code}: {detail}"
            if 400 <= e.code < 500 and e.code != 429:
                break  # bad request (e.g. unsupported parameter) - retrying will not help
        except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as e:
            last_err = f"{type(e).__name__}: {e}"
        else:
            if not data.get("choices"):
                last_err = f"no choices in response: {str(data)[:300]}"
            else:
                ch = data["choices"][0]
                msg = ch.get("message") or {}
                return {
                    "content": msg.get("content") or "",
                    "reasoning": msg.get("reasoning_content") or msg.get("reasoning") or "",
                    "usage": data.get("usage") or {},
                    "finish_reason": ch.get("finish_reason"),
                    "latency_s": round(time.time() - t0, 2),
                    "model": data.get("model"),
                }
        time.sleep(min(60, 5 * 2 ** attempt))
    raise ChatError(last_err or "unknown error")
