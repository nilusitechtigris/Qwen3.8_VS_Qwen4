"""INSTRUCTION FOLLOWING: 11 tasks with fully verifiable constraints (checked by bench/checkers.py)."""
from __future__ import annotations

import json

from util import T

C = "instruction"

DEFS = ("\n\nDefinitions used for checking: a word is any whitespace-separated token that contains at least one "
        "letter or digit; a sentence is a run of text ending with '.', '!' or '?'; a line is a non-empty line of "
        "output. Output ONLY the requested text: no title, no preamble, no explanation, no 'FINAL ANSWER' line.")


def chk(name, **params):
    return {"type": "checker", "name": name, "params": params}


REF_I08 = ("The harbor wakes early when the fishing boats start their noisy engines. "
           "Gulls circle above the masts and argue loudly over scraps of bait. "
           "A baker on the corner opens his shutters and sets out bread. "
           "Tourists arrive by nine with cameras, maps, and very large straw hats. "
           "Children run along the pier and count the ropes tied to bollards. "
           "By noon the sun is high and water shines like hammered metal. "
           "Old sailors sit on benches and trade stories that grow longer yearly. "
           "In the afternoon a ferry leaves for the islands across the bay. "
           "Evening brings cooler air, orange light, and the smell of grilled fish. "
           "Finally the lanterns glow and the harbor settles into a quiet sleep.")
REF_I09 = ("A small cat sat on a warm windowsill all day long. It was gray and soft, with big round gold pupils "
           "that saw birds fly past. Now and again it would yawn, arch its long body, and curl back into a tidy "
           "ball. A child ran in, calling softly, and it slowly got up to follow. Cat and child ran out into a "
           "sunny yard full of tall grass and buzzing bugs. That cat found a cozy spot, lay down, and shut its "
           "lids again, purring softly.")
REF_I10 = ("Morning light crept slowly over the quiet town and its sleepy streets. "
           "Smoke from tall chimneys drifted upward into the pale sky above the old harbor. "
           "Hungry gulls screamed while fishermen unloaded crates of silver mackerel onto the busy wet wooden dock. "
           "Down the lane, shopkeepers unlocked their doors, swept the dusty steps, and arranged baskets of fruit in rows. "
           "Riders on bicycles weaved between carts while a street musician played cheerful tunes for anyone willing to stop and listen. "
           "Later, as the sun climbed higher, the town gathered in the square to share bread, cheese, gossip, and stories about the sea.")
REF_I11 = """Birds.
Every dawn.
Night slowly fades.
Clouds drift past quietly.
Hills glow and catch light.
Many small creatures slowly begin moving.
A gentle wind brushes the tall grass.
Rivers carry cold water down to the sea.
Kind farmers walk early to the fields with tools.
So why do people sleep through such a beautiful dawn?"""

PRINTING = ("Around 1440 in Mainz, Johannes Gutenberg combined a screw press, oil-based ink and durable metal "
            "movable type into a practical printing system. Within fifty years presses were operating in more than "
            "two hundred European towns, and millions of books had been produced. The falling cost of books helped "
            "literacy spread, allowed scholars to share identical texts, supported the rapid circulation of "
            "Reformation pamphlets, and later made the exchange of scientific results far faster than hand copying "
            "ever could.")


def tasks():
    out = []
    out.append(T("IF-01", C, 1, "Single-token reply",
                 "Reply with exactly the word ACKNOWLEDGED in uppercase letters and nothing else - no punctuation, "
                 "no quotes, no other words.",
                 chk("exact_text", expected="ACKNOWLEDGED"), 0.97, "ACKNOWLEDGED", mode="raw",
                 wrong="ACKNOWLEDGED."))
    out.append(T("IF-02", C, 1, "JSON array of primes",
                 "Output a JSON array containing exactly 5 distinct prime numbers that are each greater than 100. "
                 "Output only the JSON array.",
                 chk("json_primes", n=5, greater_than=100), 0.96, "[101, 103, 107, 109, 113]", mode="raw",
                 wrong="[101, 103, 107, 109, 111]"))
    out.append(T("IF-03", C, 2, "Sentence initials and length",
                 "Write exactly 3 sentences about the ocean. The first sentence must begin with the letter O, the "
                 "second with C and the third with E. The whole text must contain between 30 and 45 words in total."
                 + DEFS,
                 chk("sentence_initials", letters="OCE", min_words=30, max_words=45), 0.85,
                 "Oceans cover most of our planet and shape the weather that every living thing depends on. "
                 "Currents carry heat from the tropics toward the poles in slow, enormous loops. "
                 "Every wave that reaches the shore began as wind somewhere far away.", mode="raw",
                 wrong="Oceans are vast. Currents move. Every wave matters."))
    out.append(T("IF-04", C, 2, "Three lines with exact word counts",
                 "Write three lines about autumn. Line 1 must have exactly 5 words, line 2 exactly 7 words and line 3 "
                 "exactly 5 words. Use only lowercase letters and spaces: no punctuation of any kind, no capital "
                 "letters." + DEFS,
                 chk("line_word_counts", counts=[5, 7, 5], lowercase=True, no_punctuation=True), 0.85,
                 "cold leaves drift across roads\nthe maple trees glow red and gold\nsoon the branches will rest",
                 mode="raw", wrong="Cold leaves drift across roads\nthe maple trees glow red and gold\nsoon the branches rest"))
    out.append(T("IF-05", C, 2, "Sorted bullet list",
                 "List exactly 7 different capital cities of European countries, one per line, each line formatted as "
                 "'- City' (a hyphen, a space, then the English name of the city). The list must be in reverse "
                 "alphabetical order (Z to A). Output nothing else." + DEFS,
                 chk("capitals_reverse", n=7), 0.85, "- Warsaw\n- Vienna\n- Rome\n- Paris\n- Oslo\n- Madrid\n- Berlin",
                 mode="raw", wrong="- Berlin\n- Madrid\n- Oslo\n- Paris\n- Rome\n- Vienna\n- Warsaw"))
    out.append(T("IF-06", C, 3, "Structured summary with self-consistency",
                 "Summarize the paragraph below as a JSON object with exactly these keys:\n"
                 "- \"summary\": a summary of exactly 25 words;\n"
                 "- \"keywords\": a list of exactly 5 distinct single lowercase words (letters a-z only), sorted "
                 "alphabetically, each of which appears as a word in your summary (ignoring case and punctuation);\n"
                 "- \"word_count\": the integer number of words in your summary.\n"
                 "Output only the JSON object.\n\nParagraph:\n" + PRINTING + DEFS,
                 chk("json_summary", summary_words=25, n_keywords=5), 0.60,
                 json.dumps({"summary": "Johannes Gutenberg built a movable type printing press around 1440, which made "
                                        "books cheaper, spread literacy across Europe, and accelerated rapid scientific "
                                        "and religious change.",
                             "keywords": ["books", "europe", "literacy", "press", "printing"], "word_count": 25}),
                 mode="raw",
                 wrong=json.dumps({"summary": "Gutenberg built a printing press around 1440 that made books cheaper.",
                                   "keywords": ["books", "cheaper", "gutenberg", "press", "printing"],
                                   "word_count": 11})))
    out.append(T("IF-07", C, 3, "Acrostic with word quotas",
                 "Write a poem of exactly 8 lines about model quantization. The first letters of the lines, read top "
                 "to bottom, must spell QUANTIZE. Every line must contain exactly 6 words. The word \"model\" (as a "
                 "whole word, any capitalization; \"models\" does not count) must appear exactly twice in the whole "
                 "poem." + DEFS,
                 chk("acrostic", word="QUANTIZE", words_per_line=6, must_word="model", must_count=2), 0.50,
                 "Quiet weights shrink inside the model.\nUnder four bits, precision fades slowly.\n"
                 "Accuracy drops a little each time.\nNumbers round toward the nearest step.\n"
                 "Tiny errors gather but rarely explode.\nIn practice the model still reasons.\n"
                 "Zero points and scales guide recovery.\nEvery layer keeps its essential shape.", mode="raw"))
    out.append(T("IF-08", C, 4, "Every sentence exactly 12 words",
                 "Write a short descriptive text about a day in a small harbor town. Every sentence must contain "
                 "exactly 12 words, and the whole text must contain between 120 and 140 words. Do not use "
                 "abbreviations, decimal numbers or any other periods inside sentences." + DEFS,
                 chk("fixed_sentence_length", words_per_sentence=12, min_words=120, max_words=140), 0.45, REF_I08,
                 mode="raw"))
    out.append(T("IF-09", C, 4, "Lipogram",
                 "Write a story of 80 to 100 words about a cat. The story must include the word \"cat\" at least "
                 "once and must NOT contain the letter 'e' anywhere (neither lowercase nor uppercase)." + DEFS,
                 chk("lipogram", letter="e", min_words=80, max_words=100, must_include=["cat"]), 0.30, REF_I09,
                 mode="raw", wrong=REF_I09 + " The end."))
    out.append(T("IF-10", C, 4, "Growing, chained sentences",
                 "Write a paragraph about a market morning with at least 6 sentences and between 100 and 130 words "
                 "in total. Each sentence must contain strictly more words than the previous one. In addition, the "
                 "last word of each sentence must begin with the same letter (ignoring case) as the first word of the "
                 "next sentence." + DEFS,
                 chk("increasing_chain", min_sentences=6, min_words=100, max_words=130), 0.40, REF_I10, mode="raw"))
    out.append(T("IF-11", C, 5, "Staircase acrostic with a letter budget",
                 "Write exactly 10 lines satisfying ALL of the following:\n"
                 "1. Line k contains exactly k words (line 1 has 1 word, line 2 has 2 words, ..., line 10 has 10 words).\n"
                 "2. The first letters of the lines spell BENCHMARKS.\n"
                 "3. Lines 1 to 9 each end with a period; line 10 ends with a question mark.\n"
                 "4. The letter 'z' does not appear anywhere.\n"
                 "5. The letter 'a' (counting both 'a' and 'A') appears exactly 20 times in total." + DEFS,
                 chk("staircase_acrostic", word="BENCHMARKS", forbidden="z", letter_to_count="a", letter_count=20),
                 0.10, REF_I11, mode="raw", wrong=REF_I11.replace("Every dawn.", "Every morning.")))
    return out
