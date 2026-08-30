"""Sentence shape: fragments, clause structure, stacked constructions."""
from __future__ import annotations

from .. import stats as S
from .. import text as T
from ..doc import Doc
from ..lexicons import CLAUSE_MARKERS
from . import FIRM, RIGID, feature


def has_clause_marker(sentence: str) -> bool:
    toks = {w.strip(".,;:!?\"'()[]").lower() for w in sentence.split()}
    if toks & CLAUSE_MARKERS:
        return True
    if len(toks) >= 5:
        return any(len(w) > 4 and w.endswith(("ed", "ing")) for w in toks)
    return False


def is_fragment(sentence: str) -> bool:
    return not has_clause_marker(sentence)


def is_stacked(block: str) -> bool:
    """Two or more short, mostly verbless pieces stacked with full stops."""
    sents = T.sentences(block)
    if len(sents) < 2:
        return False
    lens = [len(T.words(s)) for s in sents]
    if sum(lens) > 16 or max(lens) > 7:
        return False
    return sum(1 for s in sents if is_fragment(s)) >= len(sents) / 2


@feature("shape.fragment_rate", "structure", "scalar", FIRM, "0-1")
def _frag(d: Doc) -> float:
    """Share of sentences with no finite clause."""
    return S.rate(sum(1 for s in d.sentences if is_fragment(s)),
                  len(d.sentences))


@feature("shape.fragment_rate_prose", "structure", "scalar", FIRM, "0-1")
def _frag_prose(d: Doc) -> float:
    """Fragment rate over prose only.

    Short labels land in the same bucket as paragraphs and would otherwise
    report prose as almost entirely verbless.
    """
    prose = [s for s in d.sentences if len(T.words(s)) >= 8]
    return S.rate(sum(1 for s in prose if is_fragment(s)), len(prose))


@feature("shape.stacked_rate", "structure", "scalar", RIGID, "0-1")
def _stacked(d: Doc) -> float:
    """Stacked-fragment declaratives per paragraph."""
    paras = T.paragraphs(d.raw)
    return S.rate(sum(1 for p in paras if is_stacked(p)), len(paras))


@feature("shape.single_sentence_para_rate", "structure", "scalar", FIRM, "0-1")
def _single(d: Doc) -> float:
    paras = T.paragraphs(d.raw)
    return S.rate(sum(1 for p in paras if len(T.sentences(p)) == 1), len(paras))


@feature("shape.comma_clauses", "structure", "scalar", RIGID, "per sentence")
def _commas(d: Doc) -> float:
    """Commas per sentence. A proxy for clause elaboration without a parser."""
    return round(d.clean.count(",") / len(d.sentences), 4) if d.sentences else 0.0


@feature("shape.list_rate", "structure", "scalar", FIRM, "0-1")
def _lists(d: Doc) -> float:
    lines = [l.strip() for l in d.raw.splitlines() if l.strip()]
    bullets = sum(1 for l in lines
                  if l[:2] in ("- ", "* ", "+ ") or l[:3].rstrip(".)").isdigit())
    return S.rate(bullets, len(lines))
