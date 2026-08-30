"""Numeral and quantity conventions."""
from __future__ import annotations

import re

from .. import stats as S
from ..doc import Doc
from . import CONVENTION, FIRM, feature

SPELLED = set(
    "one two three four five six seven eight nine ten eleven twelve thirteen "
    "fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty "
    "fifty sixty seventy eighty ninety hundred thousand million billion".split())


@feature("num.digits_per100", "numerals", "scalar", FIRM, "per 100w")
def _digits(d: Doc) -> float:
    return S.per100(len(re.findall(r"\b\d", d.clean)), d.n_words)


@feature("num.spelled_rate", "numerals", "scalar", CONVENTION, "0-1")
def _spelled(d: Doc) -> float:
    """Words against digits for small numbers."""
    spelled = sum(1 for w in d.words if w in SPELLED)
    digits = len(re.findall(r"\b\d+\b", d.clean))
    return S.rate(spelled, spelled + digits)


@feature("num.percent_style", "numerals", "categorical", CONVENTION)
def _percent(d: Doc) -> str:
    """symbol | word | none"""
    sym = d.clean.count("%")
    word = d.lower.count("percent") + d.lower.count("per cent")
    if not sym and not word:
        return "none"
    return "symbol" if sym >= word else "word"


@feature("num.currency_per100", "numerals", "scalar", FIRM, "per 100w")
def _currency(d: Doc) -> float:
    return S.per100(len(re.findall(r"[$\u00a3\u20ac]\s?\d", d.clean)), d.n_words)


@feature("num.abbreviated_magnitude_rate", "numerals", "scalar", CONVENTION, "0-1")
def _magnitude(d: Doc) -> float:
    """5k against 5,000."""
    abbrev = len(re.findall(r"\d\s?(?:k|m|bn|tn)\b", d.lower))
    full = len(re.findall(r"\d{1,3}(?:,\d{3})+", d.clean))
    return S.rate(abbrev, abbrev + full)
