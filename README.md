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

## Read this before trusting a number

The measurement was calibrated by running held-out authorship attribution
across 24 public domain authors. The full table is in
[docs/calibration.md](docs/calibration.md). The short version:

| profile | 800w passage | 3,200w passage |
|---|---|---|
| 5,000 words | 38% | 42% |
| 20,000 words | 55% | 75% |
| 40,000 words | 60% | 82% |

Chance is 4%, and the best cell reaches 92%, which is where published Delta
results sit. So the implementation works, and everything below that is a sample
size limit.

Two things follow.

**A small profile cannot identify anyone.** Under about 2,500 words the tool is
near chance. It will still build the profile, because the rhythm and
punctuation figures are real and useful for briefing a model, but it labels the
result `provisional` and says the distance should not be trusted alone.

**A short draft cannot be scored.** Below 800 words the function-word rates are
noise whatever you compare them against, and the report says so.

Used comparatively, to ask which of two drafts is closer, it works at far
smaller sizes than it does used absolutely, to ask whether one draft passes.

## What it measures

The features with the strongest replicated evidence for identifying an
individual author, all countable without a tagger or a model.

**Function word distributions.** How often someone reaches for *of* against
*from*, *but* against *however*. Unconscious, topic independent, and the basis
of authorship attribution since Mosteller and Wallace resolved the Federalist
Papers in 1964. Standardised against between-author variation measured from
`data/baseline.json`, which is what makes it Burrows's Delta rather than a
plain frequency distance.

**Character n-grams.** Three to five character sequences, which pick up
morphology and spelling habits that whole words miss.

**Recurrent phrases.** The multi-word sequences someone returns to without
noticing. Forensic linguistics locates idiolect here more than in rare
vocabulary.

**Rhythm.** Sentence length, and more importantly its spread.

**Punctuation, per mark.** Simple, strong, easy to check.

**Register.** Person, contractions, abstraction, hedging, negation.

Content words are not used to identify anyone. They track subject matter and
community rather than the individual, so they are recorded as a topic
descriptor and kept out of the identity signal.

Correlated features are grouped, so a single habit like contracting moves the
distance once rather than three times, and marks absent from both texts are
excluded rather than diluting the average.

## How context works

A person writes an email differently from a report while remaining
recognisably themselves. So identity and convention are separated, and only the
second gives way to the occasion.

```
target = you + (1 - fidelity) * elasticity * (occasion - you)
```

Fidelity defaults to 0.8. Elasticity is declared per feature. Function words,
rhythm and punctuation habit sit at zero and never move. Length, formality and
hedging give way. Capitalisation and numeral style cannot be averaged at all,
so they go to whichever side owns them, usually the occasion.

## Where profiles live

One markdown file per person, under `VOICEPRINT_HOME` or the platform data
directory. Readable, editable, deletable.

```bash
vp show yash      # read it
vp remove yash    # delete it
```

The prose at the top is for the person it describes. A fenced JSON block at the
bottom is how the tool reads it back.

## Getting the writing

Ordered, and it stops rather than improvising.

1. Connected sources, if the host has any, and only after asking
2. Files you name
3. Text you paste
4. Nothing, in which case it says so and exits

There is no fifth step where it approximates. A connector is read only after an
explicit yes: if no consent prompt is wired up, every connector is treated as
declined, so a host that forgets cannot quietly read a mailbox.

## How much writing

| words | label | what it is worth |
|---|---|---|
| 20,000+ | stable | the function-word measures hold |
| 10,000 to 20,000 | usable | good on long passages, weaker on short |
| 2,500 to 10,000 | thin | rhythm and punctuation only |
| under 2,500 | provisional | structure is real, distances are not |

Register matters as much as volume. Genre moves writing at least as much as
identity does (Biber 1988), so tag samples with `--register` and the tool keeps
them apart, falling back to a pooled profile where one register is thin.

## Using it from an agent

An MCP server over stdio, so one implementation serves every client that speaks
the protocol.

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
print(report.distance.overall, report.passed, report.reliable)
```

## What it will not do

It will not write for you. It measures, instructs and checks; the writing
happens elsewhere.

It will not identify an author from a paragraph. See the calibration table.

It will not defeat a provenance watermark. Those work on token sampling, not
syntax, and they exist so people can tell what a model wrote. This moves output
toward a person's measured statistics, which is a different thing.

It will not detect machine text reliably. The strongest signal for that is
token-level perplexity, which needs a language model, which this deliberately
does not have.

## Numbers that are still guesses

Named so they are not mistaken for method. The aggregate weighting
`0.45·delta + 0.35·scalar + 0.20·ngram`, the verdict bands at 0.6, 1.0 and 1.8
times tolerance, the n-gram cosine scaling, the tolerance strictness curve in
`blend.py`, and the materiality floors in `check.py`. Each is a defensible
heuristic and none is calibrated. The confidence tiers and the reliable-length
threshold are the two that now come from measurement.

## Reading

[docs/research.md](docs/research.md) for the evidence behind the feature set,
with verification status per source.
[docs/calibration.md](docs/calibration.md) for what the tool can resolve.
[docs/holdout-test.md](docs/holdout-test.md) for whether the brief changes the
writing, including the first version of that experiment which was too kind to
itself.

## Licence

MIT.
