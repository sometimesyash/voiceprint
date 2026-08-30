"""Lexical richness, length-corrected.

Raw type-token ratio falls monotonically with text length, so it cannot be
compared across corpora of different sizes (Tweedie & Baayen 1998). MATTR,
MTLD and Yule's K are length-robust and are what the profile stores.
"""
from __future__ import annotations

from collections import Counter

from .. import stats as S
from ..doc import Doc
from ..lexicons import STOPWORDS
from . import RIGID, feature


def mattr(seq: list[str], window: int = 100) -> float:
    """Moving-average type-token ratio (Covington & McFall 2010)."""
    if len(seq) < window:
        return S.rate(len(set(seq)), len(seq))
    counts = Counter(seq[:window])
    total = len(counts)
    n = 1
    for i in range(window, len(seq)):
        out, inc = seq[i - window], seq[i]
        counts[out] -= 1
        if counts[out] == 0:
            del counts[out]
        counts[inc] += 1
        total += len(counts)
        n += 1
    return round(total / n / window, 4)


def _mtld_pass(seq: list[str], threshold: float) -> float:
    factors, types, count = 0.0, set(), 0
    ttr = 1.0
    for w in seq:
        count += 1
        types.add(w)
        ttr = len(types) / count
        if ttr <= threshold:
            factors += 1
            types, count = set(), 0
            ttr = 1.0
    if count:
        factors += (1 - ttr) / (1 - threshold) if threshold < 1 else 0
    return len(seq) / factors if factors else float(len(seq))


def mtld(seq: list[str], threshold: float = 0.72) -> float:
    """Measure of textual lexical diversity (McCarthy & Jarvis 2010)."""
    if len(seq) < 50:
        return 0.0
    return round((_mtld_pass(seq, threshold)
                  + _mtld_pass(list(reversed(seq)), threshold)) / 2, 2)


def yules_k(seq: list[str]) -> float:
    """Yule's K (1944). Length-robust by construction."""
    n = len(seq)
    if n < 2:
        return 0.0
    freqs = Counter(Counter(seq).values())
    m2 = sum(f * (i ** 2) for i, f in freqs.items())
    return round(10_000 * (m2 - n) / (n * n), 3)


def hapax_rate(seq: list[str]) -> float:
    """Share of the vocabulary occurring exactly once."""
    counts = Counter(seq)
    return S.rate(sum(1 for c in counts.values() if c == 1), len(counts))


@feature("richness.mattr", "richness", "scalar", RIGID, "0-1", group="richness")
def _mattr(d: Doc) -> float:
    return mattr(d.words)


@feature("richness.mtld", "richness", "scalar", RIGID, "factors", group="richness")
def _mtld(d: Doc) -> float:
    return mtld(d.words)


@feature("richness.yules_k", "richness", "scalar", RIGID, "K", group="richness")
def _yk(d: Doc) -> float:
    return yules_k(d.words)


@feature("richness.hapax_rate", "richness", "scalar", RIGID, "0-1", group="richness")
def _hapax(d: Doc) -> float:
    return hapax_rate(d.words)


@feature("richness.content_hapax_rate", "richness", "scalar", RIGID, "0-1", group="richness")
def _content_hapax(d: Doc) -> float:
    return hapax_rate([w for w in d.words if w not in STOPWORDS])
