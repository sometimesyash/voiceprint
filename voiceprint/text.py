"""Tokenising and segmentation. No dependencies, no tagger."""
from __future__ import annotations

import re

WORD_RE = re.compile(r"[A-Za-z][A-Za-z'\u2019-]*")
TOKEN_RE = re.compile(r"\S+")

_ABBREV = re.compile(
    r"\b(?:mr|mrs|ms|dr|prof|st|jr|sr|vs|etc|e\.g|i\.e|fig|no|approx|inc|ltd"
    r"|co|corp|dept|est|min|max|avg|q[1-4]|u\.s|u\.k)\.$", re.I)

_SENT_SPLIT = re.compile(r"(?<=[.!?])[\"'\u201d\u2019)\]]?\s+")


def tokens(text: str) -> list[str]:
    """Whitespace-delimited tokens, punctuation attached."""
    return TOKEN_RE.findall(str(text))


def words(text: str) -> list[str]:
    """Alphabetic words, lowercased, apostrophes and hyphens kept."""
    return [w.lower() for w in WORD_RE.findall(str(text))]


def sentences(text: str) -> list[str]:
    """Split on terminal punctuation and hard line breaks.

    Line breaks count because slide and note text is often a stack of lines
    with no terminal punctuation, which would otherwise read as one sentence
    and wreck every length statistic downstream.
    """
    out: list[str] = []
    for line in re.split(r"[\n\r]+", str(text)):
        line = line.strip()
        if not line:
            continue
        buf = ""
        for part in _SENT_SPLIT.split(line):
            buf = f"{buf} {part}".strip() if buf else part
            if _ABBREV.search(buf):
                continue
            out.append(buf)
            buf = ""
        if buf:
            out.append(buf)
    return [s for s in out if s.strip()]


def paragraphs(text: str) -> list[str]:
    """Blank-line delimited blocks."""
    return [p.strip() for p in re.split(r"\n\s*\n", str(text)) if p.strip()]


def normalise(text: str) -> str:
    """Collapse whitespace, keep everything else verbatim."""
    return " ".join(str(text).split())


def char_ngrams(text: str, n: int) -> list[str]:
    """Character n-grams over whitespace-normalised text."""
    s = normalise(text)
    return [s[i:i + n] for i in range(len(s) - n + 1)] if len(s) >= n else []


def word_ngrams(seq: list[str], n: int) -> list[tuple[str, ...]]:
    """Word n-grams over an already-tokenised sequence."""
    return [tuple(seq[i:i + n]) for i in range(len(seq) - n + 1)]
