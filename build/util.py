"""Small helpers shared by the category modules."""
from __future__ import annotations

from fractions import Fraction


def T(id, category, tier, title, prompt, grader, est_p, reference, *, mode="final", wrong=None,
      skills=(), notes=""):
    """Create a task dict.

    est_p     : prior estimate of P(pass) for Qwen3.8-27B 4-bit, thinking on (used for calibration).
    reference : a response that MUST pass the grader (self-test).
    wrong     : optional plausible-but-wrong response that MUST fail the grader (self-test).
    """
    assert tier in (1, 2, 3, 4, 5)
    assert 0 < est_p < 1
    return dict(id=id, category=category, tier=tier, weight=tier, title=title, mode=mode,
                prompt=prompt.strip("\n"), grader=grader, est_p=est_p, skills=list(skills),
                notes=notes, reference=reference, wrong=wrong)


def num(value, **kw):
    if isinstance(value, Fraction):
        value = f"{value.numerator}/{value.denominator}" if value.denominator != 1 else str(value.numerator)
    return {"type": "number", "value": str(value), **kw}


def exact(*answers, **kw):
    return {"type": "exact", "answers": list(answers), **kw}


def fa(x) -> str:
    """Reference response with a final answer line."""
    if isinstance(x, Fraction):
        x = f"{x.numerator}/{x.denominator}" if x.denominator != 1 else str(x.numerator)
    return f"Reasoning omitted.\nFINAL ANSWER: {x}"
