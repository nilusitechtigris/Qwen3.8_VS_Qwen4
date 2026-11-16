"""SCIENCE (5) and MULTILINGUAL (4) tasks."""
from __future__ import annotations

import math

from util import T, exact, fa, num


def sci():
    C = "science"
    out = []
    v, th, g = 30.0, 35.0, 9.81
    R = v * v * math.sin(math.radians(2 * th)) / g
    out.append(T("SCI-01", C, 2, "Projectile range",
                 "A ball is launched from flat ground at 30 m/s at 35 degrees above the horizontal. Ignore air "
                 "resistance and use g = 9.81 m/s^2. How far from the launch point does it land, in metres? Give the "
                 "value to two decimals.",
                 num(f"{R:.4f}", rel_tol=0.003), 0.95, fa(f"{R:.2f}"), wrong=fa(f"{R / 2:.2f}")))
    q = 1 / 50
    carriers = 2 * (1 - q) * q
    out.append(T("SCI-02", C, 2, "X-linked carrier frequency",
                 "An X-linked recessive condition affects 1 in 50 males in a population that is in Hardy-Weinberg "
                 "equilibrium. What fraction of females are heterozygous carriers? Give a decimal number.",
                 num(f"{carriers:.6f}", abs_tol=0.0005), 0.85, fa(f"{carriers:.4f}"), wrong=fa("0.2400")))
    mu, Re = 398600.4418, 6378.137
    r1, r2 = Re + 400.0, 42164.0
    dv1 = math.sqrt(mu / r1) * (math.sqrt(2 * r2 / (r1 + r2)) - 1)
    dv2 = math.sqrt(mu / r2) * (1 - math.sqrt(2 * r1 / (r1 + r2)))
    dv = dv1 + dv2
    out.append(T("SCI-03", C, 3, "Hohmann transfer",
                 "A spacecraft is in a circular orbit 400 km above Earth's surface and performs a two-impulse Hohmann "
                 "transfer to a coplanar circular orbit of radius 42164 km (measured from Earth's centre). Use "
                 "mu = 398600.4418 km^3/s^2 and Earth radius 6378.137 km. What is the total delta-v of the two burns, "
                 "in km/s, to three decimals?",
                 num(f"{dv:.5f}", rel_tol=0.004), 0.65, fa(f"{dv:.3f}"), wrong=fa(f"{dv1:.3f}")))
    out.append(T("SCI-04", C, 4, "Stereoisomer count with a pseudoasymmetric centre",
                 "How many stereoisomers exist for 2,3,4-trihydroxyglutaric acid "
                 "(HOOC-CH(OH)-CH(OH)-CH(OH)-COOH)? Count every distinct stereoisomer (enantiomers count separately, "
                 "meso forms count once each).",
                 num(4, exact=True), 0.50, fa(4), wrong=fa(8)))
    out.append(T("SCI-05", C, 4, "Lanthanide ground-state term",
                 "What is the ground-state term symbol (2S+1)L_J of the free Ho3+ ion according to Hund's rules? "
                 "Write it like 4I15/2 (multiplicity, letter, J).",
                 {"type": "regex", "pattern": r"\^?\{?(5|⁵)\}?\s*I\s*_?\{?(8|₈)\}?"}, 0.60, fa("5I8"), wrong=fa("5I4")))
    return out


def lang():
    C = "multilingual"
    out = []
    out.append(T("LANG-01", C, 2, "Turkish number words",
                 "Write the number 2026 in Turkish words, using correct Turkish spelling (including Turkish letters).",
                 exact("iki bin yirmi altı", ignore_spaces=True), 0.90, fa("iki bin yirmi altı"),
                 wrong=fa("iki bin yirmi alti")))
    words = ["とうきょう", "ほっかいどう", "しんぶん", "きって", "ちゃわん"]
    morae = 0
    small = set("ゃゅょぁぃぅぇぉ")
    for w in words:
        morae += sum(1 for ch in w if ch not in small)
    assert morae == 20
    out.append(T("LANG-02", C, 3, "Japanese mora count",
                 "Count the morae (not syllables) in each of these Japanese words and give the TOTAL for all five: "
                 + "、".join(words) + ". (Small ゃ/ゅ/ょ combine with the preceding kana; っ and ん are morae of their "
                 "own.)",
                 num(morae, exact=True), 0.60, fa(morae), wrong=fa(15)))
    de = "eine Million zweihundertvierunddreißigtausendfünfhundertsiebenundsechzig"
    out.append(T("LANG-03", C, 3, "German number words",
                 "Write the number 1234567 in German words as it would be written out in standard German orthography.",
                 exact(de, de.replace("ß", "ss"), "eine Million zweihundertvierunddreissigtausendfünfhundertsiebenundsechzig",
                       ignore_spaces=True), 0.60, fa(de), wrong=fa("eine Million zweihundertdreiundvierzigtausendfünfhundertsiebenundsechzig")))
    out.append(T("LANG-04", C, 4, "Turkish agglutination",
                 "Give the single Turkish word (with correct vowel harmony, consonant changes and Turkish letters) for "
                 "each of these phrases: (1) 'from our houses' (ev = house); (2) 'in your books', where 'your' is "
                 "second person PLURAL (kitap = book); (3) 'to their cars' (araba = car). Answer with the three words "
                 "in that order, separated by commas.",
                 {"type": "sequence", "items": ["evlerimizden", "kitaplarınızda", "arabalarına"]}, 0.55,
                 fa("evlerimizden, kitaplarınızda, arabalarına"), wrong=fa("evlerimizden, kitaplarinizda, arabalarına")))
    return out


def tasks():
    return sci() + lang()
