"""Qwen3.8 vs Qwen4 (27B, 4-bit) comparison benchmark."""

TIER_NAMES = {1: "T1 warm-up", 2: "T2 standard", 3: "T3 hard", 4: "T4 very hard", 5: "T5 frontier"}
TIER_WEIGHT = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}
