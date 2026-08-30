---
name: building-a-voiceprint
description: Use when someone wants their writing style captured, or when writing-in-your-voice reports no profile exists. Gathers a person's own prose from connected sources, files they name, or text they paste, then measures it into a stored markdown profile. Triggers on "learn how I write", "build my voiceprint", "capture my style", "profile my writing", or a missing profile blocking another task.
---

# Building a voiceprint

A voiceprint is measured from writing the person actually produced. It is
never inferred, never generated, and never guessed from what you know about
them. If there is no writing, there is no profile, and the honest answer is to
say so.

## Ask in this order

**1. Connected sources.** If the host can reach their mail, chat or documents,
offer it and say exactly what would be read.

> I can build this from your sent mail, which stays on this machine and is not
> uploaded anywhere. Shall I?

Never read a source they did not agree to. A decline is not a hurdle to route
around; it moves you to step two.

**2. Files they name.** Old documents, notes, posts, decks. Ask for a folder.

**3. Text they paste.** Anything of their own, several hundred words at least.

**4. Nothing.** Then say so plainly and stop.

> I have nothing of your writing to measure, so I can't build a voiceprint.
> If you point me at a folder, or paste a few hundred words you wrote, I'll
> build it from that.

Do not offer to approximate. An invented profile is worse than none, because
everything downstream then trusts it.

## Running it

```bash
vp build yash ~/Documents/writing --register essay
vp build yash --text "$(cat notes.md)" --register note
```

Or let it offer whatever sources are configured:

```bash
vp build yash
```

## What makes a good corpus

**Their own prose, continuous.** Paragraphs, not bullet lists. Long emails,
memos, posts, notes, speaker notes from old decks. Speaker notes are unusually
good, because they were written to be spoken and never designed.

**One register at a time where possible.** Genre moves writing at least as
much as identity does, so mixing emails with formal reports measures the
mixture. Tag each batch with `--register` and the tool keeps them apart.

**Not anything a model wrote.** A profile taken from generated text teaches
everything downstream to sound generated. If they hand you something a model
drafted, say so and ask for something they typed.

**Enough of it.** More than you would expect. Measured against 24 authors, a
5,000 word profile identifies the right person about 40% of the time on long
passages; 20,000 words reaches about 90%. The tool builds below that and
labels the result, but a thin profile briefs a model usefully while proving
nothing about identity.

| words | label | what it is worth |
|---|---|---|
| 20,000+ | stable | the function-word measures hold |
| 10,000 to 20,000 | usable | good on long passages, weaker on short |
| 2,500 to 10,000 | thin | rhythm and punctuation only |
| under 2,500 | provisional | structure is real, distances are not |

Do not tell someone their profile is good when it says `provisional`. Say what
it can do, which is describe how they write, and what it cannot, which is
recognise them.

## Where it goes

A markdown file, one per person, under `VOICEPRINT_HOME` or the platform data
directory. Readable, editable, deletable. Show them where it landed and tell
them they can read it.

```bash
vp show yash
vp remove yash
```

The prose at the top is for them. The fenced block at the bottom is how the
tool reads it back.

## Adding to a profile later

`vp build` refuses to overwrite silently. Pass `--force` when they have more
writing and want it rebuilt, and say that the old one is being replaced.

## Checking it worked

```bash
vp diff yash something-they-wrote.md
python scripts/discrimination.py --corpus DIR
```

Run the first against a piece of their writing that was not in the corpus.
Run the second if you have several people's writing: it holds each text out
and asks which profile it lands nearest, which is the only honest test of
whether the profile identifies anyone.

If discrimination sits near chance, the corpus is too small or too mixed. That
is information, not failure, and it should be reported rather than hidden.
