---
name: writing-in-your-voice
description: Use when writing anything in a specific person's voice - emails, messages, documents, posts, decks, replies. Measures how they actually write from their own prose, then holds the draft to those measurements instead of guessing at their style. Triggers on "write this as me", "in my voice", "sounds like me", "draft a reply from me", or any request to produce text that must read as though a particular person wrote it.
---

# Writing in your voice

Anything you write for someone will read as generated unless it is measured
against how they actually write. This skill measures first, drafts second, and
checks the draft against the measurement before returning it.

## Before you write anything

Check the profile exists.

```bash
vp list
```

If the person has no profile, stop. Do not write in a voice you have not
measured, and do not infer one from their name, their job, or the way they
phrased the request. Go to `building-a-voiceprint` instead.

## The loop

**1. Get the brief.** Tell it what you are writing, in plain words.

```bash
vp brief yash --task "reply to Andrii about the GTM timeline"
```

The brief comes back with three parts. Targets you must hold, which are
identity and do not move. Conventions, which the occasion governs. Phrases the
person actually reuses, and real sentences of theirs to match.

**2. Draft.** Follow the brief. Where it contradicts your instincts about good
writing, follow the brief: the instincts are what make text read as machine
written.

**3. Check.** Always. A draft you have not checked is a guess.

```bash
vp check yash draft.md
```

**4. Rewrite what failed.** Each finding names the measure, the gap, and what
to do. Rewrite and check again. Two or three passes is normal.

Exit code 0 means it passed. Anything else means you are not finished.

## What the numbers mean

`Voice distance` aggregates identity, scalars and n-grams. Identity is the
important one: it blends two measures, Delta over function words and texture
over character n-grams, weighted by how much text there is. The report names
which arm decided.

- under 0.9, close
- 0.9 to 1.5, acceptable
- 1.5 to 2.7, drifting
- above 2.7, off

**These bands are uncalibrated.** They are useful for comparing two drafts of
the same thing and unreliable as a pass mark. A stranger can land inside them.
If you need certainty, compare drafts against each other rather than against
the threshold.

A draft under 500 words is judged on texture alone, and a profile under 1,500
words cannot identify anyone. The report says so when either applies. See
`docs/calibration.md`.

## Fidelity

The dial is how much the occasion is allowed to move the voice. It defaults to
0.8, meaning four fifths the person and one fifth the situation.

```bash
vp brief yash --task "board paper" --fidelity 0.7
vp brief yash --task "quick note to a colleague" --fidelity 0.9
```

Rhythm, punctuation habit and function words never move whatever the dial
says. They are the person. What moves is length, formality, hedging and
contractions, which is what actually differs between an email and a report.

## What not to do

**Do not paraphrase the brief into adjectives.** "Write concisely and
professionally" throws away everything measured and replaces it with your own
taste. Use the numbers.

**Do not skip the check because the draft reads well to you.** It reads well
to you because you wrote it. That is the failure mode.

**Do not force the phrase list.** Those are phrases the person reaches for,
not phrases they must use. Salting them in reads worse than omitting them.

**Do not write in a voice with no profile.** Say you cannot, and offer to
build one.

## Fallback with no CLI

Import it. The library is standard library only.

```python
from voiceprint import store, blend_rules, against_rules, brief_markdown

vp = store.load("yash")
profile = vp.profile_for("email")
rules = blend_rules(profile, None, 0.8)
print(brief_markdown(rules, vp.name))

report = against_rules(draft, rules, profile)
print(report.to_markdown())
```
