"""
Regression check for app/parser.py, covering real parsing bugs found by comparing the
parser's output against actual uploaded lab reports (Tata 1mg, a Thyrocare-style report with
duplicated infographic sections, and an NIPT/prenatal screening report).

Not a pytest suite - deliberately dependency-free so it can run with just the stdlib. Each
case is the minimal snippet that reproduces the original bug, not the full multi-page report
(those aren't committed to the repo - they're real patient data).

Run: python app/parser_selfcheck.py
"""
import re
import sys

from app.parser import (
    BIOMARKER_DICTIONARY, STOPWORDS, BLACKLIST_EXACT_NAMES, UNIT_ONLY_NORMALIZED_KEYS,
    parse_lab_data,
)

failures = []


def check(label, condition):
    if not condition:
        failures.append(label)
        print(f"FAIL: {label}")
    else:
        print(f"ok:   {label}")


def names(text):
    _, tests = parse_lab_data(text)
    return {t["test_name"]: t for t in tests}


# --- Dictionary-safety check: the new rejection word-lists must never collide with a real
# biomarker name, or they'd silently delete legitimate results. ---
def check_wordlists_safe():
    checked = 0
    for alias, meta in BIOMARKER_DICTIONARY.items():
        for text in (alias, meta["name"]):
            checked += 1
            words = re.findall(r"[a-z0-9']+", text.lower())
            hit = [w for w in words if w in STOPWORDS]
            if hit:
                failures.append(f"stopword collision: {text!r} contains {hit}")
            if text.lower() in BLACKLIST_EXACT_NAMES:
                failures.append(f"blacklist collision: {text!r}")
            norm = re.sub(r'[^a-z0-9]', '', text.lower())
            if norm in UNIT_ONLY_NORMALIZED_KEYS:
                failures.append(f"unit-only collision: {text!r}")
    print(f"{'FAIL' if any('collision' in f for f in failures) else 'ok  '}: "
          f"word-list safety across {checked} dictionary entries")


check_wordlists_safe()

# --- Apolipoprotein: a PDF kerning glitch splits the decimal ("106.0 0 mg/dL") so the old
# parser matched only the stray trailing "0" as the value. ---
r = names("Apolipoprotein - A1     106.0 0 mg/dL 79 - 169\n")
check("Apo A1 decimal-split merge", r.get("Apolipoprotein - A1", {}).get("value") == 106.0)

# --- Microalbumin-Albumin must NOT be relabeled to plain "Albumin" (a word-boundary match on
# the short alias "albumin" inside the compound name used to steal the row). Both are real,
# distinct tests and must come out separately. ---
r = names(
    "Microalbumin-Albumin    5.90 mg/L    0 - 29.99\n"
    "Albumin                 4.10 g/dL    3.2 - 4.8\n"
)
check("Microalbumin-Albumin kept distinct", "Microalbumin-Albumin" in r)
check("Albumin not overwritten by Microalbumin row", r.get("Albumin", {}).get("value") == 4.10)

# --- ESR is purely numeric (mm/hr); "Reactive" leaking in from an adjacent column must be
# rejected, not saved as if ESR could be a serology-style result. ---
r = names("Erythrocyte Sedimentation Rate C-Reactive Protein (Quantitative)\n")
check("ESR/Reactive cross-column garbage rejected", "Erythrocyte Sedimentation Rate (ESR)" not in r)

# --- pH, unlike ESR, genuinely IS reported qualitatively in some reports - must still work. ---
r = names("Urine Reaction (pH)    Acidic    4.6 - 8.0\n")
check("pH/Acidic still accepted (not over-blocked by the ESR fix)", "Urine Reaction (pH)" in r)

# --- NIPT risk-summary table collapses two grid columns onto one text line; a name containing
# a bare risk ratio like "1:5738" is never a real biomarker. ---
r = names("Biochemical T21 risk        1:5738 Nasal bone                present\n")
check("digit:digit ratio name rejected", len(r) == 0)

# --- Legend/label fragments and narrative sentence fragments from a Thyrocare-style dashboard
# section that duplicates already-captured table data. ---
for line, desc in [
    ("Range: NEGATIVE Range: NEGATIVE\n", "bare 'Range:' legend strip"),
    ("Negative        1-2 /hpf    Nil /hpf\n", "bare 'Negative' as name"),
    ("Even 5 Minutes Of Exercise Strech During\n", "promo blurb w/ bare 'min' unit"),
    ("with an estimated prevalence of 30 %\n", "narrative sentence fragment (stopword)"),
    ("High     Normal\n", "legend word 'High' as name"),
]:
    r = names(line)
    check(f"noise rejected: {desc}", len(r) == 0)

# --- A test name wrapped onto the next physical line ("PAPP-A (Pregnancy Associated Plasma" /
# "Protein)") should be reassembled, not left truncated with an unmatched paren. ---
r = names("PAPP-A (Pregnancy Associated Plasma 7.500 mIU/mL           CLIA\nProtein)\n")
check("wrapped name reassembled", "PAPP-A (Pregnancy Associated Plasma Protein)" in r)

# --- "fb-hCG" (an abbreviation, appearing a second time in a different table layout) must
# dedupe against "Free Beta HCG" rather than create a second, wrongly-referenced row; and a
# bare number with no dash/comparator must never be accepted as a reference range. ---
r = names(
    "Free Beta HCG           29.40       ng/mL                  CLIA\n"
    "fb-hCG       29.4ng/ml       1.02 Scan date                25-01-2026\n"
)
check("fb-hCG dedupes into Free Beta hCG", len([k for k in r if 'hcg' in k.lower()]) == 1)
check("bare-number ref not adopted", r.get("Free Beta hCG", {}).get("reference_range", "") == "")

# --- Sanity check: filters must not be so aggressive they reject a completely normal row. ---
r = names("Glucose- Random         82          mg/dL   70-140         Hexokinase/G-6-PDH\n")
check("normal clean row still parses", r.get("Glucose- Random", {}).get("value") == 82.0)

print()
if failures:
    print(f"{len(failures)} check(s) failed:")
    for f in failures:
        print(" -", f)
    sys.exit(1)
else:
    print("All checks passed.")
