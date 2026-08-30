"""A parsed unit of text, computed once and shared by every extractor."""
from __future__ import annotations

from functools import cached_property

from . import text as T


class Doc:
    """Lazily parsed text. Extractors read from here rather than re-tokenising."""

    __slots__ = ("raw", "__dict__")

    def __init__(self, raw: str):
        self.raw = str(raw)

    @cached_property
    def clean(self) -> str:
        return T.normalise(self.raw)

    @cached_property
    def lower(self) -> str:
        return self.clean.lower()

    @cached_property
    def tokens(self) -> list[str]:
        return T.tokens(self.raw)

    @cached_property
    def words(self) -> list[str]:
        return T.words(self.raw)

    @cached_property
    def sentences(self) -> list[str]:
        return T.sentences(self.raw)

    @cached_property
    def sentence_lengths(self) -> list[int]:
        return [len(T.words(s)) for s in self.sentences]

    @cached_property
    def n_words(self) -> int:
        return len(self.words)

    @cached_property
    def n_tokens(self) -> int:
        return len(self.tokens)

    def __len__(self) -> int:
        return self.n_words

    def __repr__(self) -> str:
        return f"Doc({self.n_words}w, {len(self.sentences)}s)"
