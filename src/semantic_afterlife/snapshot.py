"""Portable snapshots of the regenerable-but-expensive state.

``runs/`` and ``cache/`` are git-ignored on purpose: they are large and
regenerable, and the boundary against ``artifacts/`` is what keeps the
repository reviewable. But "regenerable" costs money and hours, and an agent
that clones this repository sees none of it -- no trajectories to analyse and no
response cache to replay, so every command that needs data either fails or
spends.

This module moves that state between machines as verifiable archives:

    runs.tar.gz      every run directory, manifests, events, trajectories
    cache.tar.gz     content-addressed responses and embeddings

``cache/tokenizers/`` is deliberately excluded. It is 71 MB that any machine can
fetch from the Hub on first use, and shipping it would be the largest part of
the payload for no reproducibility gain.

Archives are built deterministically -- entries sorted, timestamps and ownership
zeroed -- so an unchanged tree produces a byte-identical archive with the same
digest. That is what makes ``sha256`` in the manifest a useful statement rather
than a timestamp of when someone happened to run the command.
"""

from __future__ import annotations

import gzip
import io
import tarfile
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import orjson

from .errors import AfterlifeError
from .hashing import sha256_file

MANIFEST_NAME = "snapshot.manifest.json"

#: Archive name -> directories it carries, relative to the repository root.
#: Ordered so that a partial restore still leaves a coherent state: runs first,
#: because they are what the analysis passes read.
PARTS: dict[str, tuple[str, ...]] = {
    "runs": ("runs",),
    "cache": ("cache/responses", "cache/embeddings"),
}

#: Never archived, whatever it costs to re-fetch.
EXCLUDED_NAMES = frozenset({".DS_Store", "Thumbs.db", "__pycache__"})


class SnapshotError(AfterlifeError):
    """Raised when an archive is missing, corrupt, or fails verification."""


@dataclass(slots=True)
class PartInfo:
    name: str
    archive: str
    sha256: str
    size_bytes: int
    n_files: int
    sources: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "archive": self.archive,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "n_files": self.n_files,
            "sources": list(self.sources),
        }


@dataclass(slots=True)
class SnapshotManifest:
    created_utc: str
    git_sha: str | None
    parts: list[PartInfo] = field(default_factory=list)

    @property
    def total_bytes(self) -> int:
        return sum(p.size_bytes for p in self.parts)

    def as_dict(self) -> dict[str, Any]:
        return {
            "created_utc": self.created_utc,
            "git_sha": self.git_sha,
            "parts": [p.as_dict() for p in self.parts],
            "total_bytes": self.total_bytes,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SnapshotManifest:
        return cls(
            created_utc=str(payload.get("created_utc", "")),
            git_sha=payload.get("git_sha"),
            parts=[
                PartInfo(
                    name=str(p["name"]),
                    archive=str(p["archive"]),
                    sha256=str(p["sha256"]),
                    size_bytes=int(p["size_bytes"]),
                    n_files=int(p["n_files"]),
                    sources=tuple(p.get("sources", ())),
                )
                for p in payload.get("parts", [])
            ],
        )


def _walk(root: Path, sources: Iterable[str]) -> Iterator[tuple[Path, str]]:
    """Yield ``(absolute path, archive name)`` for every file under ``sources``.

    Sorted, so the archive is a deterministic function of the tree.
    """
    for source in sources:
        base = root / source
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if any(part in EXCLUDED_NAMES for part in path.parts):
                continue
            yield path, path.relative_to(root).as_posix()


def _deterministic_info(name: str, size: int) -> tarfile.TarInfo:
    """A tar header with nothing machine- or time-specific in it."""
    info = tarfile.TarInfo(name=name)
    info.size = size
    info.mtime = 0
    info.mode = 0o644
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    return info


def build_part(root: Path, name: str, sources: Iterable[str], out_dir: Path) -> PartInfo:
    """Archive one part and describe it."""
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"{name}.tar.gz"
    n_files = 0
    # The gzip container is written explicitly with mtime=0 and an empty stored
    # filename. Otherwise the wrapper carries a build timestamp and the archive
    # digest changes on every run even when nothing inside it did.
    with (
        archive.open("wb") as raw,
        gzip.GzipFile(fileobj=raw, mode="wb", compresslevel=6, mtime=0, filename="") as gz,
        tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tar,
    ):
        for path, arcname in _walk(root, sources):
            data = path.read_bytes()
            tar.addfile(_deterministic_info(arcname, len(data)), io.BytesIO(data))
            n_files += 1
    return PartInfo(
        name=name,
        archive=archive.name,
        sha256=sha256_file(archive),
        size_bytes=archive.stat().st_size,
        n_files=n_files,
        sources=tuple(sources),
    )


def create_snapshot(
    root: Path,
    out_dir: Path,
    *,
    created_utc: str,
    git_sha: str | None,
    parts: dict[str, tuple[str, ...]] | None = None,
) -> SnapshotManifest:
    """Build every archive and write the manifest beside them."""
    selected = parts if parts is not None else PARTS
    manifest = SnapshotManifest(created_utc=created_utc, git_sha=git_sha)
    for name, sources in selected.items():
        manifest.parts.append(build_part(root, name, sources, out_dir))
    (out_dir / MANIFEST_NAME).write_bytes(
        orjson.dumps(manifest.as_dict(), option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS)
    )
    return manifest


def read_manifest(path: Path) -> SnapshotManifest:
    if not path.is_file():
        raise SnapshotError(f"no snapshot manifest at {path}")
    return SnapshotManifest.from_dict(orjson.loads(path.read_bytes()))


def verify_part(archive: Path, part: PartInfo) -> None:
    if not archive.is_file():
        raise SnapshotError(f"missing archive {archive}")
    digest = sha256_file(archive)
    if digest != part.sha256:
        raise SnapshotError(
            f"{archive.name} hashes to {digest[:12]}… but the manifest says "
            f"{part.sha256[:12]}…; the archive is truncated or corrupt, and restoring it "
            "would put unattributable data under runs/"
        )


def restore_part(archive: Path, root: Path, *, overwrite: bool) -> int:
    """Extract one archive under ``root``; returns the number of files written.

    Existing files are left alone unless ``overwrite``, so a restore onto a
    machine that already has data cannot silently replace a local run with a
    stale copy from the snapshot.
    """
    written = 0
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar:
            if not member.isfile():
                continue
            target = root / member.name
            # Refuse anything that would escape the repository root.
            if not target.resolve().is_relative_to(root.resolve()):
                raise SnapshotError(f"archive member {member.name!r} escapes the root")
            if target.exists() and not overwrite:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            extracted = tar.extractfile(member)
            if extracted is None:
                continue
            target.write_bytes(extracted.read())
            written += 1
    return written


def restore_snapshot(
    snapshot_dir: Path, root: Path, *, overwrite: bool = False, only: str | None = None
) -> dict[str, int]:
    """Verify then extract every part; returns files written per part."""
    manifest = read_manifest(snapshot_dir / MANIFEST_NAME)
    written: dict[str, int] = {}
    for part in manifest.parts:
        if only is not None and part.name != only:
            continue
        archive = snapshot_dir / part.archive
        verify_part(archive, part)
        written[part.name] = restore_part(archive, root, overwrite=overwrite)
    if only is not None and not written:
        raise SnapshotError(f"snapshot has no part named {only!r}")
    return written
