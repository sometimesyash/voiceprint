"""Windowing.

Every scalar is measured over fixed-size windows rather than the pooled
corpus, so each feature arrives with a spread as well as a centre. That spread
is what makes tolerances and confidence intervals possible, and it is the only
honest way to report a figure taken from a short sample.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from . import stats as S
from . import text as T
from .doc import Doc
from .features import extract, registry

DEFAULT_WINDOW = 500
MIN_WINDOW = 120
TARGET_WINDOWS = 8


@dataclass
class Estimate:
    """One feature's centre, spread and support."""
    mean: float
    sd: float
    n: int

    def as_dict(self) -> dict:
        return {"mean": self.mean, "sd": self.sd, "n": self.n}

    @classmethod
    def from_dict(cls, d: dict) -> "Estimate":
        return cls(d["mean"], d["sd"], d["n"])


def window_size(total_words: int) -> int:
    """Pick a window that yields enough of them to estimate a spread.

    A fixed 500 words gives two windows on a short corpus, and two windows
    cannot tell you how much someone varies. Smaller windows are noisier per
    window but the spread across them is the thing being measured.
    """
    if total_words <= 0:
        return DEFAULT_WINDOW
    return max(MIN_WINDOW, min(DEFAULT_WINDOW, total_words // TARGET_WINDOWS))


def _blocks(texts: list[str], size: int) -> list[tuple[str, int]]:
    """Paragraphs, with any that overflow a window broken along sentences."""
    out: list[tuple[str, int]] = []
    for text in texts:
        for para in T.paragraphs(text) or [str(text)]:
            n = len(T.words(para))
            if not n:
                continue
            if n <= size:
                out.append((para, n))
                continue
            buf, count = [], 0
            for sent in T.sentences(para):
                sn = len(T.words(sent))
                if count + sn > size and buf:
                    out.append((" ".join(buf), count))
                    buf, count = [], 0
                buf.append(sent)
                count += sn
            if buf:
                out.append((" ".join(buf), count))
    return out


def windows(texts: list[str], size: int | None = None,
            overlap: float = 0.0) -> list[str]:
    """Split a corpus into windows of roughly `size` words.

    Paragraphs are the unit and their separators are preserved, because line
    breaks and blank lines are themselves measured: a window flattened into
    one run of prose would report every document as a single paragraph and
    make the layout features meaningless. Overlap follows Eder's rolling
    approach and buys extra windows out of a short corpus at the cost of
    correlating them, so it is off unless asked for.
    """
    total = sum(len(T.words(t)) for t in texts)
    if not total:
        return []
    size = size or window_size(total)
    blocks = _blocks(texts, size)
    if not blocks:
        return []
    step = max(1, int(size * (1.0 - min(max(overlap, 0.0), 0.9))))

    out: list[str] = []
    start = 0
    while start < len(blocks):
        buf: list[str] = []
        count = 0
        i = start
        while i < len(blocks) and (count < size or not buf):
            buf.append(blocks[i][0])
            count += blocks[i][1]
            i += 1
        if count >= min(MIN_WINDOW, total) or not out:
            out.append("\n\n".join(buf))
        if i >= len(blocks):
            break
        advance, moved = 0, start
        while moved < len(blocks) and advance < step:
            advance += blocks[moved][1]
            moved += 1
        start = max(moved, start + 1)
    return [w for w in out if w.strip()]

    out: list[str] = []
    start = 0
    while start < len(blocks):
        buf: list[str] = []
        count = 0
        i = start
        while i < len(blocks) and (count < size or not buf):
            buf.append(blocks[i][0])
            count += blocks[i][1]
            i += 1
        if count >= min(MIN_WINDOW, total) or not out:
            out.append("\n\n".join(buf))
        if i >= len(blocks):
            break
        advance, moved = 0, start
        while moved < len(blocks) and advance < step:
            advance += blocks[moved][1]
            moved += 1
        start = max(moved, start + 1)
    return [w for w in out if w.strip()]


def aggregate(chunks: list[str]) -> tuple[dict[str, Estimate], dict[str, str]]:
    """Measure every scalar per window, then summarise. Categoricals take a vote."""
    docs = [Doc(c) for c in chunks]
    scalars: dict[str, list[float]] = {}
    cats: dict[str, Counter] = {}

    for d in docs:
        vals = extract(d, kinds=("scalar", "categorical"))
        for name, v in vals.items():
            if v is None:
                continue
            if isinstance(v, str):
                cats.setdefault(name, Counter())[v] += 1
            else:
                scalars.setdefault(name, []).append(float(v))

    est = {k: Estimate(S.mean(v), S.sd(v), len(v)) for k, v in scalars.items()}
    dom = {k: c.most_common(1)[0][0] for k, c in cats.items()}
    return est, dom


def categorical_consistency(chunks: list[str]) -> dict[str, float]:
    """How reliably a categorical holds across windows."""
    docs = [Doc(c) for c in chunks]
    cats: dict[str, Counter] = {}
    for d in docs:
        for name, v in extract(d, kinds=("categorical",)).items():
            if isinstance(v, str):
                cats.setdefault(name, Counter())[v] += 1
    return {k: S.rate(c.most_common(1)[0][1], sum(c.values()))
            for k, c in cats.items()}


def elasticity_map() -> dict[str, float]:
    return {name: f.elasticity for name, f in registry().items()}
