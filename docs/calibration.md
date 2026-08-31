# What this can and cannot resolve

Every threshold in the code is set from the tables below, produced by
`scripts/calibrate.py`. It runs held-out authorship attribution across 24
public domain authors: profiles come from the first half of each author's text
and test passages from the second, so no passage appears in the profile it is
scored against.

Chance is 4%.

## Two arms

Identity is judged two ways, because they fail in different places.

**Delta** reads the function-word distribution, standardised against how much
each word varies between authors. It is the measure the literature validates,
and it needs a lot of text before each word's rate settles.

**Texture** reads character n-grams of orders 3 to 5. A short passage contains
thousands of them where it contains a handful of any given function word, so
the estimate settles far sooner. Stamatatos (2009) reports this family as the
most robust on short and noisy text.

### Delta alone

| profile | 400w | 800w | 1,600w | 3,200w | 6,400w |
|---|---|---|---|---|---|
| 2,500 | 8% | 22% | 32% | 45% | 45% |
| 5,000 | 20% | 38% | 42% | 42% | 52% |
| 10,000 | 25% | 48% | 72% | 70% | 82% |
| 20,000 | 25% | 55% | 68% | 75% | 90% |
| 40,000 | 28% | 60% | 75% | 82% | 92% |

### Texture alone

| profile | 400w | 800w | 1,600w | 3,200w | 6,400w |
|---|---|---|---|---|---|
| 2,500 | 25% | 35% | 30% | 32% | 32% |
| 5,000 | 45% | 57% | 52% | 62% | 62% |
| 10,000 | 57% | 72% | 70% | 72% | 72% |
| 20,000 | 62% | 78% | 75% | 80% | 88% |
| 40,000 | 65% | 80% | 78% | 85% | 90% |

### The blend, which is what the tool uses

| profile | 400w | 800w | 1,600w | 3,200w | 6,400w |
|---|---|---|---|---|---|
| 2,500 | 25% | 35% | 30% | 30% | 32% |
| 5,000 | 45% | 57% | 52% | 62% | 62% |
| 10,000 | 57% | 72% | 68% | 72% | 82% |
| 20,000 | 62% | 78% | 75% | 80% | 92% |
| 40,000 | 65% | 80% | 78% | 85% | **95%** |

## What the tables say

**Texture does most of the work.** On a 400-word passage against a large
profile it reaches 65% where Delta manages 28%. Averaged across the whole grid
texture scores 62.4% and Delta 51.8%, and no weighting of the two beats texture
alone on average.

**Delta still earns its place.** It wins at the top of the range, 92% against
90%, and the blend reaches 95% there, higher than either alone. It also wins in
the corner where the profile is small but the passage is long.

**So Delta is held to a minority share.** Its weight rises from zero at 1,000
words of support to a ceiling of 0.4 at 8,000, with support taken as the
smaller of the draft and the profile. Those numbers were swept against this
grid rather than chosen. The blend sits below both arms in two cells, by two
points, which is inside the sampling error of forty trials.

**Both sizes matter, independently.** A large profile does not rescue a short
passage and a long passage does not rescue a small profile.

## The number to read

Raw distance is not comparable across lengths, because both arms shrink as
text grows. Measured across 24 authors, the median distance for a text by the
profile's own author:

| passage | same author | different author | overlap |
|---|---|---|---|
| 200w | 2.35 | 2.56 | 27% |
| 400w | 1.71 | 1.95 | 24% |
| 800w | 1.14 | 1.47 | 14% |
| 1,600w | 0.79 | 1.20 | 4% |
| 3,200w | 0.64 | 1.05 | 0% |
| 6,400w | 0.64 | 1.04 | 0% |

A fixed band of 1.5 would therefore have failed a person's own 200-word text
and passed a stranger's 6,400-word one, which is precisely backwards. The tool
reports **strangeness** instead: the share of other-author texts sitting at
least this close, read off this table at the draft's own length. Under 5% is
close, over 50% is off.

The overlap column is the honest measure of separability: how often a
different author lands at least as near as the median same-author text. It
reaches zero by 3,200 words and is 27% at 200, which is the real limit on
short-text identification.

## Measured on real correspondence

The fiction grid is a fair test but not a representative one. Against a real
corpus of business email, three authors, holding out one text at a time:

| arm | accuracy |
|---|---|
| Delta | 36% |
| texture | 91% |
| blended | 91% |

Chance is 33%. On short, formulaic, single-register prose, which is what most
working writing is, Delta is close to useless and texture is close to reliable.
This is the strongest argument for the second arm.

## What was changed because of it

Confidence tiers were originally 5,000 / 2,000 / 400 words, chosen by feel.
They moved twice: once when the first calibration showed them far too
generous, and again downward when the texture arm made small profiles usable.

| tier | words | measured |
|---|---|---|
| stable | 10,000+ | 57 to 95% |
| usable | 5,000 to 10,000 | 45 to 62% |
| thin | 1,500 to 5,000 | 25 to 35% |
| provisional | under 1,500 | near chance |

`check.py` carries `RELIABLE_WORDS = 500`. Below that a draft is judged on
texture alone and the report says so.

## The limits of the calibration

Fiction, mostly nineteenth century, all book length. Twenty-four candidate
authors is harder than the two-way question the tool usually faces, so the
percentages are pessimistic for that use even though the shape holds. The real
correspondence result above suggests the shape transfers but the balance
between the arms shifts.

## Reproducing

```bash
python scripts/build_baseline.py --gutenberg   # 24 authors, ~2.5M words
python scripts/calibrate.py                    # the arm tables
python scripts/calibrate_scale.py              # the length table
python scripts/discrimination.py               # against your own corpus
```
