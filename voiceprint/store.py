"""Where a voiceprint lives.

The profile is a markdown file. A person should be able to open it, read what
was measured about them, disagree with it, and delete it. Everything a reader
needs is in the prose; the machine-readable block is fenced at the end so the
document stays legible.

Nothing writes over an existing profile without being told to, and nothing
downstream runs without one.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .profile import Voiceprint
from .render import to_markdown

FENCE = "```json voiceprint"
FENCE_RE = re.compile(r"```json voiceprint\s*\n(.*?)\n```", re.S)


class ProfileMissing(FileNotFoundError):
    """No profile exists for this name."""


class ProfileExists(FileExistsError):
    """A profile already exists and overwrite was not requested."""


def home() -> Path:
    """VOICEPRINT_HOME, else the platform data directory.

    Deliberately not inside any one agent runtime's folder, so the same
    profile serves whichever tool is asking.
    """
    env = os.environ.get("VOICEPRINT_HOME")
    if env:
        return Path(env).expanduser()
    if os.name == "nt":
        base = os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming")
        return Path(base) / "voiceprint"
    xdg = os.environ.get("XDG_DATA_HOME")
    return Path(xdg).expanduser() / "voiceprint" if xdg else \
        Path.home() / ".local" / "share" / "voiceprint"


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", str(name).strip().lower()).strip("-")
    return s or "default"


def path_for(name: str) -> Path:
    return home() / f"{slug(name)}.md"


def exists(name: str) -> bool:
    return path_for(name).is_file()


def require(name: str) -> Path:
    """The path, or a refusal that says what to do about it."""
    p = path_for(name)
    if not p.is_file():
        known = ", ".join(n for n, _ in listing()) or "none"
        raise ProfileMissing(
            f"No voiceprint for {name!r} at {p}. Existing profiles: {known}. "
            f"Build one with `vp build` before anything reads from it; it "
            f"will not be guessed.")
    return p


def save(vp: Voiceprint, overwrite: bool = False) -> Path:
    p = path_for(vp.name)
    if p.exists() and not overwrite:
        raise ProfileExists(
            f"{p} already exists. Pass overwrite to replace it, or choose "
            f"another name.")
    p.parent.mkdir(parents=True, exist_ok=True)
    body = to_markdown(vp)
    payload = json.dumps(vp.as_dict(), separators=(",", ":"), sort_keys=True)
    p.write_text(f"{body}\n\n{FENCE}\n{payload}\n```\n", encoding="utf8")
    return p


def load(name: str) -> Voiceprint:
    p = require(name)
    text = p.read_text(encoding="utf8")
    m = FENCE_RE.search(text)
    if not m:
        raise ValueError(
            f"{p} has no voiceprint data block. The prose is readable but the "
            f"measurements are gone; rebuild it.")
    return Voiceprint.from_dict(json.loads(m.group(1)))


def listing() -> list[tuple[str, Path]]:
    root = home()
    if not root.is_dir():
        return []
    return sorted((p.stem, p) for p in root.glob("*.md"))


def delete(name: str) -> bool:
    p = path_for(name)
    if p.is_file():
        p.unlink()
        return True
    return False
