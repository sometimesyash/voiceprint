"""Calibrate the identity distance so a number means the same thing every time.

Both arms shrink as text grows, because a longer passage estimates each rate
more precisely, and the two do not run on the same scale. Measured against 24
authors, the same author scores 2.04 on a 300 word passage and 0.49 on a 6,000
word one. A fixed threshold therefore says something different at every length,
which makes "under 1.5 is acceptable" close to meaningless.

This measures the distribution of same-author and different-author distances
across sample sizes, so a raw distance can be reported as a percentile: how
many texts by other people sit closer than this one does. That figure means
the same thing whatever the length.

    python scripts/calibrate_scale.py

Writes voiceprint/data/scale.json.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from voiceprint.distance import burrows_delta
from voiceprint.doc import Doc
from voiceprint.features.lexical import function_word_vector
from voiceprint.texture import blend as blend_arms
from voiceprint.texture import distance as texture_distance
from voiceprint.texture import profile as texture_profile

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "gutenberg"
OUT = ROOT / "voiceprint" / "data" / "scale.json"

PROFILE_WORDS = 20000
SIZES = (200, 400, 800, 1600, 3200, 6400)
TRIALS = 50
QUANTILES = (0.05, 0.25, 0.5, 0.75, 0.95)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--out", type=Path, default=OUT)
    args = ap.parse_args()

    corpora = {p.stem: p.read_text(encoding="utf8", errors="ignore").split()
               for p in sorted(CACHE.glob("*.txt"))}
    if len(corpora) < 5:
        raise SystemExit("no gutenberg cache; run scripts/calibrate.py first")
    authors = list(corpora)

    profiles = {}
    for a in authors:
        head = " ".join(corpora[a][:len(corpora[a]) // 2][:PROFILE_WORDS])
        doc = Doc(head)
        profiles[a] = (function_word_vector(doc), texture_profile(doc))

    table = {}
    print(f"{'words':>6s} {'same median':>12s} {'other median':>13s} "
          f"{'overlap':>8s}")
    print("-" * 44)

    for size in SIZES:
        rng = random.Random(11)
        same, other = [], []
        for _ in range(TRIALS):
            truth = rng.choice(authors)
            tail = corpora[truth][len(corpora[truth]) // 2:]
            if len(tail) < size + 10:
                continue
            start = rng.randrange(0, len(tail) - size)
            doc = Doc(" ".join(tail[start:start + size]))
            fw, tx = function_word_vector(doc), texture_profile(doc)
            for a in authors:
                d, _ = burrows_delta(fw, profiles[a][0])
                t = texture_distance(tx, profiles[a][1])
                blended, _ = blend_arms(d, t, min(size, PROFILE_WORDS))
                (same if a == truth else other).append(blended)

        same.sort()
        other.sort()

        def q(xs, p):
            return round(xs[min(len(xs) - 1, int(p * len(xs)))], 4)

        # How often a different author scores at least as close as the median
        # same-author text. This is the honest measure of how separable the
        # two populations are at this length.
        median_same = statistics.median(same)
        overlap = sum(1 for v in other if v <= median_same) / len(other)

        table[str(size)] = {
            "same": {str(p): q(same, p) for p in QUANTILES},
            "other": {str(p): q(other, p) for p in QUANTILES},
            "overlap": round(overlap, 3),
        }
        print(f"{size:6d} {median_same:12.2f} "
              f"{statistics.median(other):13.2f} {overlap:8.0%}")

    data = {
        "schema": 1,
        "authors": len(corpora),
        "profile_words": PROFILE_WORDS,
        "trials_per_size": TRIALS,
        "sizes": list(SIZES),
        "table": table,
        "note": ("Distribution of blended identity distance by passage "
                 "length, for texts by the same author and by others. Both "
                 "arms shrink as text grows, so a raw distance is not "
                 "comparable across lengths; percentile() in distance.py "
                 "uses this to report how many other-author texts sit closer, "
                 "which is length independent. Overlap is how often a "
                 "different author scores at least as close as the median "
                 "same-author text, and is the honest measure of separability "
                 "at that length. Fiction, so working prose may differ."),
    }
    args.out.write_text(json.dumps(data, indent=1), encoding="utf8")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
