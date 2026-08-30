"""MCP server over stdio.

One implementation reaches every client that speaks MCP, which is how the
tool stays honest about being cross-platform: Claude, Codex, Cursor and the
rest get the same behaviour rather than four drifting copies.

    python -m voiceprint.mcp

Tools that read a profile check it exists and return a plain refusal if it
does not. None of them will invent one.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import context, store
from .blend import DEFAULT_FIDELITY, blend
from .check import against_rules
from .corpus import Corpus, NoCorpus, Sample
from .distance import measure
from .profile import CONFIDENCE_NOTE, build
from .render import brief_markdown

PROTOCOL = "2024-11-05"

TOOLS = [
    {
        "name": "voiceprint_build",
        "description": (
            "Measure how someone writes and store the profile as markdown. "
            "Give it files, folders, or text the user has supplied. It will "
            "not invent a profile: if nothing readable is provided it says so."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "who this profile is for"},
                "paths": {"type": "array", "items": {"type": "string"},
                          "description": "files or folders of their own writing"},
                "text": {"type": "string", "description": "prose pasted directly"},
                "register": {"type": "string",
                             "description": "email, chat, memo, report, deck, essay, note, docs"},
                "overwrite": {"type": "boolean"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "voiceprint_brief",
        "description": (
            "Get writing instructions for a stored profile, tuned to the task. "
            "Call this BEFORE drafting anything in someone's voice. Returns "
            "measured targets, the phrases they reuse, and real examples."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "task": {"type": "string",
                         "description": "what is being written, in plain words"},
                "fidelity": {"type": "number",
                             "description": "0.5 to 1.0, default 0.8. Higher holds "
                                            "closer to their own voice."},
            },
            "required": ["name"],
        },
    },
    {
        "name": "voiceprint_check",
        "description": (
            "Hold a draft against a profile. Returns a voice distance and the "
            "measures that sit furthest out, with what to do about each. Call "
            "this after drafting and rewrite until it passes."),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "draft": {"type": "string"},
                "task": {"type": "string"},
                "fidelity": {"type": "number"},
            },
            "required": ["name", "draft"],
        },
    },
    {
        "name": "voiceprint_list",
        "description": "Which profiles exist on this machine.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "voiceprint_show",
        "description": "Read a stored profile back as prose.",
        "inputSchema": {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    },
]


def _text(body: str, error: bool = False) -> dict:
    return {"content": [{"type": "text", "text": body}], "isError": error}


def _build(args: dict) -> dict:
    name = args["name"]
    corpus = Corpus()
    log = []

    for raw in args.get("paths") or []:
        try:
            from .ingest import read_path
            added = corpus.extend(read_path(raw, register=args.get("register", "unknown")))
            log.append(f"{raw}: {added} samples")
        except Exception as e:
            log.append(f"{raw}: {e}")

    if args.get("text"):
        s = Sample(args["text"], origin="supplied",
                   register=args.get("register", "unknown"))
        log.append(f"supplied text: {s.words} words"
                   if corpus.add(s) else "supplied text: too short")

    if not corpus.samples:
        return _text(
            "No writing was available, so no profile was built. Ask the user "
            "for files or paste some of their own prose. A voiceprint cannot "
            "be guessed from a name.\n\n" + "\n".join(log), error=True)

    vp = build(corpus, name)
    try:
        path = store.save(vp, overwrite=bool(args.get("overwrite")))
    except store.ProfileExists as e:
        return _text(str(e), error=True)

    return _text(
        f"Built {name} from {vp.words:,} words across {len(corpus)} samples. "
        f"Confidence {vp.pooled.confidence}. "
        f"{CONFIDENCE_NOTE[vp.pooled.confidence]}\n\nStored at {path}\n\n"
        + "\n".join(log))


def _brief(args: dict) -> dict:
    vp = store.load(args["name"])
    ctx = context.infer(args.get("task", ""),
                        float(args.get("fidelity", DEFAULT_FIDELITY)))
    profile = vp.profile_for(ctx.register)
    if profile is None:
        return _text(f"{args['name']} has no usable profile.", error=True)
    rules = blend(profile, None, ctx.fidelity)
    return _text(f"{ctx.reason}.\n\n" + brief_markdown(rules, vp.name))


def _check(args: dict) -> dict:
    vp = store.load(args["name"])
    ctx = context.infer(args.get("task", ""),
                        float(args.get("fidelity", DEFAULT_FIDELITY)))
    profile = vp.profile_for(ctx.register)
    if profile is None:
        return _text(f"{args['name']} has no usable profile.", error=True)
    rules = blend(profile, None, ctx.fidelity)
    report = against_rules(args["draft"], rules, profile)
    return _text(report.to_markdown())


def _list(_: dict) -> dict:
    found = store.listing()
    if not found:
        return _text(f"No profiles yet. Build one with voiceprint_build. "
                     f"They live in {store.home()}.")
    return _text("\n".join(f"{n}  {p}" for n, p in found))


def _show(args: dict) -> dict:
    path = store.require(args["name"])
    body = path.read_text(encoding="utf8").split("```json voiceprint")[0]
    return _text(body.rstrip())


HANDLERS = {
    "voiceprint_build": _build,
    "voiceprint_brief": _brief,
    "voiceprint_check": _check,
    "voiceprint_list": _list,
    "voiceprint_show": _show,
}


def handle(request: dict) -> dict | None:
    method = request.get("method")
    rid = request.get("id")

    if method == "initialize":
        result = {"protocolVersion": PROTOCOL,
                  "capabilities": {"tools": {}},
                  "serverInfo": {"name": "voiceprint", "version": "0.1.0"}}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        params = request.get("params") or {}
        fn = HANDLERS.get(params.get("name"))
        if fn is None:
            result = _text(f"Unknown tool {params.get('name')!r}", error=True)
        else:
            try:
                result = fn(params.get("arguments") or {})
            except store.ProfileMissing as e:
                result = _text(str(e), error=True)
            except NoCorpus as e:
                result = _text(str(e), error=True)
            except Exception as e:
                result = _text(f"{type(e).__name__}: {e}", error=True)
    elif method in ("notifications/initialized", "notifications/cancelled"):
        return None
    elif method == "ping":
        result = {}
    else:
        return {"jsonrpc": "2.0", "id": rid,
                "error": {"code": -32601, "message": f"unknown method {method}"}}

    return {"jsonrpc": "2.0", "id": rid, "result": result}


def serve(stdin=sys.stdin, stdout=sys.stdout) -> None:
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle(request)
        if response is not None:
            stdout.write(json.dumps(response) + "\n")
            stdout.flush()


if __name__ == "__main__":
    serve()
