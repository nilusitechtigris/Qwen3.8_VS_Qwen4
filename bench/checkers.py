"""Verifiable instruction-following / format checkers. Each returns (passed: bool, detail: str).

Definitions used in the prompts:
  word     = whitespace-separated token containing at least one letter or digit
  sentence = maximal run of text ending with '.', '!' or '?'
  line     = non-empty line after stripping surrounding whitespace
"""
from __future__ import annotations

import json
import re

from .common import extract_final, sentences, words

REGISTRY = {}


def checker(fn):
    REGISTRY[fn.__name__] = fn
    return fn


def _lines(text):
    return [ln.strip() for ln in text.strip().splitlines() if ln.strip()]


def _strip_fence(text):
    t = text.strip()
    m = re.fullmatch(r"```[A-Za-z]*\s*\n(.*?)\n\s*```", t, re.S)
    return m.group(1).strip() if m else t


def _first_alpha(s):
    m = re.search(r"[A-Za-z]", s)
    return m.group(0).upper() if m else ""


EUROPEAN_CAPITALS = {
    "amsterdam", "andorra la vella", "athens", "belgrade", "berlin", "bern", "bratislava", "brussels", "bucharest",
    "budapest", "chisinau", "chișinău", "copenhagen", "dublin", "helsinki", "kyiv", "kiev", "lisbon", "ljubljana",
    "london", "luxembourg", "madrid", "minsk", "monaco", "moscow", "nicosia", "oslo", "paris", "podgorica",
    "prague", "pristina", "reykjavik", "reykjavík", "riga", "rome", "san marino", "sarajevo", "skopje", "sofia",
    "stockholm", "tallinn", "tirana", "vaduz", "valletta", "vatican city", "vienna", "vilnius", "warsaw", "zagreb",
    "ankara", "tbilisi", "yerevan", "baku",
}


@checker
def exact_text(text, expected):
    ok = text.strip() == expected
    return ok, "exact match" if ok else f"expected exactly {expected!r}"


@checker
def json_primes(text, n, greater_than):
    try:
        arr = json.loads(_strip_fence(text))
    except Exception:  # noqa: BLE001
        return False, "output is not valid JSON"
    if not (isinstance(arr, list) and len(arr) == n and all(isinstance(x, int) and not isinstance(x, bool) for x in arr)):
        return False, f"need a JSON array of exactly {n} integers"
    if len(set(arr)) != n:
        return False, "numbers must be distinct"

    def is_prime(k):
        return k > 1 and all(k % d for d in range(2, int(k ** 0.5) + 1))

    bad = [x for x in arr if not (x > greater_than and is_prime(x))]
    return (not bad), "ok" if not bad else f"not primes > {greater_than}: {bad}"


@checker
def sentence_initials(text, letters, min_words, max_words):
    ss = sentences(text)
    if len(ss) != len(letters):
        return False, f"expected {len(letters)} sentences, found {len(ss)}"
    got = "".join(_first_alpha(s) for s in ss)
    if got != letters.upper():
        return False, f"sentence initials {got!r} != {letters!r}"
    n = len(words(text))
    if not (min_words <= n <= max_words):
        return False, f"total words {n} not in [{min_words}, {max_words}]"
    if len(words(" ".join(ss))) != n:
        return False, "text outside of sentences"
    return True, "ok"


@checker
def line_word_counts(text, counts, lowercase, no_punctuation):
    ls = _lines(text)
    if len(ls) != len(counts):
        return False, f"expected {len(counts)} lines, found {len(ls)}"
    for i, (ln, c) in enumerate(zip(ls, counts), 1):
        if len(words(ln)) != c:
            return False, f"line {i} has {len(words(ln))} words, expected {c}"
    if lowercase and text != text.lower():
        return False, "text is not all lowercase"
    if no_punctuation and re.search(r"[^\w\s]", text):
        return False, "punctuation found"
    return True, "ok"


@checker
def capitals_reverse(text, n):
    ls = _lines(text)
    if len(ls) != n:
        return False, f"expected {n} lines, found {len(ls)}"
    items = []
    for ln in ls:
        if not ln.startswith("- "):
            return False, f"line does not start with '- ': {ln!r}"
        items.append(ln[2:].strip().lower())
    unknown = [x for x in items if x not in EUROPEAN_CAPITALS]
    if unknown:
        return False, f"not recognised as European capitals: {unknown}"
    if len(set(items)) != n:
        return False, "duplicates"
    if items != sorted(items, reverse=True):
        return False, "not in reverse alphabetical order"
    return True, "ok"


@checker
def json_summary(text, summary_words, n_keywords):
    try:
        obj = json.loads(_strip_fence(text))
    except Exception:  # noqa: BLE001
        return False, "output is not a valid JSON object"
    if not isinstance(obj, dict) or set(obj) != {"summary", "keywords", "word_count"}:
        return False, "keys must be exactly summary, keywords, word_count"
    s, kw, wc = obj["summary"], obj["keywords"], obj["word_count"]
    if not isinstance(s, str) or len(words(s)) != summary_words:
        return False, f"summary must have exactly {summary_words} words (has {len(words(s)) if isinstance(s, str) else '?'})"
    if wc != summary_words or isinstance(wc, bool):
        return False, "word_count must equal the summary word count as an integer"
    if not (isinstance(kw, list) and len(kw) == n_keywords and all(isinstance(k, str) for k in kw)):
        return False, f"keywords must be a list of {n_keywords} strings"
    if any(not re.fullmatch(r"[a-z]+", k) for k in kw) or len(set(kw)) != n_keywords:
        return False, "keywords must be distinct single lowercase words"
    if kw != sorted(kw):
        return False, "keywords must be sorted alphabetically"
    summary_tokens = {re.sub(r"[^a-z]", "", w.lower()) for w in words(s)}
    missing = [k for k in kw if k not in summary_tokens]
    if missing:
        return False, f"keywords not found as words in the summary: {missing}"
    return True, "ok"


@checker
def acrostic(text, word, words_per_line, must_word, must_count):
    ls = _lines(text)
    if len(ls) != len(word):
        return False, f"expected {len(word)} lines, found {len(ls)}"
    got = "".join(_first_alpha(ln) for ln in ls)
    if got != word.upper():
        return False, f"acrostic {got!r} != {word!r}"
    for i, ln in enumerate(ls, 1):
        if len(words(ln)) != words_per_line:
            return False, f"line {i} has {len(words(ln))} words"
    c = len(re.findall(rf"\b{re.escape(must_word)}\b", text, re.I))
    if c != must_count:
        return False, f"'{must_word}' appears {c} times, expected {must_count}"
    return True, "ok"


@checker
def fixed_sentence_length(text, words_per_sentence, min_words, max_words):
    ss = sentences(text)
    n = len(words(text))
    if not ss:
        return False, "no sentences"
    if len(words(" ".join(ss))) != n:
        return False, "text outside of sentences"
    bad = [i for i, s in enumerate(ss, 1) if len(words(s)) != words_per_sentence]
    if bad:
        return False, f"sentences {bad[:5]} do not have exactly {words_per_sentence} words"
    if not (min_words <= n <= max_words):
        return False, f"total words {n} not in [{min_words}, {max_words}]"
    return True, "ok"


@checker
def lipogram(text, letter, min_words, max_words, must_include):
    if letter.lower() in text.lower():
        idx = text.lower().index(letter.lower())
        return False, f"letter '{letter}' found near: {text[max(0, idx - 20):idx + 20]!r}"
    n = len(words(text))
    if not (min_words <= n <= max_words):
        return False, f"word count {n} not in [{min_words}, {max_words}]"
    for w in must_include:
        if not re.search(rf"\b{re.escape(w)}\b", text, re.I):
            return False, f"must include the word {w!r}"
    return True, "ok"


@checker
def increasing_chain(text, min_sentences, min_words, max_words):
    ss = sentences(text)
    n = len(words(text))
    if len(ss) < min_sentences:
        return False, f"need at least {min_sentences} sentences, found {len(ss)}"
    if len(words(" ".join(ss))) != n:
        return False, "text outside of sentences"
    lens = [len(words(s)) for s in ss]
    if any(b <= a for a, b in zip(lens, lens[1:])):
        return False, f"sentence lengths not strictly increasing: {lens}"
    for i in range(len(ss) - 1):
        last = _first_alpha(words(ss[i])[-1])
        first = _first_alpha(words(ss[i + 1])[0])
        if last != first:
            return False, f"chain broken between sentence {i + 1} ('{words(ss[i])[-1]}') and {i + 2} ('{words(ss[i + 1])[0]}')"
    if not (min_words <= n <= max_words):
        return False, f"total words {n} not in [{min_words}, {max_words}]"
    return True, "ok"


@checker
def staircase_acrostic(text, word, forbidden, letter_to_count, letter_count):
    ls = _lines(text)
    if len(ls) != len(word):
        return False, f"expected {len(word)} lines, found {len(ls)}"
    for k, ln in enumerate(ls, 1):
        if len(words(ln)) != k:
            return False, f"line {k} has {len(words(ln))} words, expected {k}"
        end = "?" if k == len(ls) else "."
        if not ln.endswith(end):
            return False, f"line {k} must end with '{end}'"
    got = "".join(_first_alpha(ln) for ln in ls)
    if got != word.upper():
        return False, f"acrostic {got!r} != {word!r}"
    if forbidden.lower() in text.lower():
        return False, f"forbidden letter '{forbidden}' used"
    c = text.lower().count(letter_to_count.lower())
    if c != letter_count:
        return False, f"letter '{letter_to_count}' appears {c} times, expected {letter_count}"
    return True, "ok"


@checker
def email_json(text, expected):
    try:
        obj = json.loads(_strip_fence(text))
    except Exception:  # noqa: BLE001
        return False, "not valid JSON"
    if not isinstance(obj, dict) or set(obj) != set(expected):
        return False, f"keys must be exactly {sorted(expected)}"
    for k, v in expected.items():
        got = obj[k]
        if isinstance(v, float):
            if not isinstance(got, (int, float)) or isinstance(got, bool) or abs(got - v) > 1e-9:
                return False, f"{k}: expected number {v}"
        elif isinstance(v, str):
            if not isinstance(got, str) or got.strip().lower() != v.lower():
                return False, f"{k}: expected {v!r}"
        elif got != v:
            return False, f"{k}: expected {v!r}"
    return True, "ok"


@checker
def csv_exact(text, expected_rows):
    body = _strip_fence(text)
    rows = [[c.strip() for c in ln.split(",")] for ln in body.splitlines() if ln.strip()]
    ok = rows == expected_rows
    return ok, "ok" if ok else f"rows differ (got {rows[:3]}...)"


@checker
def regex_tester(text, positives, negatives):
    ans = extract_final(text)
    if not ans:
        return False, "no FINAL ANSWER"
    pat = ans.strip()
    if len(pat) >= 2 and pat[0] == pat[-1] == "/":
        pat = pat[1:-1]
    try:
        rx = re.compile(pat)
    except re.error as e:
        return False, f"invalid regex: {e}"
    fp = [s for s in negatives if rx.fullmatch(s)]
    fn = [s for s in positives if not rx.fullmatch(s)]
    if fp or fn:
        return False, f"wrongly accepted {fp[:3]}, wrongly rejected {fn[:3]}"
    return True, "ok"


@checker
def json_object_exact(text, expected, tol):
    try:
        obj = json.loads(_strip_fence(text))
    except Exception:  # noqa: BLE001
        return False, "not valid JSON"
    if not isinstance(obj, dict) or set(obj) != set(expected):
        return False, f"keys must be exactly {sorted(expected)}"
    for k, v in expected.items():
        g = obj[k]
        if not isinstance(g, (int, float)) or isinstance(g, bool) or abs(g - v) > tol:
            return False, f"{k}: expected {v}, got {g}"
    if list(obj) != sorted(obj):
        return False, "keys must be sorted"
    return True, "ok"
