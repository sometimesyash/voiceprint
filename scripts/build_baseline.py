"""Build the multi-author baseline that Delta needs.

Burrows's Delta standardises each word against its variation ACROSS authors.
Without that the measure cannot know which words separate people, so this
derives per-word means and standard deviations from a corpus of many authors
writing separately.

Source texts come from Project Gutenberg, which is public domain, or from any
directory of per-author folders passed on the command line. The result is
committed as voiceprint/data/baseline.json so the package stays offline.

    python scripts/build_baseline.py --from-dir CORPUS   # author-per-folder
    python scripts/build_baseline.py --gutenberg         # download and build
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from voiceprint.doc import Doc
from voiceprint.features.lexical import function_word_vector
from voiceprint.lexicons import FUNCTION_WORDS

OUT = Path(__file__).resolve().parent.parent / "voiceprint" / "data" / "baseline.json"
CHUNK = 2500

# Public domain, deliberately spread across period, sex and register so the
# variation captured is between people rather than between genres.
GUTENBERG = {
    "austen-emma": 158, "austen-persuasion": 105, "bronte-jane-eyre": 1260,
    "dickens-two-cities": 98, "eliot-middlemarch": 145, "conrad-heart": 219,
    "wilde-dorian": 174, "stoker-dracula": 345, "shelley-frankenstein": 84,
    "twain-huck": 76, "melville-moby": 2701, "hardy-tess": 110,
    "gaskell-north-south": 4276, "trollope-warden": 619, "james-portrait": 2833,
    "stevenson-jekyll": 43, "wells-time-machine": 35, "doyle-hound": 2852,
    "carroll-alice": 11, "kipling-jungle": 236, "forster-room": 2641,
    "chesterton-thursday": 1695, "buchan-steps": 558, "grahame-willows": 289,
}


def chunks(text: str, size: int = CHUNK) -> list[str]:
    words = text.split()
    return [" ".join(words[i:i + size])
            for i in range(0, len(words), size) if len(words[i:i + size]) > size // 2]


def strip_gutenberg(text: str) -> str:
    start = text.find("*** START")
    end = text.find("*** END")
    if start != -1:
        text = text[text.find("\n", start) + 1:]
    if end != -1:
        text = text[:text.rfind("*** END")]
    return text


def fetch_gutenberg() -> dict[str, str]:
    import urllib.request
    out = {}
    for name, ident in GUTENBERG.items():
        for url in (f"https://www.gutenberg.org/files/{ident}/{ident}-0.txt",
                    f"https://www.gutenberg.org/cache/epub/{ident}/pg{ident}.txt"):
            try:
                with urllib.request.urlopen(url, timeout=30) as r:
                    body = r.read().decode("utf8", errors="ignore")
                if len(body) > 20_000:
                    out[name] = strip_gutenberg(body)
                    print(f"  {name:26s} {len(out[name].split()):>7,} words")
                    break
            except Exception:
                continue
        else:
            print(f"  {name:26s} unavailable")
    return out


def read_dir(root: Path) -> dict[str, str]:
    out = {}
    for sub in sorted(p for p in root.iterdir() if p.is_dir()):
        parts = [f.read_text(encoding="utf8", errors="ignore")
                 for f in sorted(sub.rglob("*.txt"))]
        if parts:
            out[sub.name] = "\n\n".join(parts)
            print(f"  {sub.name:26s} {len(out[sub.name].split()):>7,} words")
    return out


def build(corpora: dict[str, str]) -> dict:
    """Per-word mean and sd across author samples, which is what Delta needs."""
    per_author: dict[str, list[dict]] = {}
    for author, text in corpora.items():
        vectors = [function_word_vector(Doc(c)) for c in chunks(text)]
        if vectors:
            per_author[author] = vectors

    if len(per_author) < 5:
        raise SystemExit(f"only {len(per_author)} authors; need at least 5")

    # One vector per author, so a prolific author does not dominate the spread.
    author_means = {
        a: {w: statistics.fmean(v[w] for v in vs) for w in FUNCTION_WORDS}
        for a, vs in per_author.items()
    }

    stats = {}
    for w in FUNCTION_WORDS:
        vals = [author_means[a][w] for a in author_means]
        mean = statistics.fmean(vals)
        sd = statistics.pstdev(vals) if len(vals) > 1 else 0.0
        stats[w] = [round(mean, 4), round(sd, 4)]

    return {
        "schema": 1,
        "kind": "function_word_between_author",
        "unit": "per 1000 words",
        "authors": len(per_author),
        "samples": sum(len(v) for v in per_author.values()),
        "chunk_words": CHUNK,
        "source": "Project Gutenberg, public domain" if not ARGS.from_dir else str(ARGS.from_dir),
        "note": ("Per-word mean and standard deviation taken across authors, "
                 "one vector per author. This is the reference Burrows's Delta "
                 "standardises against; without it Delta cannot know which "
                 "words separate people."),
        "stats": stats,
    }


def main():
    global ARGS
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from-dir", type=Path)
    ap.add_argument("--gutenberg", action="store_true")
    ap.add_argument("-o", "--out", type=Path, default=OUT)
    ARGS = ap.parse_args()

    if ARGS.from_dir:
        corpora = read_dir(ARGS.from_dir)
    elif ARGS.gutenberg:
        corpora = fetch_gutenberg()
    else:
        raise SystemExit("pass --from-dir or --gutenberg")

    data = build(corpora)
    ARGS.out.parent.mkdir(parents=True, exist_ok=True)
    ARGS.out.write_text(json.dumps(data, indent=1), encoding="utf8")

    sds = [sd for _, sd in data["stats"].values()]
    print(f"\n{data['authors']} authors, {data['samples']} samples")
    print(f"per-word sd: median {statistics.median(sds):.3f}, "
          f"max {max(sds):.3f}, zero for {sum(1 for s in sds if s == 0)} words")
    print(f"wrote {ARGS.out} ({ARGS.out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
