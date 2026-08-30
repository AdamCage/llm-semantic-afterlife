"""Canonical serialisation and content hashing.

Content hashes are load-bearing here: they name cache entries, identify configs
inside ``run_id``, and form the integrity block of every manifest. They must
therefore be stable across processes, platforms and Python versions, which is
why serialisation goes through one canonical form rather than ``str(obj)``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_json(obj: Any) -> str:
    """Deterministic JSON: sorted keys, no insignificant whitespace, UTF-8 text.

    ``ensure_ascii=False`` keeps non-Latin text readable in cached payloads,
    which matters because seeds and generated trajectories are often not
    English.
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_obj(obj: Any) -> str:
    return sha256_text(canonical_json(obj))


def sha256_file(path: Path, *, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(chunk_size):
            digest.update(block)
    return digest.hexdigest()


def fingerprint_secret(secret: str | None, *, length: int = 12) -> str | None:
    """Short, non-reversible identifier for a credential.

    Lets a run be attributed to a specific key without the key ever touching
    disk. ``None`` in, ``None`` out, so callers need no special-casing.
    """
    if not secret:
        return None
    return f"sha256:{sha256_text(secret)[:length]}"


def hash_tree(root: Path, *, patterns: tuple[str, ...] = ("**/*",)) -> dict[str, str]:
    """Map of ``relative path -> sha256`` for every file under ``root``.

    Used as the integrity block of a run manifest so that later tampering or
    partial writes are detectable.
    """
    out: dict[str, str] = {}
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if path.is_file() and path.name != "manifest.json":
                out[path.relative_to(root).as_posix()] = sha256_file(path)
    return out
