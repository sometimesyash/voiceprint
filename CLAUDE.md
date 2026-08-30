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

**Do not present calibration as evidence.** The sentence-length variation
thresholds were chosen by hand. They are not in any paper, they are labelled
that way in the docs, and anything else invented should be labelled the same.

**Do not make the tool guess.** The acquisition ladder ends in a refusal on
purpose. If you find a path where a profile could be synthesised, inferred
from a name, or filled in from a model's own priors, that is a bug worth
fixing rather than a gap worth closing.

## Tests

```bash
python -m unittest discover -s tests
```

Everything must pass before a change lands. The primitives in `test_text.py`
are heuristics and they rot silently, so they are tested first and hardest.

Three tests exist to protect reasoning rather than behaviour. They assert that
raw type-token ratio collapses with length, that a rigid feature never moves
under blending, and that a declined source is never read. If you find yourself
changing one of those, you are probably changing the design.

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
