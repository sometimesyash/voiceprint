"""Connectors.

The core never reaches the network. A host that can read a mailbox or a chat
log supplies a connector, and the ladder in corpus.py asks the user before
touching any of them.
"""
from __future__ import annotations

from .files import FileConnector
from .jsonl import JsonlConnector

BUILTIN = [JsonlConnector, FileConnector]


def discover() -> list:
    """Connectors that need no host. Deliberately few."""
    return [c for c in (cls() for cls in BUILTIN) if c.available()]
