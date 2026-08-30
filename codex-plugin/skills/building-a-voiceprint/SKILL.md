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

4. **Nothing.** Then say so plainly, and offer the prompts.

> I have nothing of your writing to measure, so I can't build a voiceprint.
> If you point me at a folder, or paste a few hundred words you wrote, I'll
> build it from that. Or I can ask you a few questions and use the answers.

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

**Enough of it.** More than you would expect, though less than it used to be.
Identity is measured two ways, and the character-texture arm holds up on
material where word frequencies are still noise, so a 5,000 word profile now
does what 10,000 used to.

| words | label | what it is worth |
|---|---|---|
| 10,000+ | stable | both measures hold |
| 5,000 to 10,000 | usable | enough to brief with confidence |
| 1,500 to 5,000 | thin | texture carries identity, directional only |
| under 1,500 | provisional | shape is real, distances are not |

Do not tell someone their profile is good when it says `provisional`. Say what
it can do, which is describe how they write, and what it cannot, which is
recognise them.

## When there is not enough

```bash
vp elicit yash
```

Returns prompts that draw natural prose, chosen to spread across registers
rather than pile up in one. Put them to the person and collect the answers as
new samples.

Two rules behind them, worth keeping if you write your own. Never ask someone
to describe how they write, because the description is aspirational and the
prose that follows is stilted. Ask about something they already have opinions
about, because argument produces natural rhythm where description produces
lists.

Always prefer writing that already exists. Elicited prose is self-conscious by
construction, so it is the fallback rather than the first move.

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
