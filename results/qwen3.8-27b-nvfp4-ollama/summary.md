# qwen3.8-27b-nvfp4-ollama

- Model: `qwen3.8-27b-bench`
- **Weighted score: 50.0 / 100** (tasks attempted: 100/100)
- Tasks solved: 79.0 / 100
- Weights: tasks/weights.json sha256 da6314aedc53eae62c51ceb7db8a103cc1498dab9d65e86ce500cc96b65edb1d
- Truncated samples (finish_reason=length): 13; request errors: 0
- Mean completion tokens per sample: 8964

| Tier | Tasks | Solved | Score |
|---|---:|---:|---:|
| T1 warm-up | 8 | 8.0 | 100.0 |
| T2 standard | 20 | 19.0 | 87.9 |
| T3 hard | 33 | 30.0 | 79.3 |
| T4 very hard | 28 | 19.0 | 44.7 |
| T5 frontier | 11 | 3.0 | 12.6 |

| Category | Tasks | Solved | Score |
|---|---:|---:|---:|
| agent | 8 | 7.0 | 59.3 |
| code | 14 | 7.0 | 20.4 |
| instruction | 11 | 8.0 | 37.8 |
| knowledge | 10 | 8.0 | 48.4 |
| logic | 12 | 10.0 | 59.0 |
| long_context | 8 | 8.0 | 100.0 |
| math | 14 | 12.0 | 60.5 |
| multilingual | 4 | 4.0 | 100.0 |
| science | 5 | 4.0 | 51.3 |
| structured | 6 | 6.0 | 100.0 |
| trace | 8 | 5.0 | 32.1 |

## Failed samples

| Task | Sample | Detail |
|---|---:|---|
| AGENT-08 | 0 | delivered 0/3 using 10/64 steps |
| CODE-03 | 0 | tests failed:   File "/var/folders/r0/yczndp3n49z7t_4634qrxz8c0000gn/T/tmp1xy0i6wx/candidate_with_tests.py", line 72, in parse_unary /     w |
| CODE-06 | 0 | no python code block found |
| CODE-09 | 0 | no python code block found |
| CODE-10 | 0 | no python code block found |
| CODE-12 | 0 | no python code block found |
| CODE-13 | 0 | no python code block found |
| CODE-14 | 0 | no python code block found |
| IF-07 | 0 | line 7 has 7 words |
| IF-08 | 0 | sentences [6] do not have exactly 12 words |
| IF-11 | 0 | acrostic 'BENCHMERKS' != 'BENCHMARKS' |
| KNOW-08 | 0 | expected one of ['CYRILLIC LETTER MULTIOCULAR O'] |
| KNOW-10 | 0 | expected one of ['REVERSED QUESTION MARK'] |
| LOGIC-06 | 0 | expected exactly 16 |
| LOGIC-12 | 0 | no FINAL ANSWER found |
| MATH-11 | 0 | could not parse a number |
| MATH-13 | 0 | could not parse a number |
| SCI-04 | 0 | could not parse a number |
| TRACE-04 | 0 | could not parse a number |
| TRACE-05 | 0 | no FINAL ANSWER found |
| TRACE-08 | 0 | expected one of ['Q8!'] |
