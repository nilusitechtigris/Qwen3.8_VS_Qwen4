# Task index

Benchmark version 1.0.0 - 100 tasks - total weight 314 points - tasks.jsonl sha256 `2b16f14176184fd5...`

Answers live in `tasks.jsonl` (grader specs). This index intentionally lists no answers.

## Calibration prior (Qwen3.8-27B 4-bit, thinking on)

Expected weighted score: **49.8 / 100** - expected tasks solved: 58.0 / 100

| Tier | Weight | Tasks | Points | Mean est. pass rate | Expected points |
|---|---:|---:|---:|---:|---:|
| T1 warm-up | 1 | 8 | 8 | 0.97 | 7.8 |
| T2 standard | 2 | 20 | 40 | 0.87 | 34.8 |
| T3 hard | 3 | 33 | 99 | 0.59 | 58.0 |
| T4 very hard | 4 | 28 | 112 | 0.41 | 46.4 |
| T5 frontier | 5 | 11 | 55 | 0.17 | 9.5 |

| Category | Tasks | Points | Expected points | Expected % |
|---|---:|---:|---:|---:|
| agent | 8 | 24 | 13.2 | 55% |
| code | 14 | 45 | 24.9 | 55% |
| instruction | 11 | 31 | 15.4 | 50% |
| knowledge | 10 | 31 | 14.3 | 46% |
| logic | 12 | 38 | 16.7 | 44% |
| long_context | 8 | 28 | 12.4 | 44% |
| math | 14 | 45 | 20.5 | 46% |
| multilingual | 4 | 12 | 7.6 | 63% |
| science | 5 | 15 | 9.9 | 66% |
| structured | 6 | 16 | 9.4 | 59% |
| trace | 8 | 29 | 12.1 | 42% |

## Tasks

| ID | Category | Tier | Weight | Est. pass (Qwen3.8) | Mode | Title |
|---|---|---:|---:|---:|---|---|
| MATH-01 | math | 1 | 1 | 0.98 | final | Sum of divisors |
| MATH-02 | math | 2 | 2 | 0.90 | final | Last three digits of a power |
| MATH-03 | math | 2 | 2 | 0.85 | final | Dice: max and parity |
| MATH-04 | math | 3 | 3 | 0.75 | final | Subset sums mod 7 |
| MATH-05 | math | 3 | 3 | 0.70 | final | Orthocenter-centroid distance |
| MATH-06 | math | 3 | 3 | 0.65 | final | Board coverings |
| MATH-07 | math | 3 | 3 | 0.50 | final | Constrained strings with a pattern |
| MATH-08 | math | 3 | 3 | 0.50 | final | Unreachable trailing-zero counts |
| MATH-09 | math | 3 | 3 | 0.55 | final | Waiting time for a pair sum |
| MATH-10 | math | 4 | 4 | 0.50 | final | Representations by x^2+xy+y^2 |
| MATH-11 | math | 4 | 4 | 0.25 | final | Permutations that move every element far |
| MATH-12 | math | 4 | 4 | 0.30 | final | Functional equation on a finite set |
| MATH-13 | math | 5 | 5 | 0.08 | final | Digit sum preserved by tripling |
| MATH-14 | math | 5 | 5 | 0.10 | final | Floor-sqrt recursion |
| LOGIC-01 | logic | 1 | 1 | 0.98 | final | Height ordering |
| LOGIC-02 | logic | 2 | 2 | 0.90 | final | Knights and knaves |
| LOGIC-03 | logic | 2 | 2 | 0.85 | final | River crossing with a big boat |
| LOGIC-04 | logic | 3 | 3 | 0.70 | final | Four-door game show variant |
| LOGIC-05 | logic | 3 | 3 | 0.45 | final | Five-house logic grid |
| LOGIC-06 | logic | 3 | 3 | 0.55 | final | Two-worker scheduling |
| LOGIC-07 | logic | 3 | 3 | 0.55 | final | Self-referential statements |
| LOGIC-08 | logic | 3 | 3 | 0.60 | final | Counterfeit coin limit |
| LOGIC-09 | logic | 4 | 4 | 0.25 | final | Six-house logic grid |
| LOGIC-10 | logic | 4 | 4 | 0.30 | final | Who knows the date |
| LOGIC-11 | logic | 5 | 5 | 0.15 | final | Knights, knaves and spies |
| LOGIC-12 | logic | 5 | 5 | 0.15 | final | Sudoku |
| CODE-01 | code | 1 | 1 | 0.98 | code | Alphanumeric palindrome |
| CODE-02 | code | 2 | 2 | 0.93 | code | Merge intervals |
| CODE-03 | code | 2 | 2 | 0.80 | code | Arithmetic expression evaluator |
| CODE-04 | code | 2 | 2 | 0.92 | code | LRU cache |
| CODE-05 | code | 3 | 3 | 0.60 | code | Alien dictionary order |
| CODE-06 | code | 3 | 3 | 0.70 | code | Shortest path collecting all keys |
| CODE-07 | code | 3 | 3 | 0.65 | code | Counting special integers |
| CODE-08 | code | 3 | 3 | 0.45 | code | Strict ISO-8601 duration parser |
| CODE-09 | code | 4 | 4 | 0.60 | code | Huge-index recurrence |
| CODE-10 | code | 4 | 4 | 0.55 | code | Distinct palindromic substrings |
| CODE-11 | code | 4 | 4 | 0.35 | code | Knight distance on an infinite board |
| CODE-12 | code | 4 | 4 | 0.55 | code | Regex matcher without backtracking blow-up |
| CODE-13 | code | 5 | 5 | 0.25 | code | k-th distinct substring |
| CODE-14 | code | 5 | 5 | 0.40 | code | Cheapest strictly increasing fix |
| IF-01 | instruction | 1 | 1 | 0.97 | raw | Single-token reply |
| IF-02 | instruction | 1 | 1 | 0.96 | raw | JSON array of primes |
| IF-03 | instruction | 2 | 2 | 0.85 | raw | Sentence initials and length |
| IF-04 | instruction | 2 | 2 | 0.85 | raw | Three lines with exact word counts |
| IF-05 | instruction | 2 | 2 | 0.85 | raw | Sorted bullet list |
| IF-06 | instruction | 3 | 3 | 0.60 | raw | Structured summary with self-consistency |
| IF-07 | instruction | 3 | 3 | 0.50 | raw | Acrostic with word quotas |
| IF-08 | instruction | 4 | 4 | 0.45 | raw | Every sentence exactly 12 words |
| IF-09 | instruction | 4 | 4 | 0.30 | raw | Lipogram |
| IF-10 | instruction | 4 | 4 | 0.40 | raw | Growing, chained sentences |
| IF-11 | instruction | 5 | 5 | 0.10 | raw | Staircase acrostic with a letter budget |
| KNOW-01 | knowledge | 1 | 1 | 0.99 | final | Element symbol |
| KNOW-02 | knowledge | 2 | 2 | 0.85 | final | Bieberbach conjecture |
| KNOW-03 | knowledge | 2 | 2 | 0.80 | final | Ytterby elements |
| KNOW-04 | knowledge | 3 | 3 | 0.55 | final | Mersenne prime exponent |
| KNOW-05 | knowledge | 3 | 3 | 0.55 | final | Unicode code point |
| KNOW-06 | knowledge | 3 | 3 | 0.50 | final | HTTP semantics RFC |
| KNOW-07 | knowledge | 4 | 4 | 0.45 | final | ISO 3166 numeric code |
| KNOW-08 | knowledge | 4 | 4 | 0.30 | final | Obscure Unicode character name |
| KNOW-09 | knowledge | 4 | 4 | 0.40 | final | SHA-256 test vector |
| KNOW-10 | knowledge | 5 | 5 | 0.12 | final | Unicode punctuation name |
| LONG-01 | long_context | 2 | 2 | 0.93 | final | Needle in a server log |
| LONG-02 | long_context | 3 | 3 | 0.65 | final | Multi-needle with corrections |
| LONG-03 | long_context | 3 | 3 | 0.60 | final | Variable chasing in a long script |
| LONG-04 | long_context | 3 | 3 | 0.60 | final | Filtered aggregation over a CSV |
| LONG-05 | long_context | 4 | 4 | 0.35 | final | Concurrent sessions at a timestamp |
| LONG-06 | long_context | 4 | 4 | 0.30 | final | Inventory state tracking |
| LONG-07 | long_context | 4 | 4 | 0.40 | final | Policy with conflicting amendments |
| LONG-08 | long_context | 5 | 5 | 0.15 | final | Shortest route hidden in a travel guide |
| TRACE-01 | trace | 2 | 2 | 0.85 | final | List aliasing |
| TRACE-02 | trace | 3 | 3 | 0.65 | final | Closures and mutable defaults |
| TRACE-03 | trace | 3 | 3 | 0.60 | final | Stack machine |
| TRACE-04 | trace | 4 | 4 | 0.30 | final | xorshift32 by hand |
| TRACE-05 | trace | 4 | 4 | 0.30 | final | Game of Life on a torus |
| TRACE-06 | trace | 4 | 4 | 0.35 | final | Elementary cellular automaton |
| TRACE-07 | trace | 4 | 4 | 0.45 | final | Register machine |
| TRACE-08 | trace | 5 | 5 | 0.20 | final | Brainfuck with wrap-around |
| AGENT-01 | agent | 1 | 1 | 0.95 | agent | Calculator tools |
| AGENT-02 | agent | 2 | 2 | 0.85 | agent | Find a config in a file tree |
| AGENT-03 | agent | 2 | 2 | 0.85 | agent | Order lookup and aggregation |
| AGENT-04 | agent | 3 | 3 | 0.55 | agent | Constrained flight search |
| AGENT-05 | agent | 3 | 3 | 0.60 | agent | Locate a bug from failing tests |
| AGENT-06 | agent | 4 | 4 | 0.55 | agent | Paginated API aggregation |
| AGENT-07 | agent | 4 | 4 | 0.55 | agent | Stale cache awareness |
| AGENT-08 | agent | 5 | 5 | 0.20 | agent | Delivery robot under a step budget |
| STRUCT-01 | structured | 1 | 1 | 0.95 | raw | Extract fields from an email |
| STRUCT-02 | structured | 2 | 2 | 0.85 | raw | Messy table to clean CSV |
| STRUCT-03 | structured | 3 | 3 | 0.60 | final | Write a strict IPv4 regex |
| STRUCT-04 | structured | 3 | 3 | 0.45 | raw | Group-by average from JSON |
| STRUCT-05 | structured | 3 | 3 | 0.60 | sql | SQL: second-highest salary per department |
| STRUCT-06 | structured | 4 | 4 | 0.45 | sql | SQL: recursive bill of materials |
| SCI-01 | science | 2 | 2 | 0.95 | final | Projectile range |
| SCI-02 | science | 2 | 2 | 0.85 | final | X-linked carrier frequency |
| SCI-03 | science | 3 | 3 | 0.65 | final | Hohmann transfer |
| SCI-04 | science | 4 | 4 | 0.50 | final | Stereoisomer count with a pseudoasymmetric centre |
| SCI-05 | science | 4 | 4 | 0.60 | final | Lanthanide ground-state term |
| LANG-01 | multilingual | 2 | 2 | 0.90 | final | Turkish number words |
| LANG-02 | multilingual | 3 | 3 | 0.60 | final | Japanese mora count |
| LANG-03 | multilingual | 3 | 3 | 0.60 | final | German number words |
| LANG-04 | multilingual | 4 | 4 | 0.55 | final | Turkish agglutination |
