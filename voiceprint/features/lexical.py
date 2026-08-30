"""Function-word vectors and n-grams.

These are the two feature families with the strongest replicated power to
individuate an author (Mosteller & Wallace 1964; Burrows 2002; Stamatatos
2009; Grieve 2007; Kestemont 2014). They are vectors rather than scalars, so
they are stored separately from the scalar block and consumed by distance.py.

Content words are deliberately not here. They track subject matter and
community, not the person (Eisenstein 2010; Bamman et al. 2014), and belong in
the topic descriptor.
"""
from __future__ import annotations

from collections import Counter

from .. import text as T
from ..doc import Doc
from ..lexicons import FUNCTION_WORDS

FW_INDEX = {w: i for i, w in enumerate(FUNCTION_WORDS)}


def function_word_vector(doc: Doc) -> dict[str, float]:
    """Relative frequency of each function word, per 1000 words.

    The inventory is fixed so vectors from different profiles share a
    coordinate space and Delta is meaningful between them.
    """
    if not doc.n_words:
        return {w: 0.0 for w in FUNCTION_WORDS}
    counts = Counter(w for w in doc.words if w in FW_INDEX)
    n = doc.n_words
    return {w: round(counts.get(w, 0) * 1000.0 / n, 4) for w in FUNCTION_WORDS}


def char_ngram_profile(doc: Doc, n: int = 4, top: int = 300) -> dict[str, float]:
    """Most frequent character n-grams, per 1000 n-grams."""
    grams = T.char_ngrams(doc.lower, n)
    if not grams:
        return {}
    counts = Counter(grams)
    total = len(grams)
    return {g: round(c * 1000.0 / total, 4)
            for g, c in counts.most_common(top)}


def word_ngram_counts(doc: Doc, n: int) -> Counter:
    return Counter(T.word_ngrams(doc.words, n))


def punctuation_shape(doc: Doc) -> dict[str, float]:
    """Punctuation trigrams: the shape of marks around words.

    Captures habits like ", and" or "; the" that neither word nor plain
    character n-grams isolate cleanly.
    """
    import re
    shapes = re.findall(r"[,;:.!?\u2014\u2013()]\s*\w{1,4}", doc.lower)
    if not shapes:
        return {}
    counts = Counter(s.strip() for s in shapes)
    total = sum(counts.values())
    return {s: round(c * 1000.0 / total, 4) for s, c in counts.most_common(80)}


def topic_words(doc: Doc, top: int = 30) -> list[str]:
    """Content words. A topic descriptor, not an identity feature."""
    from ..lexicons import STOPWORDS
    content = [w for w in doc.words if w not in STOPWORDS and len(w) > 3]
    return [w for w, _ in Counter(content).most_common(top)]
