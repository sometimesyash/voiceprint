"""The texture arm: character n-grams.

Delta needs enough text for each word's rate to settle, and under a couple of
thousand words it does not. Character n-grams settle far sooner, because a
short passage contains thousands of them where it contains only a handful of
any given function word. Stamatatos (2009) reports them as the most robust
family on short and noisy text, and measurement here agrees: on 150 word
passages against 24 authors they identify the right person 47% of the time
where Delta manages 10%.

Orders 3 to 5 are kept together. Three-grams carry morphology and short
function words, five-grams carry whole short words and their neighbours, and
the mixture is steadier across sample sizes than any single order.

Delta is still the better measure once there is enough text, so the two are
blended by how much text there actually is rather than by preference. See
docs/small-samples.md.
"""
from __future__ import annotations

from collections import Counter

from .doc import Doc
from .text import char_ngrams

ORDERS = (3, 4, 5)
TOP_PER_ORDER = 500

# Delta's share of the identity verdict, as a function of how much text there
# is. Swept against the calibration rather than chosen: texture alone scores
# 62.4% across the grid and no weighting beats that on average, so Delta is
# held to a minority share and only reaches it when there is enough text for
# it to be the measure the literature validates. It earns its place at the
# top of the range, where it takes 92% against texture's 90%.
FLOOR_WORDS = 1000
CEILING_WORDS = 8000
MAX_DELTA_WEIGHT = 0.4


def profile(doc: Doc, top: int = TOP_PER_ORDER) -> dict[str, dict[str, float]]:
    """Per-order n-gram frequencies, per thousand n-grams of that order."""
    out: dict[str, dict[str, float]] = {}
    for n in ORDERS:
        grams = char_ngrams(doc.lower, n)
        if not grams:
            out[str(n)] = {}
            continue
        counts = Counter(grams)
        total = len(grams)
        out[str(n)] = {g: round(c * 1000.0 / total, 4)
                       for g, c in counts.most_common(top)}
    return out


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    keys = set(a) | set(b)
    xs = [a.get(k, 0.0) for k in keys]
    ys = [b.get(k, 0.0) for k in keys]
    dot = sum(x * y for x, y in zip(xs, ys))
    na = sum(x * x for x in xs) ** 0.5
    nb = sum(y * y for y in ys) ** 0.5
    return 1 - dot / (na * nb) if na and nb else 0.0


def distance(observed: dict[str, dict[str, float]],
             reference: dict[str, dict[str, float]]) -> float:
    """Mean cosine complement across the orders both sides carry.

    Scaled by six so the figure sits on roughly the same range as Delta and
    the two can be averaged without one silently dominating.
    """
    scores = [_cosine(observed.get(str(n), {}), reference.get(str(n), {}))
              for n in ORDERS
              if observed.get(str(n)) and reference.get(str(n))]
    return round(sum(scores) / len(scores) * 6, 4) if scores else 0.0


def delta_weight(support_words: int) -> float:
    """How much of the verdict Delta should carry, given the text available.

    `support_words` is the smaller of the draft and the profile, since the
    noisier of the two governs. The curve is set from the measured crossover
    in docs/small-samples.md rather than chosen.
    """
    if support_words <= FLOOR_WORDS:
        return 0.0
    span = CEILING_WORDS - FLOOR_WORDS
    return round(min(MAX_DELTA_WEIGHT,
                     (support_words - FLOOR_WORDS) / span * MAX_DELTA_WEIGHT), 3)


def blend(delta: float, texture: float, support_words: int) -> tuple[float, float]:
    """Combine the two arms. Returns the blended figure and Delta's weight."""
    w = delta_weight(support_words)
    return round(w * delta + (1 - w) * texture, 4), w
