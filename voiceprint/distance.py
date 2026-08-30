"""Voice distance.

Burrows's Delta (2002) is the measure: standardise each function word's
frequency against the reference, then take the mean absolute difference. It
has been replicated for two decades and needs nothing but arithmetic, which
makes it the right objective for a rewrite loop to minimise.

The scalar distance alongside it works the same way, except the spread comes
from the windowed estimates rather than from a corpus of authors, so a feature
the person is inconsistent about is forgiving and one they are rigid about is
not.
"""
from __future__ import annotations

from dataclasses import dataclass

from .doc import Doc
from .features import registry
from .features.lexical import char_ngram_profile, function_word_vector
from .profile import Profile
from .windows import Estimate

# A feature that happened to come out identical across a handful of windows has
# not been shown to be invariant, only unmeasured. Without a floor its standard
# deviation is zero and one accident dominates the whole distance.
MIN_WINDOWS = 3
RELATIVE_FLOOR = 0.15
ABSOLUTE_FLOOR = 0.01
Z_CAP = 6.0


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

    def verdict(self, tolerance: float = 1.5) -> str:
        if self.overall <= tolerance * 0.6:
            return "close"
        if self.overall <= tolerance:
            return "acceptable"
        if self.overall <= tolerance * 1.8:
            return "drifting"
        return "off"

    def as_dict(self) -> dict:
        return {"delta": self.delta, "scalar": self.scalar,
                "ngram": self.ngram, "overall": self.overall,
                "verdict": self.verdict(),
                "worst": [d.as_dict() for d in self.worst]}


def _dispersion(vec: dict[str, float]) -> dict[str, float]:
    """Per-word spread, approximated from the reference itself.

    Delta normally takes standard deviations from a corpus of many authors.
    With one author's profile the frequency itself is the best available
    proxy for how variable a word is, since common words vary more in
    absolute terms than rare ones.
    """
    return {w: max((f ** 0.5) * 0.6 + 0.15, 0.15) for w, f in vec.items()}


def burrows_delta(observed: dict[str, float],
                  reference: dict[str, float]) -> float:
    """Mean absolute z-difference over the shared function-word space."""
    keys = [k for k in reference if k in observed]
    if not keys:
        return 0.0
    disp = _dispersion(reference)
    total = sum(abs(observed[k] - reference[k]) / disp[k] for k in keys)
    return round(total / len(keys), 4)


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
        if est is None or value is None or est.n < MIN_WINDOWS:
            continue
        sd = dispersion(est)
        z = max(-Z_CAP, min(Z_CAP, (float(value) - est.mean) / sd))
        out.append(Deviation(name, reg[name].family if name in reg else "?",
                             round(float(value), 4), est.mean, round(sd, 4), z))
    return out


def measure(text: str, profile: Profile, worst: int = 8) -> Distance:
    """How far a draft sits from a profile."""
    doc = Doc(text)
    devs = scalar_deviations(doc, profile)
    scalar = round(sum(abs(d.z) for d in devs) / len(devs), 4) if devs else 0.0
    delta = burrows_delta(function_word_vector(doc), profile.function_words)
    ngram = ngram_distance(char_ngram_profile(doc), profile.char_ngrams)

    overall = round(0.45 * delta + 0.35 * scalar + 0.20 * ngram, 4)
    devs.sort(key=lambda d: -abs(d.z))
    return Distance(delta, scalar, ngram, overall, devs[:worst], len(devs))
