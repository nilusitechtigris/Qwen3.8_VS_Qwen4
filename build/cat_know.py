"""KNOWLEDGE: 10 long-tail factual questions with stable, checkable answers.
Where possible the answer is verified locally (unicodedata, hashlib, primality)."""
from __future__ import annotations

import hashlib
import unicodedata

from util import T, exact, fa, num

C = "knowledge"


def is_prime(n):
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


def lucas_lehmer(p):
    if p == 2:
        return True
    m = (1 << p) - 1
    s = 4
    for _ in range(p - 2):
        s = (s * s - 2) % m
    return s == 0


def tasks():
    out = []
    out.append(T("KNOW-01", C, 1, "Element symbol",
                 "What is the chemical symbol of tungsten?",
                 exact("W", case_sensitive=True), 0.99, fa("W"), wrong=fa("Tu")))
    out.append(T("KNOW-02", C, 2, "Bieberbach conjecture",
                 "Which mathematician proved the Bieberbach conjecture in 1984 (published 1985)? Give the surname.",
                 exact("de Branges", "Louis de Branges", "de Branges de Bourcia", "Louis de Branges de Bourcia"),
                 0.85, fa("de Branges"), wrong=fa("Bieberbach")))
    out.append(T("KNOW-03", C, 2, "Ytterby elements",
                 "Four chemical elements are named after the Swedish village of Ytterby. Which of them has the "
                 "highest atomic number?",
                 exact("ytterbium", "Yb"), 0.80, fa("Ytterbium"), wrong=fa("Erbium")))
    # smallest Mersenne prime exponent above 1000, verified with Lucas-Lehmer
    p = next(q for q in range(1001, 3000) if is_prime(q) and lucas_lehmer(q))
    out.append(T("KNOW-04", C, 3, "Mersenne prime exponent",
                 "What is the smallest prime p greater than 1000 such that 2^p - 1 is prime?",
                 num(p, exact=True), 0.55, fa(p), wrong=fa(2203)))
    cp = f"U+{ord(chr(0x131)):04X}"
    assert unicodedata.name(chr(0x131)) == "LATIN SMALL LETTER DOTLESS I"
    out.append(T("KNOW-05", C, 3, "Unicode code point",
                 "What is the Unicode code point of LATIN SMALL LETTER DOTLESS I (the Turkish letter 'ı')? Answer in "
                 "the form U+XXXX.",
                 {"type": "regex", "pattern": r"U\+0?131"}, 0.55, fa(cp), wrong=fa("U+0130")))
    out.append(T("KNOW-06", C, 3, "HTTP semantics RFC",
                 "Which RFC number is the June 2022 IETF standard titled \"HTTP Semantics\"?",
                 {"type": "regex", "pattern": r"(RFC\s*)?9110"}, 0.50, fa("RFC 9110"), wrong=fa("RFC 7231")))
    out.append(T("KNOW-07", C, 4, "ISO 3166 numeric code",
                 "Which country has the ISO 3166-1 numeric country code 792?",
                 exact("Turkey", "Türkiye", "Turkiye", "Republic of Turkey", "Republic of Türkiye"), 0.45,
                 fa("Türkiye"), wrong=fa("Turkmenistan")))
    name = unicodedata.name(chr(0xA66E))
    out.append(T("KNOW-08", C, 4, "Obscure Unicode character name",
                 "What is the official Unicode character name of code point U+A66E? Give the name exactly as in the "
                 "Unicode standard (uppercase).",
                 exact(name), 0.30, fa(name), wrong=fa("CYRILLIC LETTER MONOGRAPH UK")))
    h = hashlib.sha256(b"abc").hexdigest()[:8]
    out.append(T("KNOW-09", C, 4, "SHA-256 test vector",
                 "What are the first 8 hexadecimal characters (lowercase) of the SHA-256 digest of the 3-byte ASCII "
                 "string \"abc\"?",
                 exact(h), 0.40, fa(h), wrong=fa("e3b0c442")))
    name2 = unicodedata.name(chr(0x2E2E))
    out.append(T("KNOW-10", C, 5, "Unicode punctuation name",
                 "What is the official Unicode character name of code point U+2E2E? Give the name exactly as in the "
                 "Unicode standard (uppercase).",
                 exact(name2), 0.12, fa(name2), wrong=fa("IRONY MARK")))
    return out
