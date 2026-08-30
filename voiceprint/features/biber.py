"""Biber-style closed-class counts and a derived involved/informational score.

Biber (1988) built six dimensions by factor analysis over ~67 features. Many of
those features need a tagger; the ones here do not. The dimension score is a
standardised composite of the countable subset, so it is directionally
Biber-like rather than a reproduction of his factor loadings.
"""
from __future__ import annotations

from .. import stats as S
from ..doc import Doc
from ..lexicons import (AMPLIFIERS, DEMONSTRATIVES, DISCOURSE_PARTICLES,
                        DOWNTONERS, HEDGES, PREPOSITIONS,
                        SUBORDINATORS_CAUSATIVE, SUBORDINATORS_CONCESSIVE,
                        SUBORDINATORS_CONDITIONAL, WH_WORDS)
from . import FIRM, SUPPLE, feature


def _rate_of(d: Doc, lexicon: set[str]) -> float:
    return S.per100(sum(1 for w in d.words if w in lexicon), d.n_words)


@feature("biber.preposition_per100", "biber", "scalar", FIRM, "per 100w")
def _prep(d: Doc) -> float:
    return _rate_of(d, PREPOSITIONS)


@feature("biber.causative_per100", "biber", "scalar", SUPPLE, "per 100w")
def _causative(d: Doc) -> float:
    return _rate_of(d, SUBORDINATORS_CAUSATIVE)


@feature("biber.concessive_per100", "biber", "scalar", SUPPLE, "per 100w")
def _concessive(d: Doc) -> float:
    return _rate_of(d, SUBORDINATORS_CONCESSIVE)


@feature("biber.conditional_per100", "biber", "scalar", SUPPLE, "per 100w")
def _conditional(d: Doc) -> float:
    return _rate_of(d, SUBORDINATORS_CONDITIONAL)


@feature("biber.amplifier_per100", "biber", "scalar", SUPPLE, "per 100w")
def _amp(d: Doc) -> float:
    return _rate_of(d, AMPLIFIERS)


@feature("biber.downtoner_per100", "biber", "scalar", SUPPLE, "per 100w")
def _down(d: Doc) -> float:
    return _rate_of(d, DOWNTONERS)


@feature("biber.hedge_per100", "biber", "scalar", SUPPLE, "per 100w")
def _hedge(d: Doc) -> float:
    return _rate_of(d, HEDGES)


@feature("biber.discourse_particle_per100", "biber", "scalar", SUPPLE, "per 100w")
def _disc(d: Doc) -> float:
    return _rate_of(d, DISCOURSE_PARTICLES)


@feature("biber.demonstrative_per100", "biber", "scalar", FIRM, "per 100w")
def _dem(d: Doc) -> float:
    return _rate_of(d, DEMONSTRATIVES)


@feature("biber.wh_per100", "biber", "scalar", SUPPLE, "per 100w")
def _wh(d: Doc) -> float:
    return _rate_of(d, WH_WORDS)


@feature("biber.involved_score", "biber", "scalar", SUPPLE, "z-ish")
def _involved(d: Doc) -> float:
    """Involved against informational production, Biber's Dimension 1.

    Positive is involved: contractions, pronouns, short words, discourse
    particles. Negative is informational: nominalisation, prepositions, long
    words, high lexical density. Scaled to roughly -3..+3 on ordinary prose.
    """
    from .register import CONTRACTION_RE
    from .richness import mattr

    if not d.n_words:
        return 0.0
    involved = (
        S.per100(len(CONTRACTION_RE.findall(d.clean)), d.n_words) / 2.0
        + _rate_of(d, DISCOURSE_PARTICLES)
        + _rate_of(d, HEDGES)
        + S.per100(sum(1 for w in d.words if len(w) <= 3), d.n_words) / 10.0
    )
    informational = (
        _rate_of(d, PREPOSITIONS) / 2.0
        + S.per100(sum(1 for w in d.words if len(w) >= 9), d.n_words) / 2.0
        + mattr(d.words) * 4.0
    )
    return round((involved - informational) / 2.0, 3)
