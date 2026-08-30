"""Reading text out of files.

Plain formats are handled with the standard library. Anything needing a third
party package degrades to a note rather than an exception, because a missing
optional dependency should cost you one file, not the run.
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Iterator
from xml.etree import ElementTree as ET

from ..corpus import Sample

TEXT_SUFFIXES = {".txt", ".md", ".markdown", ".rst", ".org"}
SUFFIXES = TEXT_SUFFIXES | {".docx", ".pptx", ".pdf", ".eml", ".html", ".htm"}

# Document furniture: headings, code, links, filenames. Counting it drags every
# statistic toward the telegraphic and profiles the format instead of the person.
# Blank lines are never dropped; they carry the paragraph structure.
SKIP_LINE = re.compile(
    r"^(?:#{1,6}\s|\||```|\s*[-*+]\s*$|https?://|\d+\s*$"
    r"|[A-Za-z0-9 _.-]{0,40}\.(?:py|js|ts|json|md|txt|pptx|docx|xlsx|csv)\s*$)")


def strip_markup(t: str) -> str:
    t = re.sub(r"`{1,3}[^`]*`{1,3}", " ", t)
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
    t = re.sub(r"^\s{0,3}>\s?", "", t, flags=re.M)
    t = re.sub(r"[*_#]{1,3}", "", t)
    return t


def _text(path: Path) -> str:
    raw = strip_markup(path.read_text(encoding="utf8", errors="ignore"))
    kept = [l for l in raw.splitlines() if not SKIP_LINE.match(l.strip())]
    return "\n".join(kept)


def _docx(path: Path) -> str:
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    paras = ["".join(n.text or "" for n in p.iter(f"{W}t"))
             for p in root.iter(f"{W}p")]
    return "\n\n".join(p.strip() for p in paras if p.strip())


def _pptx(path: Path) -> str:
    A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    out: list[str] = []
    with zipfile.ZipFile(path) as z:
        names = sorted(n for n in z.namelist()
                       if re.match(r"ppt/(slides|notesSlides)/[^/]+\.xml$", n))
        for n in names:
            try:
                root = ET.fromstring(z.read(n))
            except ET.ParseError:
                continue
            for p in root.iter(f"{A}p"):
                line = "".join(t.text or "" for t in p.iter(f"{A}t")).strip()
                if line:
                    out.append(line)
    return "\n".join(out)


def _eml(path: Path) -> str:
    import email
    from email import policy
    msg = email.message_from_bytes(path.read_bytes(), policy=policy.default)
    body = msg.get_body(preferencelist=("plain", "html"))
    if body is None:
        return ""
    text = body.get_content()
    return quoted_reply_removed(text)


def _html(path: Path) -> str:
    from html.parser import HTMLParser

    class Strip(HTMLParser):
        def __init__(self):
            super().__init__()
            self.parts: list[str] = []
            self.skip = False

        def handle_starttag(self, tag, attrs):
            if tag in ("script", "style"):
                self.skip = True

        def handle_endtag(self, tag):
            if tag in ("script", "style"):
                self.skip = False
            if tag in ("p", "div", "br", "li", "h1", "h2", "h3"):
                self.parts.append("\n")

        def handle_data(self, data):
            if not self.skip:
                self.parts.append(data)

    s = Strip()
    s.feed(path.read_text(encoding="utf8", errors="ignore"))
    return "".join(s.parts)


def _pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    return "\n\n".join((pg.extract_text() or "") for pg in PdfReader(str(path)).pages)


READERS = {".docx": _docx, ".pptx": _pptx, ".eml": _eml, ".html": _html,
           ".htm": _html, ".pdf": _pdf}


def quoted_reply_removed(text: str) -> str:
    """Drop quoted history and signatures from a message.

    What someone quotes was written by someone else, and a signature block is
    boilerplate. Both would otherwise be measured as theirs.
    """
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(">"):
            continue
        if re.match(r"^-{2,}\s*$|^_{2,}\s*$", s):
            break
        if re.match(r"^(On .{5,80}wrote:|From:|Sent:|To:|Subject:)", s):
            break
        if re.match(r"^(Sent from my |Get Outlook for )", s):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def read_file(path: Path, register: str = "unknown") -> str:
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return _text(path)
    reader = READERS.get(suffix)
    return reader(path) if reader else ""


def read_path(target: str | Path, register: str = "unknown") -> Iterator[Sample]:
    """Yield one sample per readable file, walking directories."""
    p = Path(target).expanduser()
    if not p.exists():
        raise FileNotFoundError(f"{p} does not exist")
    files = (sorted(f for f in p.rglob("*") if f.suffix.lower() in SUFFIXES)
             if p.is_dir() else [p])
    for f in files:
        try:
            body = read_file(f, register)
        except Exception:
            continue
        if body.strip():
            yield Sample(body, origin=str(f), register=register)
