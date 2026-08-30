"""Recurrent phrases: the things a person says more often than anyone else.

Forensic linguistics locates idiolect less in rare words than in habitual
multi-word co-selection, the phrases someone reaches for repeatedly without
noticing (Coulthard 2004; Johnson & Wright 2014; Wright 2017 on the Enron
corpus). A phrase earns a place here by being frequent in the person's writing
and unremarkable elsewhere, which is why a background baseline is required
before anything is reported as characteristic.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

from . import text as T
from .doc import Doc
from .lexicons import FUNCTION_WORDS

FW = set(FUNCTION_WORDS)


@dataclass
class Phrase:
    text: str
    n: int
    count: int
    per_10k: float
    docs: int
    lift: float | None = None

    def as_dict(self) -> dict:
        d = {"text": self.text, "n": self.n, "count": self.count,
             "per_10k": self.per_10k, "docs": self.docs}
        if self.lift is not None:
            d["lift"] = self.lift
        return d


@dataclass
class Signature:
    """The phrases, openers, closers and collocations someone repeats."""
    bundles: list[Phrase] = field(default_factory=list)
    openers: list[Phrase] = field(default_factory=list)
    closers: list[Phrase] = field(default_factory=list)
    fillers: list[Phrase] = field(default_factory=list)
    favoured_words: list[Phrase] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {k: [p.as_dict() for p in v] for k, v in self.__dict__.items()}


def _all_function(gram: tuple[str, ...]) -> bool:
    return all(w in FW for w in gram)


def _phrases(docs: list[Doc], n: int, min_count: int, total_words: int,
             require_content: bool) -> list[Phrase]:
    counts: Counter = Counter()
    doc_freq: Counter = Counter()
    for d in docs:
        grams = T.word_ngrams(d.words, n)
        counts.update(grams)
        doc_freq.update(set(grams))

    out = []
    for gram, c in counts.items():
        if c < min_count:
            continue
        if require_content and _all_function(gram):
            continue
        out.append(Phrase(text=" ".join(gram), n=n, count=c,
                          per_10k=round(c * 10_000 / total_words, 3)
                          if total_words else 0.0,
                          docs=doc_freq[gram]))
    out.sort(key=lambda p: (-p.count, p.text))
    return out


def _sentence_edges(docs: list[Doc], words_taken: int, head: bool) -> Counter:
    counts: Counter = Counter()
    for d in docs:
        for s in d.sentences:
            w = T.words(s)
            if len(w) < words_taken + 1:
                continue
            part = w[:words_taken] if head else w[-words_taken:]
            counts[" ".join(part)] += 1
    return counts


def build(texts: list[str], baseline: dict[str, float] | None = None,
          min_count: int = 3, top: int = 40) -> Signature:
    """Find what someone repeats, scored against a baseline where available.

    Without a baseline the counts still hold, but they will surface ordinary
    English alongside anything genuinely characteristic, so callers should say
    so rather than presenting raw frequency as a fingerprint.
    """
    docs = [Doc(t) for t in texts if str(t).strip()]
    total = sum(d.n_words for d in docs)
    if not total:
        return Signature()

    bundles: list[Phrase] = []
    for n in (2, 3, 4, 5):
        bundles.extend(_phrases(docs, n, min_count, total, require_content=True))

    fillers = _phrases(docs, 3, min_count, total, require_content=False)
    fillers = [p for p in fillers if _all_function(tuple(p.text.split()))]

    word_counts = Counter(w for d in docs for w in d.words)
    favoured = [
        Phrase(text=w, n=1, count=c, per_10k=round(c * 10_000 / total, 3),
               docs=sum(1 for d in docs if w in d.words))
        for w, c in word_counts.items() if c >= min_count
    ]

    if baseline:
        for group in (bundles, fillers, favoured):
            for p in group:
                b = baseline.get(p.text, 0.0)
                p.lift = round(math.log2((p.per_10k + 0.1) / (b + 0.1)), 3)
        bundles.sort(key=lambda p: (-(p.lift or 0), -p.count))
        fillers.sort(key=lambda p: (-(p.lift or 0), -p.count))
        favoured.sort(key=lambda p: (-(p.lift or 0), -p.count))

    def _edges(head: bool) -> list[Phrase]:
        c = _sentence_edges(docs, 2, head)
        return [Phrase(text=t, n=2, count=n_, per_10k=round(n_ * 10_000 / total, 3),
                       docs=0)
                for t, n_ in c.most_common(top) if n_ >= min_count]

    return Signature(
        bundles=bundles[:top],
        openers=_edges(head=True)[:20],
        closers=_edges(head=False)[:20],
        fillers=fillers[:20],
        favoured_words=[p for p in favoured
                        if p.text not in FW][:top] if baseline else favoured[:top],
    )
