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


def ollama_unload(cfg, wait_s=120):
    """Unload the model from an Ollama server and wait until it is gone.

    Used between tasks when the config sets "unload_between_tasks": "ollama". Ollama's MLX runner keeps a prefix
    cache of every prompt it has seen and does not free it, so on a small-memory machine memory use grows task by
    task until the system swaps heavily. Unloading after each task frees that memory and also guarantees that no
    task benefits from another task's cache.
    """
    root = cfg["base_url"].rstrip("/")
    if root.endswith("/v1"):
        root = root[:-3]
    try:
        _post(root + "/api/generate", {"model": cfg["model"], "keep_alive": 0}, _headers(cfg), 60)
    except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as e:
        print(f"warning: could not unload {cfg['model']}: {e}", flush=True)
        return False
    deadline = time.time() + wait_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(urllib.request.Request(root + "/api/ps", headers=_headers(cfg)), timeout=30) as r:
                loaded = [m.get("name", "") for m in json.loads(r.read().decode("utf-8")).get("models", [])]
        except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError):
            loaded = []
        if not any(n == cfg["model"] or n.split(":")[0] == cfg["model"].split(":")[0] for n in loaded):
            return True
        time.sleep(1)
    print(f"warning: {cfg['model']} still loaded after {wait_s}s", flush=True)
    return False
