"""Checking a draft against a profile."""
from __future__ import annotations

from dataclasses import dataclass, field

from .blend import Ruleset
from .distance import Distance, measure
from .doc import Doc
from .features import extract, registry
from .features.structure import is_stacked
from .profile import Profile
from . import text as T

FAIL_Z = 2.5
WARN_Z = 1.5

# A rate that is zero in the profile and tiny in the draft is not evidence of
# anything. One question mark in nine hundred words should not fail a check
# just because the sample happened not to contain one.
MATERIAL = {
    "per 100w": 0.35,
    "0-1": 0.06,
    "words": 1.5,
    "chars": 0.3,
    "ratio": 0.08,
    "per sentence": 0.15,
}
DEFAULT_MATERIAL = 0.1


@dataclass
class Finding:
    severity: str
    feature: str
    message: str
    fix: str = ""

    def as_dict(self) -> dict:
        return {"severity": self.severity, "feature": self.feature,
                "message": self.message, "fix": self.fix}


@dataclass
class Report:
    distance: Distance
    findings: list[Finding] = field(default_factory=list)
    words: int = 0

    @property
    def failures(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "FAIL"]

    @property
    def passed(self) -> bool:
        return not self.failures

    def as_dict(self) -> dict:
        return {"words": self.words, "passed": self.passed,
                "distance": self.distance.as_dict(),
                "findings": [f.as_dict() for f in self.findings]}

    def to_markdown(self) -> str:
        d = self.distance
        L = [f"Voice distance {d.overall:.2f} ({d.verdict()}). "
             f"Delta {d.delta:.2f}, scalars {d.scalar:.2f}, "
             f"n-grams {d.ngram:.2f}.", ""]
        if not self.findings:
            L.append("Nothing to flag.")
            return "\n".join(L)
        for f in self.findings:
            L.append(f"**{f.severity}** {f.message}")
            if f.fix:
                L.append(f"  {f.fix}")
        return "\n".join(L)


FIXES = {
    "rhythm.words_per_sentence": ("Split the longest sentences.",
                                  "Join some short sentences."),
    "rhythm.length_cv": ("Even out the extremes.",
                         "Vary the lengths; matched sentences read as machine-made."),
    "register.contractions_per100": ("Spell more of them out.",
                                     "Use contractions where speech would."),
    "register.nominalisation_per100": ("Replace -tion and -ment nouns with verbs.",
                                       "This register carries more abstraction."),
    "punct.comma_per100": ("Cut commas; break clauses into sentences.",
                           "Let clauses run together more."),
    "punct.em_dash_per100": ("Cut the em dashes.", ""),
    "punct.semicolon_per100": ("Cut the semicolons.", ""),
    "shape.fragment_rate": ("Finish the sentences.", "Loosen into fragments."),
    "shape.stacked_rate": ("Rewrite stacked fragments as single statements.", ""),
}


def _fix_for(feature: str, high: bool) -> str:
    pair = FIXES.get(feature)
    return (pair[0] if high else pair[1]) if pair else ""


def _material(feature: str, observed: float, expected: float) -> bool:
    """Is the gap big enough to be worth saying?"""
    f = registry().get(feature)
    floor = MATERIAL.get(f.unit if f else "", DEFAULT_MATERIAL)
    return abs(observed - expected) >= floor


def against_profile(draft: str, profile: Profile) -> Report:
    """Measure a draft and name whatever sits furthest out."""
    doc = Doc(draft)
    dist = measure(draft, profile)
    report = Report(distance=dist, words=doc.n_words)
    reg = registry()

    if doc.n_words < 40:
        report.findings.append(Finding(
            "WARN", "length",
            f"Only {doc.n_words} words. Too short to measure reliably."))
        return report

    for dev in dist.worst:
        if abs(dev.z) < WARN_Z:
            continue
        if not _material(dev.feature, dev.observed, dev.expected):
            continue
        sev = "FAIL" if abs(dev.z) >= FAIL_Z else "WARN"
        f = reg.get(dev.feature)
        if f and f.elasticity >= 0.6 and sev == "FAIL":
            sev = "WARN"
        report.findings.append(Finding(
            sev, dev.feature,
            f"{dev.feature} is {dev.observed:g} against your {dev.expected:g} "
            f"({dev.direction}, {abs(dev.z):.1f} sd)",
            _fix_for(dev.feature, dev.z > 0)))

    stacked = [p for p in T.paragraphs(draft) if is_stacked(p)]
    allowed = profile.scalars.get("shape.stacked_rate")
    ceiling = max((allowed.mean if allowed else 0.0) + 0.05, 0.05)
    rate = len(stacked) / max(len(T.paragraphs(draft)), 1)
    if rate > ceiling:
        report.findings.append(Finding(
            "FAIL", "shape.stacked_rate",
            f"Stacked fragments in {rate:.0%} of paragraphs against your "
            f"{(allowed.mean if allowed else 0):.0%}.",
            "State the idea once, as a sentence. For example: "
            + (f"{stacked[0][:70]}..." if stacked else "")))

    if dist.delta > 2.5:
        report.findings.append(Finding(
            "FAIL", "delta",
            f"Function-word distance {dist.delta:.2f}. The underlying grammar "
            f"is not yours, whatever the surface looks like.",
            "Rewrite from scratch rather than editing."))
    return report


def against_rules(draft: str, rules: Ruleset, profile: Profile) -> Report:
    """Check against blended targets, so context-led measures are judged fairly."""
    report = against_profile(draft, profile)
    doc = Doc(draft)
    observed = extract(doc, kinds=("scalar", "categorical"))

    for name, (want, source) in rules.categoricals.items():
        got = observed.get(name)
        if isinstance(got, str) and got != want and got != "none":
            report.findings.append(Finding(
                "WARN", name, f"{name} is {got}, expected {want} ({source})."))

    kept = []
    for f in report.findings:
        t = rules.targets.get(f.feature)
        if t and f.severity == "FAIL":
            val = observed.get(f.feature)
            if isinstance(val, (int, float)) and t.low <= val <= t.high:
                continue
        kept.append(f)
    report.findings = kept
    return report
