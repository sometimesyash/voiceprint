# Does the brief actually change the writing?

Run on 30 August 2026, against a thin profile, so the numbers are indicative
rather than settled. The design is a hold-out test: build a profile on part of
someone's writing, keep some back, then compare their real held-out prose
against a model writing the same kind of thing with and without the brief.

## Setup

Profile built from nine sent emails, 890 words, confidence `thin`. Two further
emails held back and never seen by the profile. The task for the model was the
one those emails perform: write to a senior person asking for ten minutes
during a visit.

Three texts were then measured.

- **Held out.** Real writing by the person, excluded from the corpus.
- **Blind.** Written by the model on instinct, told only the task.
- **Briefed.** Written by the same model, same task, given `vp brief`.

## Result

| text | delta | scalars | n-grams | overall | verdict |
|---|---|---|---|---|---|
| held out | 1.59 | 0.75 | 1.87 | **1.35** | acceptable |
| blind | 2.38 | 0.75 | 1.34 | **1.60** | drifting |
| briefed | 1.23 | 0.51 | 1.11 | **0.96** | acceptable |

The brief cut the distance by 40%, and the briefed draft landed closer to the
profile than the person's own held-out email did.

That last part is worth being careful about rather than pleased by. A briefed
draft scoring better than real writing does not mean it is more authentic. It
means the brief optimises directly for the measured centre while a real email
sits wherever it sits, and on a thin profile the centre is drawn from very
little. Scoring close is evidence the instrument is measuring something real,
not evidence the writing is indistinguishable.

## The second hold-out

The other held-out email scored 2.16, drifting. It was written on behalf of a
cohort rather than for himself, so it runs in the first person plural where
everything in the corpus is first person singular.

This is the register confound arriving on schedule. Biber's finding is that
genre moves writing at least as much as identity does, and here a shift from
*I* to *we* inside the same medium was enough to push a genuine email out of
range. It is the argument for tagging registers and keeping them apart, and it
is why a single pooled profile should be treated as an average rather than a
description.

## What this does not show

The corpus was 890 words against the roughly 5,000 the literature asks for, all
of it one person writing similar emails over a few weeks. Delta is noisy at
that size, and the phrase list contains formulations repeated across near
duplicate networking emails rather than habits that would survive across genres.

Rerun it on a stable profile across several registers before treating any of
these figures as calibration.

## Reproducing

```bash
vp build someone corpus/train --register email
vp diff someone corpus/holdout/kept-back.txt
vp brief someone --task "the thing being written"
vp diff someone drafts/written-to-the-brief.md
```
