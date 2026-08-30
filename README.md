# voiceprint

Measure how a person writes. Hold generated prose to the measurement.

Anything a model writes for you drifts toward the way models write: sentences
of similar length, hedge then assert, the occasional stacked fragment for
weight. Telling it to "write like me" does not fix that, because the
instruction is an adjective and the problem is a distribution.

This measures a person's writing and gives the model numbers to hit instead.

```bash
pip install voiceprint

vp build yash ~/Documents/writing
vp brief yash --task "reply to a colleague about the timeline"   # before drafting
vp check yash draft.md                                            # after
```

## What it measures

The features with the strongest replicated evidence for identifying an
individual author, all of them countable without a tagger or a model.

**Function word distributions.** How often someone reaches for *of* against
*from*, *but* against *however*. Unconscious, topic independent, and the basis
of authorship attribution since Mosteller and Wallace resolved the Federalist
Papers in 1964.

**Character n-grams.** Three to five character sequences, which pick up
morphology and spelling habits that whole words miss.

**Recurrent phrases.** The multi-word sequences someone returns to without
noticing. Forensic linguistics locates idiolect here more than in rare
vocabulary.

**Rhythm.** Sentence length, and more importantly its spread. Uniform sentence
length is the most visible symptom of generated prose.

**Punctuation, per mark.** Simple, strong, and easy to check.

**Register.** Person, contractions, abstraction, hedging, negation.

It does not use content words to identify anyone. Those track subject matter
and community rather than the individual, so they are recorded as a topic
descriptor and kept out of the identity signal.

## How context works

A person writes an email differently from a report while remaining
recognisably themselves. So the tool separates what is identity from what is
convention, and only lets the occasion move the second.

```
target = you + (1 - fidelity) * elasticity * (occasion - you)
```

Fidelity defaults to 0.8. Elasticity is declared per feature. Function words,
rhythm and punctuation habit sit at zero and never move, whatever the dial
says. Length, formality and hedging give way. Capitalisation and numeral style
cannot be averaged at all, so they are handed to whichever side owns them,
usually the occasion.

## Where profiles live

One markdown file per person, under `VOICEPRINT_HOME` or the platform data
directory. Readable, editable, deletable.

```bash
vp show yash      # read it
vp remove yash    # delete it
```

The prose at the top is for the person it describes. A fenced JSON block at
the bottom is how the tool reads it back.

## Getting the writing

Ordered, and it stops rather than improvising.

1. Connected sources, if the host has any, and only after asking
2. Files you name
3. Text you paste
4. Nothing, in which case it says so and exits

There is no fifth step where it approximates. A profile that was guessed is
worse than no profile, because everything downstream trusts it.

## How much writing

Frequency measures settle around five thousand words and degrade badly below
about two and a half thousand (Eder 2015). Profiles are built below that and
labelled accordingly.

| words | label |
|---|---|
| 5,000+ | stable |
| 2,000 to 5,000 | usable |
| 400 to 2,000 | thin |
| under 400 | provisional |

Register matters as much as volume. Genre moves writing at least as much as
identity does (Biber 1988), so tag samples with `--register` and the tool
keeps them apart, falling back to a pooled profile where one register is thin.

## Using it from an agent

An MCP server over stdio, so one implementation serves every client that
speaks the protocol.

```json
{
  "mcpServers": {
    "voiceprint": { "command": "python", "args": ["-m", "voiceprint.mcp"] }
  }
}
```

Ready-made manifests for Claude, Codex and Cursor are in the plugin
directories, generated from `skills/` by `scripts/sync.py`.

## As a library

Standard library only. The optional PDF reader is the sole extra.

```python
from voiceprint import store, blend_rules, against_rules

vp = store.load("yash")
profile = vp.profile_for("email")
rules = blend_rules(profile, None, fidelity=0.8)

report = against_rules(draft, rules, profile)
print(report.distance.overall, report.passed)
```

## What it will not do

It will not write for you. It measures, instructs and checks; the writing
happens elsewhere.

It will not defeat a provenance watermark. Those work on token sampling, not
syntax, and they exist so people can tell what a model wrote. This moves
output toward a person's measured statistics, which is a different thing.

It will not detect machine text reliably. The strongest signal for that is
token-level perplexity, which needs a language model, which this deliberately
does not have.

## Reading

The evidence behind the feature set is in [docs/research.md](docs/research.md),
with what is cited and what is calibration.

## Licence

MIT.
