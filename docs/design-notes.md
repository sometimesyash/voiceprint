# Design notes

Why the repo is built the way it is. Written for whoever picks this up later,
including me, and for agents working in the tree.

## Constraints that are not negotiable

**No third-party dependencies.** Every measurement is countable over raw text,
which is what makes the tool runnable anywhere without a install step that can
fail. The single exception is the optional PDF reader, and a missing `pypdf`
skips one file rather than breaking the run.

**The feature set is evidence-led.** Each family traces to replicated work in
the stylometry literature, recorded in `research.md` with verification status
per source. A new measurement needs either a citation or a test showing it
separates two authors on real text. Adding one because it sounds like it would
individuate someone is how the feature set rots.

**Uncalibrated constants stay labelled.** The aggregate weighting, the verdict
bands, the tolerance curve and the materiality floors were all chosen by hand.
They are listed in the README under a heading that says so. Add one, add it to
that list; replace one with a measured value, move it out.

**The docstring must match the arithmetic.** An early version cited Burrows's
Delta while scaling each word by its own sampling noise, which is a different
measure with none of Delta's power. The citation made it look principled for
weeks. If the computation changes, the claim changes in the same commit.

**The tool never guesses.** The acquisition ladder ends in `NoCorpus`, and a
connector with no consent prompt is treated as declined. Any path where a
profile could be synthesised, inferred from a name, or a source read without
an explicit yes is a bug, not a gap.

**No accuracy figure without a held-out split.** An early `discrimination.py`
scored texts against profiles built from those same texts and reported 4 out of
4. Any evaluation where a passage can appear in the profile it is scored
against is worthless, and worse than worthless because it reads as evidence.

## Generated, not written

```bash
python scripts/build_baseline.py --gutenberg   # between-author variation
python scripts/calibrate.py                    # what the tool can resolve
python scripts/sync.py                         # per-harness skill copies
```

`baseline.json` is what makes Delta Delta. Without it the measure degrades to a
frequency-weighted distance and every `Distance` reports `calibrated=False`.

`calibration.json` sets the confidence tiers, the reliable-length threshold and
the two-arm weighting curve. Change a measurement and it needs rerunning;
numbers in the docs come from that file rather than from an expectation of how
it ought to behave.

`skills/` is the source. Never hand-edit `claude-plugin/`, `codex-plugin/` or
`cursor-plugin/`, because the sync overwrites them.

## Tests

```bash
python -m unittest discover -s tests
```

The primitives in `test_text.py` are heuristics and rot silently, so they are
tested hardest. `test_regressions.py` holds one test per defect found in
review, each of which passed silently before its fix.

Several tests protect reasoning rather than behaviour: that raw type-token
ratio collapses with length, that a rigid feature never moves under blending,
that a connector is never read without an explicit yes, that the shipped
calibration converges well above chance. Changing one of those means changing
the design.

## Style

Comments under a tenth of the lines. One-line docstrings unless the contract is
genuinely unobvious, in which case state what is not recoverable from the code:
units, precedence, behaviour on empty input. Rationale lives in `docs/`.

No comment that restates the line beneath it.

No em dashes. British spelling throughout.

Names should say what the thing is. `dispersion` rather than `disp`, `windows`
rather than `chunks`. Most of the reading is done by someone trying to work out
whether a number can be trusted.
