"""Reverse legacy-code-page mojibake in UTF-8 text files.

When a UTF-8 file is read as cp1251/cp1252 and written back as UTF-8, each
original multi-byte sequence becomes two or three single-byte characters. The
transformation is byte-reversible: map each character back to the byte it came
from, then decode the result as UTF-8.

Run with ``--check`` first; ``--write`` only when the preview looks right.
"""

from __future__ import annotations

import argparse
import codecs
import sys
from pathlib import Path

# Tried in order. Both are single-byte, so a character that round-trips through
# either one identifies its original byte unambiguously enough for repair.
CANDIDATE_CODECS = ("cp1251", "cp1252")


def to_original_bytes(text: str) -> bytes | None:
    out = bytearray()
    for char in text:
        code = ord(char)
        if code < 0x80:
            out.append(code)
            continue
        for codec in CANDIDATE_CODECS:
            try:
                encoded = char.encode(codec)
            except UnicodeEncodeError:
                continue
            if len(encoded) == 1:
                out.extend(encoded)
                break
        else:
            return None
    return bytes(out)


def repair(text: str) -> str | None:
    raw = to_original_bytes(text)
    if raw is None:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--write", action="store_true", help="apply the repair in place")
    args = parser.parse_args()

    failures = 0
    for path in args.paths:
        raw = path.read_bytes()
        had_bom = raw.startswith(codecs.BOM_UTF8)
        text = raw.decode("utf-8-sig")
        fixed = repair(text)
        if fixed is None:
            print(f"{path}: could not reverse cleanly; leave it alone and fix by hand")
            failures += 1
            continue
        changed = [
            (before, after)
            for before, after in zip(text.splitlines(), fixed.splitlines(), strict=False)
            if before != after
        ]
        print(f"{path}: bom={had_bom} lines_changed={len(changed)}")
        for before, after in changed[:6]:
            print(f"  - {before.strip()[:110]}")
            print(f"  + {after.strip()[:110]}")
        if args.write:
            # No BOM: a BOM in a Python source file is what let this happen in
            # the first place, and nothing here needs one.
            path.write_bytes(fixed.encode("utf-8"))
            print(f"  written without BOM ({len(fixed.encode('utf-8'))} bytes)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
