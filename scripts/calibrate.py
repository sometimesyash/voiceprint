"""Measure what the tool can and cannot resolve, then store the answer.

Held-out authorship attribution across public domain authors, swept over both
profile size and passage size. The resulting table is what the confidence
tiers and the minimum-length guard are set from, so those numbers stop being
guesses.

    python scripts/calibrate.py

Writes voiceprint/data/calibration.json. Populates a Gutenberg cache on first
run, shared with build_baseline.py.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from voiceprint.doc import Doc
from voiceprint.features.lexical import function_word_vector
from voiceprint.lexicons import FUNCTION_WORDS
from voiceprint.texture import blend as blend_arms
from voiceprint.texture import distance as texture_distance
from voiceprint.texture import profile as texture_profile

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "voiceprint" / "data" / "calibration.json"
CACHE = ROOT / ".cache" / "gutenberg"
BASELINE = ROOT / "voiceprint" / "data" / "baseline.json"

PROFILE_SIZES = (2500, 5000, 10000, 20000, 40000)
PASSAGE_SIZES = (400, 800, 1600, 3200, 6400)
TRIALS = 40

from build_baseline import GUTENBERG, strip_gutenberg  # noqa: E402


def load() -> dict[str, list[str]]:
    CACHE.mkdir(parents=True, exist_ok=True)
    out = {}
    for name, ident in GUTENBERG.items():
        cached = CACHE / f"{name}.txt"
        if not cached.exists():
            for url in (f"https://www.gutenberg.org/files/{ident}/{ident}-0.txt",
                        f"https://www.gutenberg.org/cache/epub/{ident}/pg{ident}.txt"):
                try:
                    with urllib.request.urlopen(url, timeout=30) as r:
                        body = strip_gutenberg(
                            r.read().decode("utf8", errors="ignore"))
                    if len(body) > 20_000:
                        cached.write_text(body, encoding="utf8")
                        break
                except Exception:
                    continue
        if cached.exists():
            out[name] = cached.read_text(encoding="utf8", errors="ignore").split()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--out", type=Path, default=OUT)
    args = ap.parse_args()

    stats = json.loads(BASELINE.read_text(encoding="utf8"))["stats"]
    words = [w for w in FUNCTION_WORDS if stats[w][1] > 0]

    def delta(obs, ref):
        return statistics.fmean(
            [abs(obs[w] - ref[w]) / stats[w][1] for w in words])

    corpora = load()
    if len(corpora) < 5:
        raise SystemExit(f"only {len(corpora)} authors cached")
    authors = list(corpora)
    chance = 1 / len(authors)
    print(f"{len(authors)} authors, chance {chance:.0%}, "
          f"{TRIALS} trials per cell\n")

    grid: dict[str, dict[str, float]] = {"delta": {}, "texture": {},
                                         "blended": {}}
    for arm in ("delta", "texture", "blended"):
        print(f"[{arm}]")
        print(f"{'profile':>9s} " + "".join(f"{n:>8d}" for n in PASSAGE_SIZES))
        print("-" * (9 + 8 * len(PASSAGE_SIZES)))
        for pw in PROFILE_SIZES:
            heads = {a: " ".join(corpora[a][:len(corpora[a]) // 2][:pw])
                     for a in authors}
            prof_fw = {a: function_word_vector(Doc(heads[a])) for a in authors}
            prof_tx = {a: texture_profile(Doc(heads[a])) for a in authors}
            row = []
            for tw in PASSAGE_SIZES:
                rng = random.Random(3)
                hits = n = 0
                for _ in range(TRIALS):
                    truth = rng.choice(authors)
                    tail = corpora[truth][len(corpora[truth]) // 2:]
                    if len(tail) < tw + 10:
                        continue
                    start = rng.randrange(0, len(tail) - tw)
                    doc = Doc(" ".join(tail[start:start + tw]))
                    obs_fw = function_word_vector(doc)
                    obs_tx = texture_profile(doc) if arm != "delta" else {}
                    scores = {}
                    for a in authors:
                        d = delta(obs_fw, prof_fw[a])
                        if arm == "delta":
                            scores[a] = d
                        else:
                            t = texture_distance(obs_tx, prof_tx[a])
                            scores[a] = t if arm == "texture" else \
                                blend_arms(d, t, min(tw, pw))[0]
                    hits += min(scores, key=scores.get) == truth
                    n += 1
                acc = round(hits / n, 3) if n else 0.0
                grid[arm][f"{pw}x{tw}"] = acc
                row.append(acc)
            print(f"{pw:9d} " + "".join(f"{v:8.0%}" for v in row))
        print()

    data = {
        "schema": 2,
        "authors": len(corpora),
        "chance": round(chance, 4),
        "trials_per_cell": TRIALS,
        "profile_sizes": list(PROFILE_SIZES),
        "passage_sizes": list(PASSAGE_SIZES),
        "accuracy": grid["blended"],
        "by_arm": grid,
        "note": ("Held-out attribution over public domain fiction. Profiles "
                 "come from the first half of each author's text and passages "
                 "from the second, so no passage appears in the profile it is "
                 "scored against. Three arms are compared: function-word "
                 "Delta, character n-gram texture, and the size-weighted "
                 "blend the tool actually uses. Texture dominates on short "
                 "samples and Delta catches up as text grows, which is why "
                 "the blend follows sample size. Fiction, so working prose "
                 "may differ."),
    }
    args.out.write_text(json.dumps(data, indent=1), encoding="utf8")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
