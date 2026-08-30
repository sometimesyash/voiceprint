"""Small numeric helpers. Everything degrades to 0.0 on empty input."""
from __future__ import annotations

import math
import statistics


def rate(n: float, total: float, nd: int = 4) -> float:
    return round(n / total, nd) if total else 0.0


def per100(n: float, n_words: float, nd: int = 3) -> float:
    return round(n * 100.0 / n_words, nd) if n_words else 0.0


def mean(xs) -> float:
    xs = list(xs)
    return round(statistics.fmean(xs), 4) if xs else 0.0


def sd(xs) -> float:
    xs = list(xs)
    return round(statistics.pstdev(xs), 4) if len(xs) > 1 else 0.0


def median(xs) -> float:
    xs = list(xs)
    return round(statistics.median(xs), 4) if xs else 0.0


def cv(xs) -> float:
    """Coefficient of variation. The sentence-length uniformity measure."""
    m = mean(xs)
    return round(sd(xs) / m, 4) if m else 0.0


def zscore(x: float, mu: float, sigma: float) -> float:
    return (x - mu) / sigma if sigma else 0.0


def entropy(counts) -> float:
    """Shannon entropy in bits over a count mapping."""
    vals = [c for c in counts if c > 0]
    total = sum(vals)
    if not total:
        return 0.0
    return round(-sum((c / total) * math.log2(c / total) for c in vals), 4)
