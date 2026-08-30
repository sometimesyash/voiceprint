"""Feature registry.

Every measurement declares its family, its kind, and its elasticity. Elasticity
is what the fidelity dial acts on: 0 means the feature is identity and context
may never move it, 1 means it is pure convention and context governs it
outright. See reference/blending.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from ..doc import Doc

Kind = Literal["scalar", "categorical", "vector"]

RIGID = 0.0
FIRM = 0.25
SUPPLE = 0.6
CONVENTION = 1.0


@dataclass(frozen=True)
class Feature:
    name: str
    family: str
    kind: Kind
    elasticity: float
    fn: Callable[[Doc], object]
    unit: str = ""
    doc: str = ""
    group: str = ""


_REGISTRY: dict[str, Feature] = {}


def feature(name: str, family: str, kind: Kind, elasticity: float,
            unit: str = "", doc: str = "", group: str = ""):
    """Register an extractor.

    `group` names a correlated cluster. Features sharing one measure the same
    underlying habit from different angles, so the distance counts the group
    once rather than once per feature.
    """
    def wrap(fn):
        if name in _REGISTRY:
            raise ValueError(f"duplicate feature {name!r}")
        _REGISTRY[name] = Feature(name, family, kind, elasticity, fn, unit,
                                  doc or (fn.__doc__ or "").strip(),
                                  group or name)
        return fn
    return wrap


def registry() -> dict[str, Feature]:
    return dict(_REGISTRY)


def group_of(name: str) -> str:
    f = _REGISTRY.get(name)
    return f.group if f else name


def groups() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for f in _REGISTRY.values():
        out.setdefault(f.group, []).append(f.name)
    return out


def by_family(family: str) -> list[Feature]:
    return [f for f in _REGISTRY.values() if f.family == family]


def families() -> list[str]:
    return sorted({f.family for f in _REGISTRY.values()})


def extract(doc: Doc, kinds: tuple[str, ...] = ("scalar",)) -> dict[str, object]:
    """Run every registered extractor of the given kinds over one Doc."""
    out: dict[str, object] = {}
    for f in _REGISTRY.values():
        if f.kind not in kinds:
            continue
        try:
            out[f.name] = f.fn(doc)
        except Exception:
            out[f.name] = None
    return out


from . import (  # noqa: E402,F401
    surface, structure, register, punctuation, numerals, richness, biber,
    lexical,
)
