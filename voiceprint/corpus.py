"""Corpus assembly and the acquisition ladder.

Nothing here reaches the network. Hosts that can read a mailbox or a chat log
register a connector; the core only ever sees text that has already been
handed to it, and only after the user has agreed to that particular source.

The ladder is ordered and it terminates. If no source yields usable text the
result is NoCorpus, never an invented profile.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Iterable, Protocol

from . import text as T

MIN_SAMPLE_WORDS = 25


class NoCorpus(Exception):
    """No writing was available and none may be invented."""


class ConsentDenied(Exception):
    """The user declined a source."""


@dataclass
class Sample:
    text: str
    origin: str
    register: str = "unknown"
    written_at: str | None = None
    sha256: str = ""
    words: int = 0

    def __post_init__(self):
        self.text = self.text.strip()
        self.words = len(T.words(self.text))
        self.sha256 = hashlib.sha256(self.text.encode("utf8")).hexdigest()[:16]

    @property
    def usable(self) -> bool:
        return self.words >= MIN_SAMPLE_WORDS


@dataclass
class Corpus:
    """Samples plus the record of where each one came from."""
    samples: list[Sample] = field(default_factory=list)
    collected_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))

    def add(self, sample: Sample) -> bool:
        if not sample.usable:
            return False
        if any(s.sha256 == sample.sha256 for s in self.samples):
            return False
        self.samples.append(sample)
        return True

    def extend(self, samples: Iterable[Sample]) -> int:
        return sum(1 for s in samples if self.add(s))

    @property
    def words(self) -> int:
        return sum(s.words for s in self.samples)

    @property
    def texts(self) -> list[str]:
        return [s.text for s in self.samples]

    def by_register(self) -> dict[str, list[Sample]]:
        out: dict[str, list[Sample]] = {}
        for s in self.samples:
            out.setdefault(s.register, []).append(s)
        return out

    def registers(self) -> list[str]:
        return sorted(self.by_register())

    def filter(self, register: str) -> "Corpus":
        c = Corpus(collected_at=self.collected_at)
        c.samples = [s for s in self.samples if s.register == register]
        return c

    def manifest(self) -> list[dict]:
        return [{"origin": s.origin, "register": s.register, "words": s.words,
                 "sha256": s.sha256, "written_at": s.written_at}
                for s in self.samples]

    def __len__(self) -> int:
        return len(self.samples)


class Connector(Protocol):
    """A host-supplied reader for one kind of material."""

    name: str
    label: str

    def available(self) -> bool: ...

    def describe(self) -> str: ...

    def fetch(self, limit: int) -> list[Sample]: ...


@dataclass
class Ladder:
    """Try connectors, then named files, then pasted text. Then stop.

    `ask` is the host's consent prompt. It receives a plain description of what
    would be read and returns True only on an explicit yes. A connector that is
    available is still never read without one.
    """
    connectors: list[Connector] = field(default_factory=list)
    ask: Callable[[str], bool] | None = None
    limit: int = 200

    def gather(self, files: list[str] | None = None,
               pasted: str | None = None,
               register: str = "unknown") -> tuple[Corpus, list[str]]:
        corpus = Corpus()
        log: list[str] = []

        for c in self.connectors:
            try:
                if not c.available():
                    log.append(f"{c.name}: not connected")
                    continue
            except Exception as e:
                log.append(f"{c.name}: unavailable ({e})")
                continue

            if self.ask and not self.ask(c.describe()):
                log.append(f"{c.name}: declined")
                continue

            try:
                got = c.fetch(self.limit)
            except Exception as e:
                log.append(f"{c.name}: failed ({e})")
                continue
            added = corpus.extend(got)
            log.append(f"{c.name}: {added} samples, {sum(s.words for s in got)} words")

        if files:
            from .ingest import read_path
            for path in files:
                try:
                    got = list(read_path(path, register=register))
                except Exception as e:
                    log.append(f"{path}: failed ({e})")
                    continue
                added = corpus.extend(got)
                log.append(f"{path}: {added} samples")

        if pasted and pasted.strip():
            s = Sample(pasted, origin="pasted", register=register)
            if corpus.add(s):
                log.append(f"pasted: {s.words} words")
            else:
                log.append(f"pasted: too short (under {MIN_SAMPLE_WORDS} words)")

        if not corpus.samples:
            raise NoCorpus(
                "No writing was available. Connected sources returned nothing "
                "or were declined, no readable files were given, and no text "
                "was pasted. A voiceprint cannot be inferred without a sample; "
                "supply some of your own writing and run it again.")
        return corpus, log
