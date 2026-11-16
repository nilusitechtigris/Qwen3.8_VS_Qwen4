# Qwen3.8 vs Qwen4 — 27B 4-bit comparison benchmark

100 original tasks with weights and difficulty tiers, built to compare **Qwen3.8-27B (4-bit)** with **Qwen4-27B
(4-bit)** as soon as Qwen4 lands on Hugging Face.

- **Calibrated for headroom:** the prior expected score of Qwen3.8-27B 4-bit (thinking on) is **≈ 50 / 100**. That
  leaves room above for Qwen4 to show improvement, and enough easy tasks to catch regressions.
- **Deterministic grading, no LLM judge:** every task is pass/fail by code. That means exact or numeric answers,
  hidden unit tests, executed SQL, constraint checkers, or the final state of a simulated environment.
- **Original and generated:** puzzles, documents and test data are produced by seeded generators, and every
  computable answer is computed in code (brute force, solvers, interpreters). So the answers are verified and the
  tasks are not copies of public benchmarks.
- **Zero dependencies:** Python 3.10+ standard library only. Talks to any OpenAI-compatible server (LM Studio,
  mlx_lm.server, llama.cpp, vLLM, SGLang, Ollama).

## At a glance

Each task's weight equals its tier. That gives 314 points in total, and the score is `100 × earned / 314`.

| Tier | Weight | Tasks | Points | Prior pass rate (Qwen3.8) | Purpose |
|---|---:|---:|---:|---:|---|
| T1 warm-up | 1 | 8 | 8 | 0.97 | sanity / regression floor |
| T2 standard | 2 | 20 | 40 | 0.87 | solid everyday competence |
| T3 hard | 3 | 33 | 99 | 0.59 | where the 50 line is decided |
| T4 very hard | 4 | 28 | 112 | 0.41 | main headroom for Qwen4 |
| T5 frontier | 5 | 11 | 55 | 0.17 | ceiling: should rarely pass today |

| Category | Tasks | Points | What it measures | Graded by |
|---|---:|---:|---|---|
| math | 14 | 45 | number theory, combinatorics, probability, geometry | exact numbers / fractions |
| logic | 12 | 38 | logic grids, knights/knaves/spies, epistemic puzzle, scheduling, Sudoku | exact answers (uniqueness proven by solver) |
| code | 14 | 45 | algorithms with large-input time limits, strict spec parsing | hidden unit tests in a subprocess |
| instruction | 11 | 31 | stacked verifiable constraints (lipogram, acrostics, exact word counts) | constraint checkers |
| knowledge | 10 | 31 | long-tail facts (Unicode, RFCs, ISO codes, math history) | exact answers |
| long_context | 8 | 28 | needles with decoys, variable chasing, aggregation, state tracking (up to ~20k tokens) | exact answers |
| trace | 8 | 29 | executing code mentally: Python gotchas, stack/register machines, xorshift, Life, Rule 110, Brainfuck | exact output |
| agent | 8 | 24 | multi-turn tool use in simulated environments (pagination, stale caches, planning under a step budget) | final answer and/or final environment state |
| structured | 6 | 16 | JSON/CSV extraction, regex writing, SQLite (window functions, recursive CTE) | JSON/CSV checkers, regex test-suite, SQL executed on SQLite |
| science | 5 | 15 | physics, genetics, orbital mechanics, stereochemistry, term symbols | numeric tolerance / exact |
| multilingual | 4 | 12 | Turkish morphology and numbers, German numbers, Japanese morae | exact answers |

The full list (IDs, tiers, prior pass rates, titles; no answers) is in [tasks/TASKS.md](tasks/TASKS.md).

## Quick start

```bash
python3 selftest.py
```

The self-test proves the benchmark itself is sound, with no model involved. For every task, the reference answer
must pass. It must still pass when preceded by a `<think>` block that contains a wrong answer. A plausible wrong
answer must fail (88 tasks have one), and an empty reply must fail.

### 1. Serve Qwen3.8-27B 4-bit

Any OpenAI-compatible server works. On a Mac, the simplest is LM Studio with
[`lmstudio-community/Qwen3.8-27B-MLX-4bit`](https://hf.co/lmstudio-community/Qwen3.8-27B-MLX-4bit):
download it, load it with a **context length of at least 65,536 tokens** (the longest prompt is about 20k tokens,
plus up to 32k output tokens), and start the local server (default `http://localhost:1234/v1`).

Then put the exact model id your server exposes into `configs/qwen3.8-27b-4bit.json`:

```bash
python3 run.py --config configs/qwen3.8-27b-4bit.json --list-models
```

### 2. Smoke test, then the full run

```bash
python3 run.py --config configs/qwen3.8-27b-4bit.json --tiers 1 --run-name smoke
```

```bash
python3 run.py --config configs/qwen3.8-27b-4bit.json
```

Results go to `results/<name>/` (`responses.jsonl`, `meta.json`, then `grades.jsonl`, `summary.json` and
`summary.md`). Runs are **resumable**: re-run the same command and finished tasks are skipped. Useful flags:
`--only MATH-01,CODE-03`, `--categories code,math`, `--tiers 3,4`, `--samples 3`, `--max-tokens 65536`,
`--no-thinking`, `--concurrency 2`.

### 3. Check calibration on Qwen3.8 (pilot run)

```bash
python3 calibrate.py results/qwen3.8-27b-4bit
```

This compares the observed score with the prior, tier by tier, and lists surprises: expected-easy tasks that
failed and expected-hard tasks that passed. If the score lands far outside 45–55, retune `est_p` or tiers in
`build/cat_*.py`, rebuild (see below), and repeat. **Freeze the task set before Qwen4 is released.** Every run
records the SHA-256 of `tasks/tasks.jsonl`, and grading warns if it changed.

### 4. When Qwen4 is out

Edit `configs/qwen4-27b-4bit.json`: set the model id, and copy the sampling settings from the Qwen4 model card. Then:

```bash
python3 run.py --config configs/qwen4-27b-4bit.json
```

```bash
python3 compare.py results/qwen3.8-27b-4bit results/qwen4-27b-4bit
```

`compare.py` writes `reports/<A>_vs_<B>.md` (and `.json`) containing:

- the weighted-score delta, with a **paired bootstrap 95% CI** over tasks
- an exact **McNemar** test on tasks that flipped
- per-tier and per-category deltas
- the lists of tasks only one model solves (so you can spot regressions)

## Fair-comparison protocol

1. Both runs use the **same `tasks/tasks.jsonl`** (check `tasks_sha256` in each `meta.json`).
2. Use the **same quantization family and bit width**, from the same converter if possible (e.g. both MLX 4-bit
   from the same publisher, or both GGUF Q4_K_M). Use the same server software and version.
3. **Thinking on** for both, each model at its **officially recommended sampling settings**. For Qwen3.8 thinking
   mode the model card says: `temperature 1.0, top_p 0.95, top_k 20, min_p 0, presence_penalty 0, repetition_penalty 1`.
4. Use the **same `max_tokens`** (default 32768) and the same `reasoning_effort` if you set one. A truncated
   answer counts as a failure, and `summary.md` reports how many samples were truncated.
5. No system prompt (the task prompts are self-contained). The same context length setting for both.
6. Sampling at temperature 1.0 is noisy. One sample per task gives a rough answer; **`--samples 3`** gives
   per-task pass rates and a much tighter CI. The score then uses the mean pass rate per task.

Time: a 27B 4-bit model on Apple Silicon generates very roughly 15–25 tokens/s. With thinking, 100 tasks can take
**8–20 hours per sample**. Plan overnight runs; resuming makes interruptions harmless.

## How grading works

- **Answer extraction.** `<think>…</think>` blocks are removed (and so is everything before a stray `</think>`).
  For `final`-mode tasks, the grader takes the text after the **last** `FINAL ANSWER:` (falling back to the last
  `\boxed{}`). Markdown, LaTeX wrappers and a trailing period are stripped.
- **Answer types:**
  - `exact`: case/whitespace-normalised, with a list of accepted variants
  - `number`: exact rational (fractions are fine), or with an absolute/relative tolerance
  - `set` and `sequence`: comma-separated items
  - `regex`
- **Code tasks** (`code` mode). The last ```` ```python ```` block is extracted and run with `python3 -I` in a
  temporary directory, with the hidden tests appended. Large cases enforce the complexity the prompt asks for:
  references finish in about 0.1–0.6 s, limits are 10–40 s, and naive O(n²) solutions time out.
  ⚠️ This executes model-written code on your machine, the same as any code benchmark. Run it in a VM or
  container if that worries you.
- **SQL tasks** run the query against an in-memory SQLite database and compare the result rows.
- **Instruction tasks** (`raw` mode) are checked on the whole visible reply by
  [bench/checkers.py](bench/checkers.py). The prompts define exactly what counts as a word, sentence and line.
  For JSON-only answers, one surrounding code fence is tolerated.
- **Agent tasks** use a plain-text protocol, so no native tool-calling support is needed. The model writes
  `CALL {"tool": ..., "args": ...}`, the runner answers `RESULT: {...}`, and this repeats until `FINAL ANSWER:`.
  Environments are deterministic: grading replays the recorded calls and checks the answer and/or final state.

## Calibration: where "≈ 50" comes from

Each task carries `est_p`, a prior probability that Qwen3.8-27B 4-bit (thinking on) passes it. The expected score
is `Σ weight·est_p / Σ weight` = **49.8**, with about 58 of 100 tasks expected solved. The priors were set from the
Qwen3.8-27B model card (GPQA-Diamond 89.2, LiveCodeBench v6 90.3, HLE 30.8, IFBench 79.5, strong agentic
numbers), discounted a little for 4-bit quantisation and local `max_tokens` limits. Task difficulty was then
pushed up until the prior landed at 50.

**These are judgement calls, not measurements.** Qwen3.8 is available today, so the pilot run in step 3 is how you
turn the prior into a measured baseline before Qwen4 arrives.

## Repository layout

```
bench/          grading core: answer extraction, graders, IF checkers, agent environments, HTTP client
build/          task generators, one module per category (cat_*.py) + build_tasks.py
tasks/          tasks.jsonl (the frozen benchmark), TASKS.md (index), tasks.sha256, selftest_refs.jsonl
configs/        model configs (Qwen3.8 ready, Qwen4 placeholder, mock)
tools/          mock_server.py, a fake OpenAI-compatible server for pipeline tests
run.py          run a model     grade.py   grade a run     compare.py   A vs B report
calibrate.py    prior vs observed     selftest.py   validate every task's grader
```

Rebuilding the tasks is deterministic (all generators are seeded):

```bash
python3 build/build_tasks.py
```

```bash
python3 selftest.py
```

To test the whole HTTP pipeline without a model, start the mock server in one terminal:

```bash
python3 tools/mock_server.py --port 8799 --accuracy 0.5
```

Then run the benchmark against it in another:

```bash
python3 run.py --config configs/mock.json --run-name mock-test
```

## Caveats

- **Contamination.** `tasks/tasks.jsonl` contains the answers. If this repository is public, future models could
  see it during training. Keep the repo private until both models have been evaluated (or regenerate the tasks
  with new seeds).
- **Answers not machine-verified.** These are hand-derived or rest on established references rather than code: KNOW-01, KNOW-02, KNOW-03,
  KNOW-06, KNOW-07, LOGIC-01, LOGIC-03, LOGIC-08 (39 coins), SCI-04 (4 stereoisomers), SCI-05 (⁵I₈), LANG-01, LANG-03 and LANG-04.
  Everything else is computed or checked in code: the Unicode names come from `unicodedata`, the SHA-256 from
  `hashlib`, and the Mersenne exponent from a Lucas–Lehmer test.
- **4-bit effects.** 4-bit quantisation costs a few points, and different 4-bit methods differ. Compare like
  with like.
- **Tiers are priors too.** After the Qwen3.8 pilot, consider re-labelling tasks whose observed difficulty
  clearly contradicts their tier, but do it before freezing.
