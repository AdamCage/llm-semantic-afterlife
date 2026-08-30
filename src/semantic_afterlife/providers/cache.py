"""Content-addressed response cache.

The cache is what makes level-L3 reproducibility possible: with
``AFTERLIFE_EXECUTION_MODE=replay`` an entire run re-executes from disk with zero
network calls, so a reviewer without an API key can still re-derive the numbers.

Keys are ``sha256(provider ‖ path ‖ canonical_json(payload))``. Because the
payload includes the prompt, the sampling parameters and the stochastic seed, two
requests share a key only if they are genuinely the same request.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import orjson

from ..errors import CacheMissError
from ..hashing import canonical_json, sha256_text


def cache_key(provider: str, path: str, payload: dict[str, Any]) -> str:
    return sha256_text(f"{provider}\n{path}\n{canonical_json(payload)}")


class ResponseCache:
    """Flat sharded store of raw provider responses."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.hits = 0
        self.misses = 0

    def _path(self, key: str) -> Path:
        return self.root / key[:2] / f"{key}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        path = self._path(key)
        if not path.is_file():
            self.misses += 1
            return None
        self.hits += 1
        return orjson.loads(path.read_bytes())

    def require(self, key: str, *, context: str) -> dict[str, Any]:
        entry = self.get(key)
        if entry is None:
            raise CacheMissError(
                f"replay mode: no cached response for {context} (key {key[:12]}…). "
                "Either the config differs from the original run or the cache is incomplete."
            )
        return entry

    def put(
        self, key: str, *, provider: str, path: str, payload: dict[str, Any], body: Any
    ) -> None:
        target = self._path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Payload is stored alongside the body so a cache entry is self-describing
        # and a corrupted key can be diagnosed rather than merely dropped.
        target.write_bytes(
            orjson.dumps(
                {"provider": provider, "path": path, "payload": payload, "body": body},
                option=orjson.OPT_INDENT_2,
            )
        )

    def stats(self) -> dict[str, int]:
        return {"hits": self.hits, "misses": self.misses}
