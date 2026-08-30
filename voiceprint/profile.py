"""Corpus to Voiceprint.

Confidence tiers follow Eder (2015), who found frequency-based attribution
reliable around 5,000 words and badly degraded below 2,500. A profile below
that is not refused, but it is labelled, and the label travels with every
figure taken from it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from . import signature as sig
from . import texture as TX
from . import windows as W
from .corpus import Corpus
from .doc import Doc
from .features.lexical import (char_ngram_profile, function_word_vector,
                               punctuation_shape, topic_words)

SCHEMA = 1

# Set from scripts/calibrate.py, which measures held-out attribution accuracy
# against 24 authors using both arms. The tiers name what a profile can
# actually resolve rather than what would be convenient. Adding the texture
# arm moved these down: 5,000 words now does what 10,000 used to.
# See docs/calibration.md.
STABLE_WORDS = 10000
USABLE_WORDS = 5000
THIN_WORDS = 1500


def confidence(words: int) -> str:
    if words >= STABLE_WORDS:
        return "stable"
    if words >= USABLE_WORDS:
        return "usable"
    if words >= THIN_WORDS:
        return "thin"
    return "provisional"


CONFIDENCE_NOTE = {
    "stable": "Enough writing for both measures to hold. In testing this "
              "size resolved the right author 70 to 95% of the time.",
    "usable": "Workable. Around 45 to 62% correct in testing, well above "
              "chance and enough to brief a writer with confidence.",
    "thin": "Below the size where the word-frequency measure settles. "
            "Identity is judged on character texture instead, which holds up "
            "better here, but treat the figures as directional.",
    "provisional": "Too little writing to measure properly. The shape of the "
                   "writing is real and worth briefing from; the distance "
                   "figures are not trustworthy on their own.",
}


@dataclass
class Profile:
    """One register's measurements."""
    register: str
    words: int
    windows: int
    confidence: str
    scalars: dict[str, W.Estimate] = field(default_factory=dict)
    categoricals: dict[str, str] = field(default_factory=dict)
    consistency: dict[str, float] = field(default_factory=dict)
    function_words: dict[str, float] = field(default_factory=dict)
    char_ngrams: dict[str, float] = field(default_factory=dict)
    texture: dict[str, dict[str, float]] = field(default_factory=dict)
    punct_shapes: dict[str, float] = field(default_factory=dict)
    signature: dict = field(default_factory=dict)
    topics: list[str] = field(default_factory=list)
    exemplars: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "register": self.register, "words": self.words,
            "windows": self.windows, "confidence": self.confidence,
            "scalars": {k: v.as_dict() for k, v in self.scalars.items()},
            "categoricals": self.categoricals,
            "consistency": self.consistency,
            "function_words": self.function_words,
            "char_ngrams": self.char_ngrams,
            "texture": self.texture,
            "punct_shapes": self.punct_shapes,
            "signature": self.signature,
            "topics": self.topics,
            "exemplars": self.exemplars,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Profile":
        p = cls(d["register"], d["words"], d["windows"], d["confidence"])
        p.scalars = {k: W.Estimate.from_dict(v)
                     for k, v in d.get("scalars", {}).items()}
        for key in ("categoricals", "consistency", "function_words",
                    "char_ngrams", "texture", "punct_shapes", "signature"):
            setattr(p, key, d.get(key, {}))
        p.topics = d.get("topics", [])
        p.exemplars = d.get("exemplars", [])
        return p


@dataclass
class Voiceprint:
    name: str
    schema: int = SCHEMA
    built_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    words: int = 0
    registers: dict[str, Profile] = field(default_factory=dict)
    pooled: Profile | None = None
    manifest: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def profile_for(self, register: str | None = None) -> Profile | None:
        """Register-specific where the data supports it, pooled otherwise."""
        if register and register in self.registers:
            p = self.registers[register]
            if p.confidence != "provisional":
                return p
        return self.pooled

    def as_dict(self) -> dict:
        return {
            "name": self.name, "schema": self.schema,
            "built_at": self.built_at, "words": self.words,
            "registers": {k: v.as_dict() for k, v in self.registers.items()},
            "pooled": self.pooled.as_dict() if self.pooled else None,
            "manifest": self.manifest, "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Voiceprint":
        vp = cls(d["name"], d.get("schema", SCHEMA), d.get("built_at", ""),
                 d.get("words", 0))
        vp.registers = {k: Profile.from_dict(v)
                        for k, v in (d.get("registers") or {}).items()}
        vp.pooled = Profile.from_dict(d["pooled"]) if d.get("pooled") else None
        vp.manifest = d.get("manifest", [])
        vp.notes = d.get("notes", [])
        return vp


def exemplars(texts: list[str], n: int = 8) -> list[str]:
    """Verbatim sentences spanning the length range.

    Real sentences carry more than any statistic. Taken across the range
    rather than off the top, so the reader sees how short and how long this
    person actually goes.
    """
    from . import text as T
    seen, uniq = set(), []
    for t in texts:
        for s in T.sentences(t):
            s = T.normalise(s)
            k = s.lower()
            if 6 <= len(T.words(s)) <= 45 and k not in seen:
                seen.add(k)
                uniq.append(s)
    if len(uniq) <= n:
        return uniq
    uniq.sort(key=lambda s: len(T.words(s)))
    idx = [round(i * (len(uniq) - 1) / (n - 1)) for i in range(n)]
    return [uniq[i] for i in sorted(set(idx))]


def _profile(texts: list[str], register: str,
             baseline: dict | None = None) -> Profile | None:
    pooled = Doc(" ".join(texts))
    # A short corpus is windowed with overlap so there are still enough windows
    # to see how much the person varies.
    overlap = 0.5 if pooled.n_words < USABLE_WORDS else 0.0
    chunks = W.windows(texts, overlap=overlap)
    if not chunks:
        return None
    est, cats = W.aggregate(chunks, overlap=overlap)
    p = Profile(
        register=register,
        words=pooled.n_words,
        windows=len(chunks),
        confidence=confidence(pooled.n_words),
        scalars=est,
        categoricals=cats,
        consistency=W.categorical_consistency(chunks),
        function_words=function_word_vector(pooled),
        char_ngrams=char_ngram_profile(pooled),
        texture=TX.profile(pooled),
        punct_shapes=punctuation_shape(pooled),
        signature=sig.build(texts, baseline=baseline).as_dict(),
        topics=topic_words(pooled),
        exemplars=exemplars(texts),
    )
    return p


def build(corpus: Corpus, name: str,
          baseline: dict | None = None) -> Voiceprint:
    """Measure a corpus, per register and pooled."""
    vp = Voiceprint(name=name, words=corpus.words, manifest=corpus.manifest())

    for register, samples in corpus.by_register().items():
        p = _profile([s.text for s in samples], register, baseline)
        if p:
            vp.registers[register] = p

    vp.pooled = _profile(corpus.texts, "pooled", baseline)

    if vp.pooled:
        vp.notes.append(CONFIDENCE_NOTE[vp.pooled.confidence])
    if len(vp.registers) > 1:
        vp.notes.append(
            "Built from more than one register. Register shifts a person's "
            "writing at least as much as identity does, so the pooled figures "
            "average across genres; prefer a register-specific profile where "
            "one is available.")
    thin = [r for r, p in vp.registers.items()
            if p.confidence in ("thin", "provisional")]
    if thin:
        vp.notes.append(
            "Thin on: " + ", ".join(sorted(thin))
            + ". These fall back to the pooled profile.")
    if vp.pooled and not baseline:
        vp.notes.append(
            "No background corpus was supplied, so recurrent phrases are "
            "ranked by raw frequency and will include ordinary English "
            "alongside anything characteristic.")
    return vp
