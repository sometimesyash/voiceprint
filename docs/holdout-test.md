# Does the brief change the writing?

A hold-out test: build a profile on part of someone's writing, keep some back,
then compare their real held-out prose against a model writing the same kind of
thing with and without the brief.

Run twice. The first run flattered the tool. The second, after the measurement
was fixed and calibrated, did not, and the second is the one to read.

## Setup

Profile built from nine sent emails, 890 words. Two further emails held back.
The task given to the model was the one those emails perform: write to a senior
person asking for ten minutes during a visit.

## First run, before calibration

| text | overall | verdict |
|---|---|---|
| held out | 1.35 | acceptable |
| model, blind | 1.60 | drifting |
| model, briefed | 0.96 | acceptable |

Read on its own this looks like the brief cutting distance by 40%. It was
reported that way, and that was too generous, for two reasons found later.

**The measure was not Delta.** It scaled each word by its own sampling noise
rather than by how much that word varies between people, so it could not know
which words separate authors. It has since been rebuilt against a 24 author
reference.

**Nothing had been checked against a stranger.** When that was finally done, a
completely different person scored 1.24 against the profile and passed as
`acceptable`, while a genuine held-out email scored 2.16 and failed as
`drifting`. The thresholds were doing no work.

## Second run, after calibration

| text | delta | overall | verdict |
|---|---|---|---|
| model, briefed | 2.22 | 1.47 | acceptable |
| other author B | 2.09 | 1.75 | drifting |
| model, blind | 3.08 | 2.04 | drifting |
| other author C | 2.67 | 2.15 | drifting |
| held out B | 3.01 | 2.17 | drifting |
| held out A | 3.30 | 2.21 | drifting |

The briefed draft still comes out closest, and the blind draft is still well
behind it, so the brief does move the writing. Everything else in the table is
noise: real emails by the profile's own author sit further away than a stranger
does.

That is the correct result for an 890-word profile. The calibration in
[calibration.md](calibration.md) puts attribution near chance below 2,500
words, and this profile is a third of that. The tool now labels it
`provisional` and says the distance figures should not be trusted alone, which
is the honest reading.

## What it establishes

**The brief has an effect.** Briefed beat blind in both runs, by 0.64 and 0.57.
That is the one claim the experiment supports.

**Nothing about authenticity.** A briefed draft scoring closer than real
writing does not mean it is more authentically the person. The brief optimises
directly for the measured centre; a real email sits wherever it sits.

**Nothing about identification.** At this sample size the tool cannot tell this
person from a stranger, and no longer pretends otherwise.

## The register confound, seen live

Held-out email B scored badly in both runs for a specific reason: it is written
on behalf of a cohort, so it runs in the first person plural where every
training email is first person singular.

Biber's finding is that genre moves writing at least as much as identity does.
Here a shift from *I* to *we* inside the same medium was enough to push a
genuine email out of range. It is the argument for tagging registers and
keeping them apart.

## Reproducing

```bash
vp build someone corpus/train --register email
vp diff someone corpus/holdout/kept-back.txt
vp brief someone --task "the thing being written"
vp diff someone drafts/written-to-the-brief.md
```

Score a stranger's writing too. Without that the numbers mean very little,
which is the lesson of the first run.
