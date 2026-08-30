"""Register: person, contractions, abstraction, formality."""
from __future__ import annotations

import re

from .. import stats as S
from ..doc import Doc
from ..lexicons import (NOMINAL_SUFFIXES, PRONOUNS_FIRST_PL, PRONOUNS_FIRST_SG,
                        PRONOUNS_SECOND, PRONOUNS_THIRD)
from . import FIRM, RIGID, SUPPLE, feature

CONTRACTION_RE = re.compile(r"\b\w+['\u2019](s|t|re|ve|ll|d|m)\b", re.I)


@feature("person.dominant", "register", "categorical", SUPPLE, group="person")
def _person(d: Doc) -> str:
    """first_singular | first_plural | second | third | impersonal"""
    counts = {
        "first_singular": sum(1 for w in d.words if w in PRONOUNS_FIRST_SG),
        "first_plural": sum(1 for w in d.words if w in PRONOUNS_FIRST_PL),
        "second": sum(1 for w in d.words if w in PRONOUNS_SECOND),
        "third": sum(1 for w in d.words if w in PRONOUNS_THIRD),
    }
    top = max(counts, key=counts.get)
    return top if counts[top] else "impersonal"


@feature("person.first_sg_per100", "register", "scalar", SUPPLE, "per 100w", group="person")
def _fsg(d: Doc) -> float:
    return S.per100(sum(1 for w in d.words if w in PRONOUNS_FIRST_SG), d.n_words)


@feature("person.first_pl_per100", "register", "scalar", SUPPLE, "per 100w", group="person")
def _fpl(d: Doc) -> float:
    return S.per100(sum(1 for w in d.words if w in PRONOUNS_FIRST_PL), d.n_words)


@feature("person.second_per100", "register", "scalar", SUPPLE, "per 100w", group="person")
def _snd(d: Doc) -> float:
    return S.per100(sum(1 for w in d.words if w in PRONOUNS_SECOND), d.n_words)


@feature("person.third_per100", "register", "scalar", SUPPLE, "per 100w", group="person")
def _thd(d: Doc) -> float:
    return S.per100(sum(1 for w in d.words if w in PRONOUNS_THIRD), d.n_words)


@feature("register.contractions_per100", "register", "scalar", SUPPLE,
         "per 100w", group="contraction")
def _contractions(d: Doc) -> float:
    return S.per100(len(CONTRACTION_RE.findall(d.clean)), d.n_words)


@feature("register.nominalisation_per100", "register", "scalar", FIRM, "per 100w")
def _nominal(d: Doc) -> float:
    """Suffix-counted. Catches false positives like 'moment' and 'question'."""
    n = sum(1 for w in d.words if len(w) > 6 and w.endswith(NOMINAL_SUFFIXES))
    return S.per100(n, d.n_words)


@feature("register.negation_synthetic_rate", "register", "scalar", RIGID,
         "0-1", group="contraction")
def _negation(d: Doc) -> float:
    """n't against 'not'. Biber's synthetic-versus-analytic negation."""
    synth = len(re.findall(r"n['\u2019]t\b", d.lower))
    analytic = sum(1 for w in d.words if w == "not")
    return S.rate(synth, synth + analytic)


@feature("register.passive_hint_per100", "register", "scalar", FIRM, "per 100w")
def _passive(d: Doc) -> float:
    """be + past participle, approximated by suffix. Noisy without a tagger."""
    n = len(re.findall(
        r"\b(?:is|are|was|were|be|been|being)\s+\w+(?:ed|en)\b", d.lower))
    return S.per100(n, d.n_words)


@feature("register.that_deletion_hint", "register", "scalar", SUPPLE, "per 100w")
def _that(d: Doc) -> float:
    n = len(re.findall(
        r"\b(?:said|think|know|believe|hope|guess|suppose|feel)\s+(?!that\b)"
        r"(?:i|you|we|they|he|she|it|the|this)\b", d.lower))
    return S.per100(n, d.n_words)
