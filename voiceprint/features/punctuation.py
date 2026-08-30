"""Punctuation rates per mark. Grieve (2007) ranks these among the strongest
simple authorship features."""
from __future__ import annotations

import re

from .. import stats as S
from ..doc import Doc
from . import RIGID, feature

MARKS = {
    "comma": lambda s: s.count(","),
    "semicolon": lambda s: s.count(";"),
    "colon": lambda s: s.count(":"),
    "em_dash": lambda s: s.count("\u2014"),
    "en_dash": lambda s: s.count("\u2013"),
    "hyphen": lambda s: len(re.findall(r"\w-\w", s)),
    "question": lambda s: s.count("?"),
    "exclamation": lambda s: s.count("!"),
    "parenthesis": lambda s: s.count("("),
    "bracket": lambda s: s.count("["),
    "quote_double": lambda s: s.count('"') + s.count("\u201c"),
    "quote_single": lambda s: len(re.findall(r"(?<!\w)['\u2018]", s)),
    "ellipsis": lambda s: s.count("...") + s.count("\u2026"),
    "ampersand": lambda s: s.count("&"),
    "slash": lambda s: len(re.findall(r"\w/\w", s)),
}

# Word-internal apostrophes are contractions and possessives, already counted
# in register.contractions_per100. Measuring them here too made one habit move
# three features and dominate the distance, so the mark is deliberately absent
# from this table.
GROUPS = {"quote_double": "quotes", "quote_single": "quotes",
          "em_dash": "dashes", "en_dash": "dashes"}


def _make(mark: str, fn):
    @feature(f"punct.{mark}_per100", "punctuation", "scalar", RIGID,
             "per 100w", group=GROUPS.get(mark, f"punct.{mark}"))
    def _f(d: Doc, _fn=fn) -> float:
        return S.per100(_fn(d.clean), d.n_words)
    return _f


for _m, _fn in MARKS.items():
    _make(_m, _fn)


@feature("punct.density_per100", "punctuation", "scalar", RIGID, "per 100w")
def _density(d: Doc) -> float:
    """All marks together. Separates sparse writers from heavy ones."""
    return S.per100(sum(fn(d.clean) for fn in MARKS.values()), d.n_words)


@feature("punct.dash_style", "punctuation", "categorical", RIGID)
def _dash(d: Doc) -> str:
    """em | en | double_hyphen | none"""
    counts = {
        "em": d.clean.count("\u2014"),
        "en": len(re.findall(r"\s\u2013\s", d.clean)),
        "double_hyphen": d.clean.count("--"),
    }
    top = max(counts, key=counts.get)
    return top if counts[top] else "none"


@feature("punct.oxford_comma_rate", "punctuation", "scalar", RIGID, "0-1")
def _oxford(d: Doc) -> float:
    with_c = len(re.findall(r",\s+(?:and|or)\s+\w", d.lower))
    without = len(re.findall(r"\w\s+(?:and|or)\s+\w+[.,;]", d.lower))
    return S.rate(with_c, with_c + without)
