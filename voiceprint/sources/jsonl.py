"""A JSONL export of your own messages.

Most tools that can export a mailbox or a chat history will emit JSON lines.
Point VOICEPRINT_JSONL at one and the ladder can offer it. Records are only
read if they look like something you wrote, so an export containing a whole
thread contributes your half of it and discards the rest.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from ..corpus import Sample
from ..ingest import quoted_reply_removed

TEXT_KEYS = ("text", "body", "content", "message", "bodyPreview")
AUTHOR_KEYS = ("from", "sender", "author", "user", "role", "direction")
DATE_KEYS = ("date", "sent", "sentDateTime", "createdDateTime", "timestamp")
SELF = {"me", "self", "user", "sent", "outgoing", "assistant:false"}


def _first(record: dict, keys: tuple[str, ...]) -> str | None:
    for k in keys:
        v = record.get(k)
        if isinstance(v, str) and v.strip():
            return v
        if isinstance(v, dict):
            for nested in ("address", "name", "displayName", "emailAddress"):
                got = v.get(nested)
                if isinstance(got, str) and got.strip():
                    return got
                if isinstance(got, dict) and isinstance(got.get("address"), str):
                    return got["address"]
    return None


class JsonlConnector:
    name = "jsonl"
    label = "An export of your messages"

    def __init__(self, path: str | None = None, me: str | None = None,
                 register: str = "email"):
        raw = path or os.environ.get("VOICEPRINT_JSONL", "")
        self.path = Path(raw).expanduser() if raw else None
        self.me = (me or os.environ.get("VOICEPRINT_ME", "")).lower() or None
        self.register = register

    def available(self) -> bool:
        return bool(self.path and self.path.is_file())

    def describe(self) -> str:
        who = f" written by {self.me}" if self.me else ""
        return (f"Read messages{who} from {self.path}. Quoted replies and "
                f"signatures are dropped. Nothing leaves this machine.")

    def _mine(self, record: dict) -> bool:
        if not self.me:
            return True
        author = (_first(record, AUTHOR_KEYS) or "").lower()
        return self.me in author or author in SELF

    def fetch(self, limit: int = 200) -> list[Sample]:
        if not self.available():
            return []
        out: list[Sample] = []
        with self.path.open(encoding="utf8", errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if not line or len(out) >= limit:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(record, dict) or not self._mine(record):
                    continue
                body = _first(record, TEXT_KEYS)
                if not body:
                    continue
                body = quoted_reply_removed(body)
                if body:
                    out.append(Sample(body, origin=f"{self.path.name}",
                                      register=self.register,
                                      written_at=_first(record, DATE_KEYS)))
        return out
