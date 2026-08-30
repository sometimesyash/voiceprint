"""Does the measure actually tell people apart?

Every text is scored against every author's profile, and a text is NEVER
scored against a profile built from it. Anything less is not a test, and an
earlier version of this script made exactly that mistake: two of its four
cases scored a text against itself, self-scored zero, and were counted as
successes.

    python scripts/discrimination.py --corpus DIR

DIR holds one folder per author. With no argument it uses the local corpus.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from voiceprint.corpus import Corpus, Sample
from voiceprint.distance import burrows_delta, delta_is_calibrated
from voiceprint.doc import Doc
from voiceprint.features.lexical import function_word_vector
from voiceprint.profile import build
from voiceprint.texture import blend as blend_arms
from voiceprint.texture import distance as texture_distance
from voiceprint.texture import profile as texture_profile

DEFAULT = Path(__file__).resolve().parent.parent.parent / "corpus"


def authors_from(root: Path) -> dict[str, list[Path]]:
    if (root / "email").is_dir():
        return {
            "yash": sorted((root / "email").glob("*.txt"))
                    + sorted((root / "holdout").glob("*.txt")),
            "other-b": [root / "other" / "author-b.txt"],
            "other-c": [root / "other" / "author-c.txt"],
        }
    return {p.name: sorted(p.rglob("*.txt"))
            for p in sorted(root.iterdir()) if p.is_dir()}


def profile_from(paths: list[Path]):
    c = Corpus()
    for p in paths:
        c.add(Sample(p.read_text(encoding="utf8"), origin=p.name,
                     register="email"))
    return build(c, "x").pooled if c.samples else None


def score(doc: Doc, prof, arm: str) -> float:
    delta, _ = burrows_delta(function_word_vector(doc), prof.function_words)
    texture = texture_distance(texture_profile(doc), prof.texture)
    if arm == "delta":
        return delta
    if arm == "texture":
        return texture
    support = min(doc.n_words, prof.words) if prof.words else doc.n_words
    return blend_arms(delta, texture, support)[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", type=Path, default=DEFAULT)
    args = ap.parse_args()

    authors = {a: [p for p in ps if p.is_file()]
               for a, ps in authors_from(args.corpus).items()}
    authors = {a: ps for a, ps in authors.items() if ps}
    if len(authors) < 2:
        raise SystemExit("need at least two authors")

    print(f"Delta calibrated against a between-author reference: "
          f"{delta_is_calibrated()}\n")
    for a, ps in authors.items():
        words = sum(len(p.read_text(encoding="utf8").split()) for p in ps)
        print(f"  {a:10s} {len(ps)} texts, {words:,} words")
    print()

    names = list(authors)
    for arm in ("delta", "texture", "blended"):
        header = f"[{arm}] {'held-out text':24s}" + "".join(
            f"{a:>11s}" for a in names)
        print(header)
        print("-" * len(header))
        hits = total = 0
        for truth, paths in authors.items():
            for held in paths:
                scores, usable = {}, True
                for a in names:
                    train = [p for p in authors[a] if p != held]
                    prof = profile_from(train) if train else None
                    if prof is None:
                        usable = False
                        break
                    scores[a] = score(Doc(held.read_text(encoding="utf8")),
                                      prof, arm)
                if not usable:
                    continue
                win = min(scores, key=scores.get)
                hits += win == truth
                total += 1
                row = "".join(f"{scores[a]:11.3f}" for a in names)
                print(f"{'':7s}{truth + '/' + held.stem:24s}{row}   -> {win}"
                      f"{'' if win == truth else '   WRONG'}")
        if total:
            print(f"{'':7s}accuracy {hits}/{total} = {hits/total:.0%}  "
                  f"(chance {1/len(names):.0%})\n")


if __name__ == "__main__":
    main()
