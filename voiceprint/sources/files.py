"""A folder of writing, offered rather than demanded.

Set VOICEPRINT_SAMPLES to a directory and it becomes a source the ladder can
propose, which saves naming the same folder on every run.
"""
from __future__ import annotations

import os
from pathlib import Path

from ..corpus import Sample
from ..ingest import read_path


class FileConnector:
    name = "files"
    label = "A folder you have set aside"

    def __init__(self, root: str | None = None, register: str = "unknown"):
        self.root = Path(root or os.environ.get("VOICEPRINT_SAMPLES", "")
                         ).expanduser() if (root or os.environ.get(
                             "VOICEPRINT_SAMPLES")) else None
        self.register = register

    def available(self) -> bool:
        return bool(self.root and self.root.is_dir())

    def describe(self) -> str:
        n = len(list(self.root.rglob("*"))) if self.root else 0
        return (f"Read your writing from {self.root} "
                f"(about {n} files). Nothing leaves this machine.")

    def fetch(self, limit: int = 200) -> list[Sample]:
        if not self.available():
            return []
        out = []
        for s in read_path(self.root, register=self.register):
            out.append(s)
            if len(out) >= limit:
                break
        return out
