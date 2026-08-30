"""The fidelity dial.

A person does not write an email the way they write a report, but they remain
recognisably themselves in both. So context is allowed to move some things and
not others, and how far it may move anything at all is one number.

    target = user + (1 - fidelity) * elasticity * (context - user)

Fidelity defaults to 0.80. Elasticity is declared per feature: rhythm,
punctuation habit and function words are identity and sit at zero, so context
never touches them however low the dial goes. Length, hedging and formality
give way. Categoricals cannot be averaged, so they are handed to whichever
side has authority, which for convention is the context.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .features import registry
from .profile import Profile
from .windows import Estimate

DEFAULT_FIDELITY = 0.80

# Convention belongs to the situation, not the person. A house style that
# capitalises headings does so regardless of who is writing.
CONTEXT_GOVERNED = {
    "caps.dominant", "terminal.dominant", "num.percent_style",
    "num.spelled_rate", "num.abbreviated_magnitude_rate",
    "punct.oxford_comma_rate",
}


@dataclass
class Target:
    feature: str
    family: str
    value: float
    tolerance: float
    source: str
    unit: str = ""

    @property
    def low(self) -> float:
        return round(self.value - self.tolerance, 4)

    @property
    def high(self) -> float:
        return round(self.value + self.tolerance, 4)

    def as_dict(self) -> dict:
        return {"feature": self.feature, "family": self.family,
                "value": round(self.value, 4),
                "range": [self.low, self.high],
                "source": self.source, "unit": self.unit}


@dataclass
class Ruleset:
    fidelity: float
    targets: dict[str, Target] = field(default_factory=dict)
    categoricals: dict[str, tuple[str, str]] = field(default_factory=dict)
    signature: dict = field(default_factory=dict)
    exemplars: list[str] = field(default_factory=list)
    context_exemplars: list[str] = field(default_factory=list)
    confidence: str = "unknown"
    notes: list[str] = field(default_factory=list)

    def rigid(self) -> list[Target]:
        reg = registry()
        return [t for t in self.targets.values()
                if reg.get(t.feature) and reg[t.feature].elasticity == 0.0]

    def as_dict(self) -> dict:
        return {
            "fidelity": self.fidelity,
            "confidence": self.confidence,
            "targets": {k: v.as_dict() for k, v in self.targets.items()},
            "categoricals": {k: {"value": v[0], "source": v[1]}
                             for k, v in self.categoricals.items()},
            "signature": self.signature,
            "exemplars": self.exemplars,
            "notes": self.notes,
        }


def _tolerance(est: Estimate, fidelity: float) -> float:
    """Half-width of the acceptable band.

    Wider where the person is inconsistent, wider again where the sample is
    small, and never so tight that ordinary variation reads as a failure.
    """
    base = max(est.sd, abs(est.mean) * 0.15, 1e-3)
    support = 1.0 if est.n >= 8 else 1.0 + (8 - est.n) * 0.12
    strictness = 0.6 + (1.0 - fidelity) * 1.4
    return round(base * support * strictness * 1.25, 4)


def blend(user: Profile, context: Profile | None = None,
          fidelity: float = DEFAULT_FIDELITY) -> Ruleset:
    """Combine a person's measured voice with what the situation asks for."""
    fidelity = min(max(fidelity, 0.0), 1.0)
    reg = registry()
    rules = Ruleset(fidelity=fidelity, confidence=user.confidence)

    for name, est in user.scalars.items():
        f = reg.get(name)
        if not f:
            continue
        value, source = est.mean, "you"
        c_est = context.scalars.get(name) if context else None
        if c_est and f.elasticity > 0:
            pull = (1.0 - fidelity) * f.elasticity
            if pull > 0:
                value = est.mean + pull * (c_est.mean - est.mean)
                source = "you, adjusted" if pull < 0.5 else "context-led"
        rules.targets[name] = Target(name, f.family, value,
                                     _tolerance(est, fidelity), source, f.unit)

    for name, value in user.categoricals.items():
        source = "you"
        if context and name in context.categoricals:
            if name in CONTEXT_GOVERNED:
                value, source = context.categoricals[name], "context"
            elif user.consistency.get(name, 1.0) < 0.55:
                value, source = context.categoricals[name], "context (you vary)"
        rules.categoricals[name] = (value, source)

    rules.signature = user.signature
    rules.exemplars = user.exemplars
    if context:
        rules.context_exemplars = context.exemplars

    if context is None:
        rules.notes.append(
            "No context profile, so every target comes from your own writing.")
    else:
        moved = sum(1 for t in rules.targets.values() if t.source != "you")
        rules.notes.append(
            f"Fidelity {fidelity:.0%}. {moved} of {len(rules.targets)} "
            f"measures moved toward the context; the rest are yours "
            f"unchanged.")
    if user.confidence in ("thin", "provisional"):
        rules.notes.append(
            "The profile behind these numbers is thin, so treat the bands as "
            "direction rather than specification.")
    return rules
