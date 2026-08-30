"""Rendering a voiceprint as something a person can read."""
from __future__ import annotations

from .blend import Ruleset
from .profile import CONFIDENCE_NOTE, Profile, Voiceprint

PERSON = {
    "first_singular": "writes as I",
    "first_plural": "writes as we",
    "second": "addresses the reader as you",
    "third": "writes about others in the third person",
    "impersonal": "keeps pronouns out of it",
}

CAPS = {"upper": "ALL CAPS", "title": "Title Case", "sentence": "Sentence case",
        "lower": "all lowercase", "none": "no settled pattern"}

TERM = {"full_stop": "a full stop", "question": "a question mark",
        "exclamation": "an exclamation mark", "colon": "a colon",
        "ellipsis": "an ellipsis", "none": "nothing"}


def _get(p: Profile, name: str, default: float = 0.0) -> float:
    e = p.scalars.get(name)
    return e.mean if e else default


def _prose(p: Profile) -> list[str]:
    """The measurements, said in sentences."""
    wps = _get(p, "rhythm.words_per_sentence")
    sd = _get(p, "rhythm.sentence_sd")
    cv = _get(p, "rhythm.length_cv")
    lines = []

    if wps:
        even = ("very even" if cv < 0.35 else
                "varied" if cv < 0.7 else "highly uneven")
        lines.append(
            f"Sentences run to about {wps:.0f} words, give or take {sd:.0f}, "
            f"which makes the rhythm {even} (variation {cv:.2f}).")

    person = p.categoricals.get("person.dominant", "impersonal")
    contractions = _get(p, "register.contractions_per100")
    lines.append(
        f"The writing {PERSON.get(person, 'stays impersonal')} and uses "
        f"{contractions:.1f} contractions per hundred words"
        + (", so it is spoken rather than formal." if contractions >= 1.5
           else "." if contractions >= 0.4
           else ", spelling things out in full."))

    nominal = _get(p, "register.nominalisation_per100")
    long_words = _get(p, "word.long_rate") * 100
    lines.append(
        f"Abstraction sits at {nominal:.1f} nominalisations per hundred words "
        f"with {long_words:.0f}% long words, which is "
        + ("an abstract register." if nominal >= 6 else "concrete."))

    marks = sorted(
        ((k.split(".")[1].replace("_per100", "").replace("_", " "), e.mean)
         for k, e in p.scalars.items()
         if k.startswith("punct.") and k.endswith("_per100")
         and not k.endswith("density_per100") and e.mean > 0.05),
        key=lambda kv: -kv[1])[:5]
    if marks:
        lines.append("Punctuation per hundred words: "
                     + ", ".join(f"{k} {v:.1f}" for k, v in marks) + ".")

    caps = p.categoricals.get("caps.dominant")
    term = p.categoricals.get("terminal.dominant")
    if caps and term:
        lines.append(f"Sentences are {CAPS.get(caps, caps)} and end with "
                     f"{TERM.get(term, term)}.")

    stacked = _get(p, "shape.stacked_rate")
    lines.append(
        f"Stacked fragments appear in {stacked:.0%} of paragraphs"
        + ("." if stacked >= 0.05 else
           ", which is to say effectively never, so they should not appear "
           "in anything written to this profile."))

    richness = _get(p, "richness.mtld")
    if richness:
        lines.append(f"Lexical diversity, length-corrected, is {richness:.0f} "
                     f"MTLD.")
    return lines


def _phrases(p: Profile, limit: int = 12) -> list[str]:
    sig = p.signature or {}
    out = []
    for key, label in (("bundles", "Phrases it returns to"),
                       ("openers", "Sentence openings"),
                       ("fillers", "Connective habits")):
        items = (sig.get(key) or [])[:limit]
        if items:
            out.append(f"**{label}.** "
                       + ", ".join(f"{i['text']} ({i['count']})" for i in items))
    return out


def to_markdown(vp: Voiceprint) -> str:
    """A voiceprint as a document, not a data dump."""
    L = [f"# Voiceprint: {vp.name}", ""]
    L.append(f"Built {vp.built_at} from {vp.words:,} words across "
             f"{len(vp.manifest)} samples.")
    L.append("")

    if vp.pooled:
        L.append(f"**Confidence: {vp.pooled.confidence}.** "
                 + CONFIDENCE_NOTE[vp.pooled.confidence])
        L.append("")

    if vp.notes:
        for n in vp.notes:
            L.append(f"- {n}")
        L.append("")

    if vp.pooled:
        L.append("## How this person writes")
        L.append("")
        L.extend(_prose(vp.pooled))
        L.append("")

        phrases = _phrases(vp.pooled)
        if phrases:
            L.append("## What they repeat")
            L.append("")
            L.extend(phrases)
            L.append("")

        if vp.pooled.exemplars:
            L.append("## In their own words")
            L.append("")
            for ex in vp.pooled.exemplars:
                L.append(f"> {ex}")
                L.append("")

    if len(vp.registers) > 1:
        L.append("## By register")
        L.append("")
        L.append("| register | words | confidence | sentence length | variation |")
        L.append("|---|---|---|---|---|")
        for name, p in sorted(vp.registers.items()):
            L.append(f"| {name} | {p.words:,} | {p.confidence} | "
                     f"{_get(p, 'rhythm.words_per_sentence'):.0f}w | "
                     f"{_get(p, 'rhythm.length_cv'):.2f} |")
        L.append("")

    if vp.manifest:
        L.append("## Sources")
        L.append("")
        for m in vp.manifest[:40]:
            L.append(f"- {m['origin']} ({m['register']}, {m['words']} words)")
        if len(vp.manifest) > 40:
            L.append(f"- and {len(vp.manifest) - 40} more")
        L.append("")

    L.append("---")
    L.append("")
    L.append("Delete this file to remove the profile. The block below is how "
             "the tool reads it back; the prose above is for you.")
    return "\n".join(L)


def brief_markdown(rules: Ruleset, name: str = "you") -> str:
    """The instruction a writing agent receives."""
    L = [f"# Write as {name}", ""]
    L.extend(rules.notes)
    L.append("")
    L.append("These are measurements from real writing, not a style guide. "
             "Where they cut against your instincts about good prose, follow "
             "them anyway; the instincts are what make text read as generated.")
    L.append("")

    L.append("## Hold these")
    L.append("")
    rigid = sorted(rules.rigid(), key=lambda t: t.feature)
    if rigid:
        L.append("| measure | target | acceptable | unit |")
        L.append("|---|---|---|---|")
        for t in rigid:
            L.append(f"| {t.feature} | {t.value:.2f} | "
                     f"{t.low:.2f} to {t.high:.2f} | {t.unit} |")
        L.append("")
        L.append("These are identity. Nothing about the occasion moves them.")
        L.append("")

    L.append("## Convention")
    L.append("")
    for k, (v, src) in sorted(rules.categoricals.items()):
        L.append(f"- `{k}`: **{v}** ({src})")
    L.append("")

    sig = rules.signature or {}
    if sig.get("bundles"):
        L.append("## Their phrases")
        L.append("")
        L.append("Reach for these where they fit. Do not force them.")
        L.append("")
        for item in sig["bundles"][:15]:
            L.append(f"- {item['text']}")
        L.append("")

    if rules.exemplars:
        L.append("## Match this voice")
        L.append("")
        for ex in rules.exemplars:
            L.append(f"> {ex}")
            L.append("")

    L.append("## Before you return it")
    L.append("")
    L.append("Read it back and ask whether any sentence could appear unchanged "
             "in a piece about something else. If it could, it is filler; "
             "replace it with the specific thing it was standing in for.")
    return "\n".join(L)
