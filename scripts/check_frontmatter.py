"""Check that every SKILL.md carries parseable frontmatter.

Skill loaders read the frontmatter before anything else, so a malformed block
means the skill is silently ignored rather than loudly broken.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ("name", "description")
FRONT = re.compile(r"\A---\n(.*?)\n---\n", re.S)


def parse(block: str) -> dict:
    try:
        import yaml
        return yaml.safe_load(block) or {}
    except ImportError:
        out = {}
        for line in block.splitlines():
            if ":" in line and not line.startswith((" ", "\t", "-")):
                key, _, value = line.partition(":")
                out[key.strip()] = value.strip().strip("'\"")
        return out


def main() -> int:
    problems = 0
    for path in sorted(ROOT.rglob("SKILL.md")):
        if ".git" in path.parts:
            continue
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf8")
        match = FRONT.match(text)
        if not match:
            print(f"FAIL {rel}: no frontmatter block")
            problems += 1
            continue
        try:
            data = parse(match.group(1))
        except Exception as e:
            print(f"FAIL {rel}: {type(e).__name__}: {str(e)[:150]}")
            problems += 1
            continue
        missing = [k for k in REQUIRED if not data.get(k)]
        if missing:
            print(f"FAIL {rel}: missing {', '.join(missing)}")
            problems += 1
            continue
        if data["name"] != path.parent.name:
            print(f"FAIL {rel}: name {data['name']!r} does not match folder")
            problems += 1
            continue
        print(f"ok   {rel}  ({len(data['description'])} char description)")

    for path in sorted(ROOT.rglob("*.md")):
        if ".git" in path.parts or path.name == "SKILL.md":
            continue
        first = path.read_text(encoding="utf8").splitlines()[:1]
        if first and first[0].strip() == "---":
            print(f"FAIL {path.relative_to(ROOT)}: opens with --- and will be "
                  f"read as frontmatter")
            problems += 1

    print(f"\n{problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
