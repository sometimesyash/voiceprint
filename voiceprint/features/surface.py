"""Surface form: capitalisation, terminal punctuation, length distributions."""
from __future__ import annotations

from collections import Counter

from .. import stats as S
from .. import text as T
from ..doc import Doc
from ..lexicons import TITLE_MINOR
from . import CONVENTION, FIRM, RIGID, feature


def caps_style(s: str) -> str:
    """upper | title | sentence | lower | none"""
    s = s.strip()
    if not s or not any(c.isalpha() for c in s):
        return "none"
    if not any(c.islower() for c in s):
        return "upper"
    aw = T.WORD_RE.findall(s)
    if not aw:
        return "none"
    if next(c for c in s if c.isalpha()).islower():
        return "lower"
    significant = [w for w in aw[1:] if w.lower() not in TITLE_MINOR]
    if significant:
        capped = sum(1 for w in significant if w[0].isupper())
        if capped / len(significant) >= 0.7:
            return "title"
    return "sentence"


def terminal_punct(s: str) -> str:
    """full_stop | question | exclamation | colon | ellipsis | none"""
    s = s.strip()
    if not s:
        return "none"
    if s.endswith("...") or s.endswith("\u2026"):
        return "ellipsis"
    return {".": "full_stop", "?": "question", "!": "exclamation",
            ":": "colon"}.get(s[-1], "none")


@feature("caps.dominant", "surface", "categorical", CONVENTION, group="caps")
def _caps(d: Doc) -> str:
    """Prevailing capitalisation across sentences."""
    c = Counter(caps_style(s) for s in d.sentences)
    return c.most_common(1)[0][0] if c else "none"


@feature("caps.consistency", "surface", "scalar", CONVENTION, "0-1", group="caps")
def _caps_consistency(d: Doc) -> float:
    c = Counter(caps_style(s) for s in d.sentences)
    return S.rate(c.most_common(1)[0][1], len(d.sentences)) if c else 0.0


@feature("terminal.dominant", "surface", "categorical", CONVENTION, group="terminal")
def _term(d: Doc) -> str:
    """Prevailing final character class."""
    c = Counter(terminal_punct(s) for s in d.sentences)
    return c.most_common(1)[0][0] if c else "none"


@feature("terminal.full_stop_rate", "surface", "scalar", CONVENTION, "0-1", group="terminal")
def _term_stop(d: Doc) -> float:
    c = Counter(terminal_punct(s) for s in d.sentences)
    return S.rate(c.get("full_stop", 0), len(d.sentences))


@feature("terminal.none_rate", "surface", "scalar", CONVENTION, "0-1", group="terminal")
def _term_none(d: Doc) -> float:
    c = Counter(terminal_punct(s) for s in d.sentences)
    return S.rate(c.get("none", 0), len(d.sentences))


@feature("rhythm.words_per_sentence", "rhythm", "scalar", FIRM, "words", group="sentence_length")
def _wps(d: Doc) -> float:
    """Mean sentence length."""
    return S.mean(d.sentence_lengths)


@feature("rhythm.sentence_sd", "rhythm", "scalar", RIGID, "words", group="sentence_length")
def _wps_sd(d: Doc) -> float:
    return S.sd(d.sentence_lengths)


@feature("rhythm.length_cv", "rhythm", "scalar", RIGID, "ratio", group="sentence_length")
def _wps_cv(d: Doc) -> float:
    """Sentence-length coefficient of variation. Uniformity is the tell."""
    return S.cv(d.sentence_lengths)


@feature("rhythm.sentences_per_paragraph", "rhythm", "scalar", FIRM, "count")
def _spp(d: Doc) -> float:
    paras = T.paragraphs(d.raw)
    return S.mean([len(T.sentences(p)) for p in paras]) if paras else 0.0


@feature("word.mean_length", "surface", "scalar", RIGID, "chars", group="word_length")
def _wlen(d: Doc) -> float:
    return S.mean([len(w) for w in d.words])


@feature("word.length_sd", "surface", "scalar", RIGID, "chars", group="word_length")
def _wlen_sd(d: Doc) -> float:
    """Mendenhall's characteristic curve, compressed to its spread."""
    return S.sd([len(w) for w in d.words])


@feature("word.long_rate", "surface", "scalar", RIGID, "0-1", group="word_length")
def _wlong(d: Doc) -> float:
    return S.rate(sum(1 for w in d.words if len(w) >= 9), len(d.words))


@feature("word.short_rate", "surface", "scalar", RIGID, "0-1", group="word_length")
def _wshort(d: Doc) -> float:
    return S.rate(sum(1 for w in d.words if len(w) <= 3), len(d.words))
