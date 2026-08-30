# Contributing

## If you are an agent

Read this before you write anything.

The library has no third-party dependencies and it is going to stay that way.
The measurements are all countable over raw text, which is what makes the tool
runnable anywhere, and a dependency added for convenience costs more than it
saves. The one exception already made is the optional PDF reader, and it
degrades to a skipped file rather than an error.

**Do not add a feature because it sounds like it would individuate someone.**
The feature set is drawn from the stylometry literature, and each family in it
has replicated evidence behind it. `docs/research.md` records what is cited and
what is calibration. A new measurement needs either a citation or a test that
shows it separates two authors on real text.

**Do not present calibration as evidence.** Several constants in the code were
chosen by hand: the aggregate weighting, the verdict bands, the tolerance
curve, the materiality floors. They are listed in the README under a heading
that says so. If you add another, add it to that list. If you replace one with
a measured value, move it out.

**Do not claim a method the code does not implement.** An earlier version cited
Burrows's Delta while scaling each word by its own sampling noise, which is a
different measure with none of Delta's discriminating power. If you change how
a distance is computed, change what the docstring claims about it in the same
commit.

**Do not make the tool guess.** The acquisition ladder ends in a refusal on
purpose, and a connector with no consent prompt is treated as declined. If you
find a path where a profile could be synthesised, inferred from a name, or a
source read without an explicit yes, that is a bug worth fixing rather than a
gap worth closing.

**Do not report an accuracy without a held-out split.** An earlier version of
`scripts/discrimination.py` scored texts against profiles built from those same
texts and reported 4/4. Any test where a passage can appear in the profile it
is scored against is worthless.

## Tests

```bash
python -m unittest discover -s tests
```

Everything must pass before a change lands. The primitives in `test_text.py`
are heuristics and they rot silently, so they are tested first and hardest.
`test_regressions.py` holds one test per defect found in review; each of those
passed silently before its fix, which is why they are named individually.

Several tests exist to protect reasoning rather than behaviour. They assert
that raw type-token ratio collapses with length, that a rigid feature never
moves under blending, that a connector is never read without an explicit yes,
and that the shipped calibration converges well above chance. If you find
yourself changing one of those, you are changing the design.

## Calibration

Two data files are generated, not hand written:

```bash
python scripts/build_baseline.py --gutenberg   # between-author variation
python scripts/calibrate.py                    # what the tool can resolve
```

`baseline.json` is what makes Delta Delta. Without it the measure falls back to
a frequency-weighted distance and every `Distance` reports `calibrated=False`.

`calibration.json` sets the confidence tiers and the reliable-length threshold.
If you change a measurement, rerun it. Numbers in the docs must come from that
file rather than from an expectation of how it should behave.

## Comments

Under a tenth of the lines. One-line docstrings unless the contract is
genuinely unobvious, in which case say what is not recoverable from the code:
units, precedence, what happens on empty input. Rationale belongs in `docs/`.

No comment that restates the line beneath it.

## Skills

Written once in `skills/`, then generated into the per-harness directories.

```bash
python scripts/sync.py
python scripts/sync.py --check
```

Never edit `claude-plugin/`, `codex-plugin/` or `cursor-plugin/` by hand. The
sync will overwrite you.

## Style

No em dashes. British spelling in prose, en-GB throughout.

Names should say what the thing is. `dispersion` rather than `disp`, `windows`
rather than `chunks`. The code is read more often than it is written, and most
of the reading is done by someone trying to work out whether a number can be
trusted.
