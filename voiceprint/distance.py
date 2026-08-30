"""Voice distance.

Burrows's Delta (2002) standardises each function word's frequency against how
much that word varies BETWEEN authors, then takes the mean absolute z
difference. The between-author part is what gives the measure its power: it is
how the metric learns which words separate people and which do not.

That reference ships in data/baseline.json, built from 24 public domain authors
by scripts/build_baseline.py. Without it the measure cannot be Delta, and the
code says so rather than pretending: every Distance carries whether it was
calibrated.

The scalar distance works on the same principle, except the spread comes from
the person's own windows, so a feature they are inconsistent about is forgiving
and one they are rigid about is not.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .doc import Doc
from .features import group_of, registry
from .features.lexical import char_ngram_profile, function_word_vector
from .profile import Profile
from .texture import blend as blend_arms
from .texture import delta_weight
from .texture import distance as texture_distance
from .texture import profile as texture_profile
from .windows import Estimate

BASELINE = Path(__file__).resolve().parent / "data" / "baseline.json"

# A feature identical across a few windows has not been shown to be invariant,
# only unmeasured. Without a floor its spread is zero and one accident
# dominates the distance.
MIN_WINDOWS = 3
RELATIVE_FLOOR = 0.15
ABSOLUTE_FLOOR = 0.01
Z_CAP = 6.0

# Below this a word varies too little across the reference for its z to carry
# meaning, so it is dropped rather than allowed to spike.
MIN_BASELINE_SD = 0.02


@lru_cache(maxsize=1)
def baseline() -> dict | None:
    """Between-author reference, or None if it was not shipped."""
    try:
        data = json.loads(BASELINE.read_text(encoding="utf8"))
    except Exception:
        return None
    return data if data.get("stats") else None


def delta_is_calibrated() -> bool:
    return baseline() is not None


@dataclass
class Deviation:
    feature: str
    family: str
    observed: float
    expected: float
    sd: float
    z: float

    @property
    def direction(self) -> str:
        return "high" if self.z > 0 else "low"

    def as_dict(self) -> dict:
        return {"feature": self.feature, "family": self.family,
                "observed": self.observed, "expected": self.expected,
                "sd": self.sd, "z": round(self.z, 2)}


@dataclass
class Distance:
    delta: float
    scalar: float
    ngram: float
    overall: float
    worst: list[Deviation]
    n_features: int
    calibrated: bool = True
    texture: float = 0.0
    delta_weight: float = 1.0
    support_words: int = 0

    @property
    def identity(self) -> float:
        """The two identity arms blended by how much text supports them."""
        return round(self.delta_weight * self.delta
                     + (1 - self.delta_weight) * self.texture, 4)

    @property
    def arm(self) -> str:
        if self.delta_weight <= 0.05:
            return "texture"
        if self.delta_weight >= 0.3:
            return "both"
        return "texture-led"

    def verdict(self, tolerance: float = 1.5) -> str:
        if self.overall <= tolerance * 0.6:
            return "close"
        if self.overall <= tolerance:
            return "acceptable"
        if self.overall <= tolerance * 1.8:
            return "drifting"
        return "off"

    def as_dict(self) -> dict:
        return {"delta": self.delta, "texture": self.texture,
                "identity": self.identity, "delta_weight": self.delta_weight,
                "arm": self.arm, "scalar": self.scalar, "ngram": self.ngram,
                "overall": self.overall, "verdict": self.verdict(),
                "calibrated": self.calibrated,
                "support_words": self.support_words,
                "worst": [d.as_dict() for d in self.worst]}


def burrows_delta(observed: dict[str, float],
                  reference: dict[str, float]) -> tuple[float, bool]:
    """Mean absolute z difference over the shared function-word space.

    Returns the distance and whether a between-author reference was used. When
    one was not, the fallback scales each word by its own sampling noise, which
    is a frequency-weighted L1 distance and not Delta.
    """
    base = baseline()
    if base:
        stats = base["stats"]
        keys = [k for k in reference
                if k in observed and stats.get(k, (0, 0))[1] >= MIN_BASELINE_SD]
        if keys:
            total = sum(abs(observed[k] - reference[k]) / stats[k][1]
                        for k in keys)
            return round(total / len(keys), 4), True

    keys = [k for k in reference if k in observed]
    if not keys:
        return 0.0, False
    total = sum(abs(observed[k] - reference[k])
                / max((reference[k] ** 0.5) * 0.6, 0.15) for k in keys)
    return round(total / len(keys), 4), False


def ngram_distance(observed: dict[str, float],
                   reference: dict[str, float]) -> float:
    """Cosine complement over character n-grams, scaled to sit near Delta."""
    if not observed or not reference:
        return 0.0
    keys = set(observed) | set(reference)
    a = [observed.get(k, 0.0) for k in keys]
    b = [reference.get(k, 0.0) for k in keys]
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if not na or not nb:
        return 0.0
    return round((1 - dot / (na * nb)) * 4, 4)


def dispersion(est: Estimate) -> float:
    """Usable spread for one feature, floored so zero variance cannot divide."""
    return max(est.sd, abs(est.mean) * RELATIVE_FLOOR, ABSOLUTE_FLOOR)


def scalar_deviations(doc: Doc, profile: Profile) -> list[Deviation]:
    from .features import extract
    reg = registry()
    observed = extract(doc, kinds=("scalar",))
    out: list[Deviation] = []
    for name, value in observed.items():
        est: Estimate | None = profile.scalars.get(name)
        if est is None or value is None or est.effective_n < MIN_WINDOWS:
            continue
        sd = dispersion(est)
        z = max(-Z_CAP, min(Z_CAP, (float(value) - est.mean) / sd))
        out.append(Deviation(name, reg[name].family if name in reg else "?",
                             round(float(value), 4), est.mean, round(sd, 4), z))
    return out


def aggregate_scalar(devs: list[Deviation]) -> float:
    """Average |z| once per correlated group, ignoring mutual absences.

    A flat mean counts one habit several times, since contractions,
    apostrophes and synthetic negation all move together. It is also dragged
    toward zero by marks neither text uses. So each group contributes only its
    strongest deviation, and a feature absent from both draft and profile
    contributes nothing.
    """
    groups: dict[str, float] = {}
    for d in devs:
        if d.observed == 0.0 and d.expected == 0.0:
            continue
        g = group_of(d.feature)
        groups[g] = max(groups.get(g, 0.0), abs(d.z))
    if not groups:
        return 0.0
    return round(sum(groups.values()) / len(groups), 4)


def measure(text: str, profile: Profile, worst: int = 8) -> Distance:
    """How far a draft sits from a profile.

    Identity is judged by two arms. Delta reads the function-word
    distribution and is the stronger measure once there is enough text.
    Texture reads character n-grams and holds up on short samples where Delta
    is still noise. The weighting between them follows the smaller of the two
    texts, since the noisier side governs.
    """
    doc = Doc(text)
    devs = scalar_deviations(doc, profile)
    scalar = aggregate_scalar(devs)
    delta, calibrated = burrows_delta(function_word_vector(doc),
                                      profile.function_words)
    ngram = ngram_distance(char_ngram_profile(doc), profile.char_ngrams)

    support = min(doc.n_words, profile.words) if profile.words else doc.n_words
    texture = texture_distance(texture_profile(doc), profile.texture)
    identity, weight = blend_arms(delta, texture, support)

    overall = round(0.45 * identity + 0.35 * scalar + 0.20 * ngram, 4)
    devs.sort(key=lambda d: -abs(d.z))
    return Distance(delta, scalar, ngram, overall, devs[:worst], len(devs),
                    calibrated, texture, weight, support)
