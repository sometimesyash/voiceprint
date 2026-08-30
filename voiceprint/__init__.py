"""Measure how a person writes; hold generated prose to it."""
from __future__ import annotations

__version__ = "0.1.0"

from .blend import DEFAULT_FIDELITY, Ruleset
from .blend import blend as blend_rules
from .check import Report, against_profile, against_rules
from .context import Context, infer
from .corpus import ConsentDenied, Corpus, Ladder, NoCorpus, Sample
from .distance import Distance, measure
from .doc import Doc
from .profile import Profile, Voiceprint, build
from .render import brief_markdown, to_markdown
from .store import ProfileExists, ProfileMissing, exists, load, save

__all__ = [
    "__version__",
    "Doc", "Sample", "Corpus", "Ladder", "NoCorpus", "ConsentDenied",
    "Profile", "Voiceprint", "build",
    "Distance", "measure",
    "Ruleset", "blend_rules", "DEFAULT_FIDELITY",
    "Context", "infer",
    "Report", "against_profile", "against_rules",
    "to_markdown", "brief_markdown",
    "save", "load", "exists", "ProfileMissing", "ProfileExists",
]
