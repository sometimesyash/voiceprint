# What this can and cannot resolve

Every threshold in the code is set from the table below. It was produced by
`scripts/calibrate.py`, which runs held-out authorship attribution across 24
public domain authors: profiles are built from the first half of each author's
text and test passages drawn from the second, so no passage ever appears in the
profile it is scored against.

Chance is 4%.

| profile words | 400w passage | 800w | 1,600w | 3,200w | 6,400w |
|---|---|---|---|---|---|
| 2,500 | 8% | 22% | 32% | 45% | 45% |
| 5,000 | 20% | 38% | 42% | 42% | 52% |
| 10,000 | 25% | 48% | 72% | 70% | 82% |
| 20,000 | 25% | 55% | 68% | 75% | 90% |
| 40,000 | 28% | 60% | 75% | 82% | 92% |

## What the table says

**The implementation is sound.** Accuracy reaches 92%, which is in line with
published Delta results. A broken implementation would sit near chance
everywhere. Everything below the top right is a sample size limit, not a bug.

**Both sizes matter, and independently.** A large profile does not rescue a
short passage: 40,000 words of reference still only manages 28% on a 400-word
sample. The function-word rates in a short text are noise whatever you compare
them against.

**Five thousand words is not enough.** Eder's widely cited ~5,000 word
threshold gets 42% here, against 24 candidate authors. It is well above chance
and clearly carrying signal, but it is not a profile that can be trusted to
identify anybody on its own.

## What was changed because of it

The confidence tiers were originally 5,000 / 2,000 / 400 words, chosen from the
literature and from feel. Measured against the table they were far too
generous, so they moved:

| tier | words | measured accuracy on long passages |
|---|---|---|
| stable | 20,000+ | about 90% |
| usable | 10,000 to 20,000 | 70 to 82% |
| thin | 2,500 to 10,000 | about 45% |
| provisional | under 2,500 | near chance |

`check.py` also gained `RELIABLE_WORDS = 800`. Below that a draft is still
checked on rhythm and punctuation, but the report says the function-word
distance cannot be trusted and asks to be read comparatively.

## The limits of the calibration itself

It is fiction, mostly nineteenth century, all book length. Working prose is
shorter, more formulaic and more constrained by genre, and may behave
differently in either direction. Twenty-four candidate authors is a harder
task than the two-way question the tool usually faces, so the percentages are
pessimistic for that use, though the shape of the curve holds.

Rerun it on a corpus closer to your own material before treating these as
exact.

## Reproducing

```bash
python scripts/build_baseline.py --gutenberg   # 24 authors, ~2.5M words
python scripts/calibrate.py                    # the table above
python scripts/discrimination.py               # against your own corpus
```
