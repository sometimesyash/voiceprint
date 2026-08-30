"""Copy the skills into each harness's plugin directory.

The skills are written once. Everything else is a layout difference between
harnesses, so it is generated rather than maintained by hand.

    python scripts/sync.py            write the plugin directories
    python scripts/sync.py --install  also install into the runtimes present
    python scripts/sync.py --check    fail if anything is stale
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import sys
from pathlib import Path


def _force_remove(path: Path) -> None:
    """Delete a tree, clearing the read-only bit OneDrive leaves behind.

    Copying out of a synced folder propagates ReadOnly onto the destination,
    and Windows then refuses to remove it, so a second sync fails on a machine
    where the first one worked.
    """
    def onerror(func, target, _exc):
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except Exception:
            pass

    if path.exists():
        shutil.rmtree(path, onerror=onerror)

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"

MCP = {
    "command": "python",
    "args": ["-m", "voiceprint.mcp"],
    "env": {},
}

HARNESSES = {
    "claude-plugin": {
        "manifest": ".claude-plugin/plugin.json",
        "body": lambda: {
            "name": "voiceprint",
            "version": version(),
            "description": DESCRIPTION,
            "author": {"name": "Yash Nairan"},
            "mcpServers": {"voiceprint": MCP},
        },
    },
    "codex-plugin": {
        "manifest": "plugin.json",
        "body": lambda: {
            "name": "voiceprint",
            "version": version(),
            "description": DESCRIPTION,
            "skills": [p.name for p in sorted(SKILLS.iterdir()) if p.is_dir()],
            "mcp": {"voiceprint": MCP},
        },
    },
    "cursor-plugin": {
        "manifest": "mcp.json",
        "body": lambda: {"mcpServers": {"voiceprint": MCP}},
    },
}

DESCRIPTION = ("Measure how a person writes and hold generated prose to it, "
               "instead of guessing at their style.")

RUNTIMES = {
    "Claude Code": Path.home() / ".claude" / "skills",
    "Copilot CLI": Path.home() / ".copilot" / "skills",
    "Scout (bundled)": Path.home() / ".scout" / "skills",
    "Scout (local)": Path.home() / ".scout" / "m-skills",
    "Cowork": Path.home() / ".cowork" / "skills",
}


def version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf8")
    for line in text.splitlines():
        if line.startswith("version"):
            return line.split("=")[1].strip().strip('"')
    return "0.0.0"


def skill_names() -> list[str]:
    return [p.name for p in sorted(SKILLS.iterdir())
            if p.is_dir() and (p / "SKILL.md").is_file()]


def sync_harness(name: str, spec: dict, check: bool) -> bool:
    target = ROOT / name
    dest = target / "skills"
    changed = False

    if not check:
        _force_remove(dest)
        shutil.copytree(SKILLS, dest)
        changed = True

    manifest = target / spec["manifest"]
    body = json.dumps(spec["body"](), indent=2) + "\n"
    if check:
        if not manifest.is_file() or manifest.read_text(encoding="utf8") != body:
            return True
        return False
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(body, encoding="utf8")
    return changed


def install() -> None:
    for label, root in RUNTIMES.items():
        if not root.exists():
            print(f"  skipped   {label:18s} {root} (absent)")
            continue
        for name in skill_names():
            dest = root / name
            _force_remove(dest)
            shutil.copytree(SKILLS / name, dest, dirs_exist_ok=True)
        print(f"  installed {label:18s} {root}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--install", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    names = skill_names()
    if not names:
        print("No skills found.", file=sys.stderr)
        return 1
    print(f"skills: {', '.join(names)}")

    stale = False
    for name, spec in HARNESSES.items():
        changed = sync_harness(name, spec, args.check)
        stale = stale or (args.check and changed)
        if not args.check:
            print(f"  wrote     {name}")

    if args.check:
        print("stale, run scripts/sync.py" if stale else "up to date")
        return 1 if stale else 0

    if args.install:
        install()
    return 0


if __name__ == "__main__":
    sys.exit(main())
