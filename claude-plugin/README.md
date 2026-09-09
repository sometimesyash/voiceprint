# voiceprint (Claude Code plugin)

Measures how a person writes and holds generated prose to it, instead of
guessing at their style. This plugin exposes that as two skills plus an MCP
server, all backed by the `voiceprint` Python package.

## Prerequisite

```bash
pip install voiceprint
```

The MCP server checks for this itself: if `voiceprint` isn't importable, it
prints `voiceprint is not installed in this Python environment. Run: pip
install voiceprint` to stderr and exits, rather than failing on a bare
traceback.

## Skills

**`building-a-voiceprint`** — gathers a person's own prose (connected
sources, named files, or pasted text, in that order, never invented) and
measures it into a stored profile.

**`writing-in-your-voice`** — briefs a draft against a stored profile, then
checks the draft against those measurements before it's returned.

## What this is not

It doesn't ship or manage the `voiceprint` install itself — the MCP launcher
just tells you plainly when it's missing. For the full measurement
methodology, calibration tables, and library API, see the
[root README](../README.md).
