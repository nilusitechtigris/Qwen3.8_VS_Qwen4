"""Simulated tool environments for the AGENT tasks.

Protocol (plain text, works with any OpenAI-compatible chat endpoint, no native tool-calling needed):
  model -> one line   CALL {"tool": "<name>", "args": {...}}
  runner -> message   RESULT: {...json...}
  ... until the model answers with a line   FINAL ANSWER: <answer>
Environments are deterministic, so grading replays the recorded calls on a fresh environment.
"""
from __future__ import annotations

import json
import re
from collections import deque

from .common import extract_final, strip_thinking

PROTOCOL = """You can use the tools listed below. To call a tool, end your message with exactly one line of the form
CALL {"tool": "<tool name>", "args": {<arguments as JSON>}}
and nothing after it. Call only one tool per message. The result will come back in the next message as
RESULT: <json>. When you have finished, reply WITHOUT a CALL line and end with a line of the form
FINAL ANSWER: <your answer>"""

_CALL_RE = re.compile(r"^\s*CALL\s*(\{.*\})\s*$", re.M)


def parse_call(visible: str):
    """Return (call_dict | None, error | None) from the visible (non-thinking) text of a model message."""
    m = list(_CALL_RE.finditer(visible))
    if not m:
        return None, None
    raw = m[0].group(1)
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError as e:
        return None, f"invalid JSON in CALL line: {e}"
    if not isinstance(obj, dict) or "tool" not in obj:
        return None, 'CALL JSON must look like {"tool": "...", "args": {...}}'
    args = obj.get("args", {})
    if not isinstance(args, dict):
        return None, "args must be a JSON object"
    return {"tool": obj["tool"], "args": args}, None


# ============================================================================== environments
class Env:
    def __init__(self, config: dict):
        self.cfg = config

    def call(self, tool: str, args: dict) -> dict:
        fn = getattr(self, "t_" + tool, None)
        if fn is None:
            return {"error": f"unknown tool {tool!r}"}
        try:
            return fn(**args)
        except TypeError as e:
            return {"error": f"bad arguments: {e}"}

    def state_ok(self, check: dict) -> tuple[bool, str]:
        return True, "no state check"


class CalcEnv(Env):
    def t_add(self, a, b):
        return {"result": int(a) + int(b)}

    def t_multiply(self, a, b):
        return {"result": int(a) * int(b)}


class FileEnv(Env):
    def _norm(self, p):
        p = "/" + str(p).strip().strip("/")
        return p if p != "/" else "/"

    def t_list_dir(self, path="/"):
        p = self._norm(path)
        files = self.cfg["files"]
        prefix = "" if p == "/" else p
        entries = set()
        for f in files:
            if f.startswith(prefix + "/"):
                rest = f[len(prefix) + 1:]
                entries.add(rest.split("/")[0] + ("/" if "/" in rest else ""))
        if not entries:
            return {"error": f"no such directory: {p}"}
        return {"path": p, "entries": sorted(entries)}

    def t_read_file(self, path):
        p = self._norm(path)
        if p not in self.cfg["files"]:
            return {"error": f"no such file: {p}"}
        return {"path": p, "content": self.cfg["files"][p]}


class OrdersEnv(Env):
    def t_find_customer(self, name):
        for c in self.cfg["customers"]:
            if c["name"].lower() == str(name).strip().lower():
                return {"customer_id": c["id"], "name": c["name"]}
        return {"error": "customer not found"}

    def t_list_orders(self, customer_id):
        return {"orders": [{k: o[k] for k in ("order_id", "status", "date")} for o in self.cfg["orders"]
                           if o["customer_id"] == customer_id]}

    def t_get_order(self, order_id):
        for o in self.cfg["orders"]:
            if o["order_id"] == order_id:
                return {"order_id": order_id, "currency": "EUR", "items": o["items"], "status": o["status"]}
        return {"error": "order not found"}


class FlightsEnv(Env):
    def t_search_flights(self, origin, destination, date):
        o, d = str(origin).upper().strip(), str(destination).upper().strip()
        if date != self.cfg["date"]:
            return {"flights": [], "note": "no flights on that date"}
        return {"flights": [f for f in self.cfg["flights"] if f["from"] == o and f["to"] == d]}


class RepoEnv(Env):
    def t_list_files(self):
        return {"files": sorted(self.cfg["files"])}

    def t_read_file(self, path):
        p = str(path).strip().lstrip("./")
        if p not in self.cfg["files"]:
            return {"error": f"no such file: {p}"}
        src = self.cfg["files"][p]
        return {"path": p, "content": "\n".join(f"{i:>3}| {ln}" for i, ln in enumerate(src.splitlines(), 1))}

    def t_run_tests(self):
        return {"output": self.cfg["test_output"]}


class TicketsEnv(Env):
    def t_list_tickets(self, page_token=None):
        page = 0 if page_token in (None, "", "null") else None
        if page is None:
            tok = str(page_token)
            if tok not in self.cfg["tokens"]:
                return {"error": "invalid page_token"}
            page = self.cfg["tokens"].index(tok) + 1
        size = self.cfg["page_size"]
        items = self.cfg["tickets"][page * size:(page + 1) * size]
        nxt = self.cfg["tokens"][page] if (page + 1) * size < len(self.cfg["tickets"]) else None
        return {"tickets": items, "next_page_token": nxt}


class StockEnv(Env):
    def t_get_stock(self, sku):
        s = self.cfg["stock"].get(str(sku))
        if s is None:
            return {"error": "unknown sku"}
        return {"sku": sku, "qty": s["cached"], "source": "cache", "as_of": s["as_of"], "stale": s["stale"]}

    def t_refresh_stock(self, sku):
        s = self.cfg["stock"].get(str(sku))
        if s is None:
            return {"error": "unknown sku"}
        return {"sku": sku, "qty": s["live"], "source": "live"}


class RobotEnv(Env):
    DIRS = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1)}

    def __init__(self, config):
        super().__init__(config)
        self.grid = config["grid"]
        self.pos = tuple(config["start"])
        self.steps = 0
        self.carrying = None
        self.packages = {p["id"]: {"at": tuple(p["pickup"]), "dest": tuple(p["dest"]), "delivered": False}
                         for p in config["packages"]}

    def _view(self):
        return {"position": list(self.pos), "steps_used": self.steps, "step_budget": self.cfg["budget"],
                "carrying": self.carrying,
                "packages": {k: {"at": list(v["at"]) if v["at"] else None, "dest": list(v["dest"]),
                                 "delivered": v["delivered"]} for k, v in self.packages.items()}}

    def t_look(self):
        return {**self._view(), "map": self.grid}

    def t_move(self, path):
        path = str(path).upper().replace(" ", "").replace(",", "")
        done = ""
        for ch in path:
            if ch not in self.DIRS:
                return {"error": f"bad direction {ch!r}", **self._view()}
            if self.steps >= self.cfg["budget"]:
                return {"error": "step budget exhausted", "moved": done, **self._view()}
            dr, dc = self.DIRS[ch]
            r, c = self.pos[0] + dr, self.pos[1] + dc
            self.steps += 1
            if not (0 <= r < len(self.grid) and 0 <= c < len(self.grid[0])) or self.grid[r][c] == "#":
                return {"error": f"blocked moving {ch} from {list(self.pos)}", "moved": done, **self._view()}
            self.pos = (r, c)
            done += ch
        return {"moved": done, **self._view()}

    def t_pick(self):
        if self.carrying:
            return {"error": "already carrying a package", **self._view()}
        for k, v in self.packages.items():
            if v["at"] == self.pos and not v["delivered"]:
                v["at"] = None
                self.carrying = k
                return {"picked": k, **self._view()}
        return {"error": "no package here", **self._view()}

    def t_drop(self):
        if not self.carrying:
            return {"error": "not carrying anything", **self._view()}
        k = self.carrying
        self.carrying = None
        v = self.packages[k]
        if v["dest"] == self.pos:
            v["delivered"] = True
            return {"delivered": k, **self._view()}
        v["at"] = self.pos
        return {"dropped": k, "note": "not its destination", **self._view()}

    def state_ok(self, check):
        n = sum(v["delivered"] for v in self.packages.values())
        ok = n == len(self.packages) and self.steps <= self.cfg["budget"]
        return ok, f"delivered {n}/{len(self.packages)} using {self.steps}/{self.cfg['budget']} steps"


ENVS = {"calc": CalcEnv, "files": FileEnv, "orders": OrdersEnv, "flights": FlightsEnv, "repo": RepoEnv,
        "tickets": TicketsEnv, "stock": StockEnv, "robot": RobotEnv}


def make_env(task):
    g = task["grader"]
    return ENVS[g["env"]](g["config"])


# ============================================================================== episode loop
# Total output tokens (thinking included) one agent episode may spend: 3 full turns at max_tokens 32768.
# Without it, a model that keeps hitting max_tokens re-thinks from scratch every turn (only visible text is kept
# in the conversation) and a 30-turn episode can run for ~12 hours on a local machine. When the budget is used up
# the episode stops before the next turn and is graded on the state reached so far. It is part of the harness,
# so it applies identically to every model; it is recorded in meta.json.
EPISODE_TOKEN_BUDGET = 98_304


def run_episode(task, respond, max_turns=None, token_budget=None):
    """respond(messages) -> (content, reasoning, usage). Returns a record dict for responses.jsonl."""
    env = make_env(task)
    max_turns = max_turns or task["grader"].get("max_turns", 20)
    token_budget = token_budget or task["grader"].get("token_budget", EPISODE_TOKEN_BUDGET)
    messages = [{"role": "user", "content": task["prompt"]}]
    calls, usage_total, turns, spent, stopped = [], {}, 0, 0, None
    content, reasoning = "", ""
    for turn in range(1, max_turns + 1):
        if spent >= token_budget:
            stopped = "token_budget"
            break
        turns = turn
        content, reasoning, usage = respond(messages)
        for k, v in (usage or {}).items():
            if isinstance(v, int):
                usage_total[k] = usage_total.get(k, 0) + v
        ct = (usage or {}).get("completion_tokens")
        # servers that report no usage: estimate ~4 characters per token
        spent += ct if isinstance(ct, int) else (len(content or "") + len(reasoning or "")) // 4
        visible = strip_thinking(content)
        messages.append({"role": "assistant", "content": visible})
        call, err = parse_call(visible)
        if err:
            messages.append({"role": "user", "content": "RESULT: " + json.dumps({"error": err})})
            continue
        if call:
            res = env.call(call["tool"], call["args"])
            calls.append(call)
            messages.append({"role": "user", "content": "RESULT: " + json.dumps(res, ensure_ascii=False)})
            continue
        if extract_final(visible) is not None:
            break
        messages.append({"role": "user", "content": "Please either CALL a tool or give your FINAL ANSWER."})
    else:
        stopped = "max_turns"
    return {"content": content, "reasoning": reasoning, "calls": calls, "turns": turns, "stopped": stopped,
            "transcript": messages, "usage": usage_total}


def grade_agent(task, record):
    from .graders import ANSWER_GRADERS  # local import to avoid a cycle

    g = task["grader"]
    env = ENVS[g["env"]](g["config"])
    for c in record.get("calls", []):
        env.call(c["tool"], c["args"])
    detail = []
    passed = True
    final = extract_final(record.get("content") or "")
    if g.get("answer"):
        r = ANSWER_GRADERS[g["answer"]["type"]](g["answer"], final)
        passed &= r["passed"]
        detail.append(r["detail"] or ("answer ok" if r["passed"] else "answer wrong"))
    if g.get("state_check") is not None:
        ok, d = env.state_ok(g["state_check"])
        passed &= ok
        detail.append(d)
    for req in g.get("required_tools", []):
        if not any(c["tool"] == req for c in record.get("calls", [])):
            passed = False
            detail.append(f"required tool {req!r} was never called")
    return {"passed": bool(passed), "extracted": final, "detail": "; ".join(detail)}


def bfs_dist(grid, a, b):
    R, Cn = len(grid), len(grid[0])
    q, seen = deque([(tuple(a), 0)]), {tuple(a)}
    while q:
        (r, c), d = q.popleft()
        if (r, c) == tuple(b):
            return d
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < R and 0 <= nc < Cn and grid[nr][nc] != "#" and (nr, nc) not in seen:
                seen.add((nr, nc))
                q.append(((nr, nc), d + 1))
    return None


def bfs_path(grid, a, b):
    R, Cn = len(grid), len(grid[0])
    prev = {tuple(a): None}
    q = deque([tuple(a)])
    while q:
        cur = q.popleft()
        if cur == tuple(b):
            break
        for ch, (dr, dc) in RobotEnv.DIRS.items():
            nr, nc = cur[0] + dr, cur[1] + dc
            if 0 <= nr < R and 0 <= nc < Cn and grid[nr][nc] != "#" and (nr, nc) not in prev:
                prev[(nr, nc)] = (cur, ch)
                q.append((nr, nc))
    path, cur = "", tuple(b)
    while prev[cur] is not None:
        cur, ch = prev[cur]
        path = ch + path
    return path
