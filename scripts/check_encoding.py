"""Guard against mojibake and BOMs in tracked text files.

Editing UTF-8 files with tools that assume a legacy code page silently corrupts
non-ASCII characters — a corrupted axis label is visible, but a corrupted
docstring or seed text is not. This check runs in CI and in pre-commit.
"""

from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path

# Sequences that only appear when UTF-8 bytes have been decoded as a legacy
# single-byte code page and re-encoded as UTF-8.
MOJIBAKE_MARKERS = (
    "\u00c3\u00a9",  # e-acute via latin-1
    "\u00e2\u0080",  # en dash / quotes via latin-1
    "\u00d0",  # Cyrillic via latin-1
    "\u0432\u0402",  # en dash via cp1251
    "\u0432\u0453",
    "\ufffd",  # replacement character
)

TEXT_SUFFIXES = {".py", ".md", ".yaml", ".yml", ".toml", ".cfg", ".txt", ".mdc", ".json"}
SKIP_PARTS = {".venv", ".git", "runs", "cache", ".cache", "node_modules", "__pycache__"}


def iter_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if SKIP_PARTS & set(path.parts):
            continue
        out.append(path)
    return out


def check(path: Path, *, ascii_only_code: bool) -> list[str]:
    problems: list[str] = []
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        problems.append("has a UTF-8 BOM")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [*problems, f"is not valid UTF-8: {exc}"]

    for marker in MOJIBAKE_MARKERS:
        if marker in text:
            index = text.index(marker)
            snippet = text[max(0, index - 30) : index + 30].replace("\n", " ")
            names = " ".join(unicodedata.name(c, hex(ord(c))) for c in marker)
            problems.append(f"contains likely mojibake ({names}) near: {snippet!r}")
            break

    if ascii_only_code and path.suffix == ".py":
        offenders = sorted({c for c in text if ord(c) > 127})
        if offenders:
            listed = ", ".join(f"U+{ord(c):04X} {unicodedata.name(c, '?')}" for c in offenders[:8])
            problems.append(f"non-ASCII in Python source: {listed}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", type=Path)
    parser.add_argument(
        "--ascii-only-code",
        action="store_true",
        help="also require Python sources to be pure ASCII, so that figure labels and log "
        "messages cannot be corrupted by an editor with a legacy code page",
    )
    args = parser.parse_args()

    failures = 0
    for path in iter_files(args.root.resolve()):
        for problem in check(path, ascii_only_code=args.ascii_only_code):
            print(f"{path}: {problem}")
            failures += 1
    if failures:
        print(f"\n{failures} encoding problem(s) found.")
        return 1
    print("encoding check: clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
