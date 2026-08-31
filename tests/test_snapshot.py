"""Snapshots carry the state that costs money to regenerate.

Two properties matter and are tested in both directions. The archive must be a
deterministic function of the tree, or its recorded digest says nothing. And a
restore must refuse a corrupt archive rather than write unattributable data
under ``runs/`` -- a wrong trajectory on disk is worse than no trajectory,
because everything downstream will happily analyse it.
"""

from __future__ import annotations

import gzip
from pathlib import Path

import orjson
import pytest

from semantic_afterlife.snapshot import (
    MANIFEST_NAME,
    SnapshotError,
    build_part,
    create_snapshot,
    read_manifest,
    restore_snapshot,
    verify_part,
)


def make_tree(root: Path) -> None:
    (root / "runs" / "s1" / "run-a" / "data").mkdir(parents=True)
    (root / "runs" / "s1" / "run-a" / "manifest.json").write_text('{"status":"COMPLETED"}')
    (root / "runs" / "s1" / "run-a" / "data" / "chunks.parquet").write_bytes(b"\x00parquet")
    (root / "runs" / "_ledger").mkdir(parents=True)
    (root / "runs" / "_ledger" / "spend.jsonl").write_text('{"cost_usd":0.1}\n')
    (root / "cache" / "responses" / "ab").mkdir(parents=True)
    (root / "cache" / "responses" / "ab" / "abcd.json").write_text('{"choices":[]}')
    (root / "cache" / "embeddings").mkdir(parents=True)
    (root / "cache" / "embeddings" / "e1.npz").write_bytes(b"\x00npz")
    # Excluded by design: large and re-fetchable from the Hub.
    (root / "cache" / "tokenizers" / "big").mkdir(parents=True)
    (root / "cache" / "tokenizers" / "big" / "tokenizer.json").write_bytes(b"x" * 4096)


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    make_tree(root)
    return root


class TestDeterminism:
    def test_the_same_tree_produces_the_same_digest(self, tree: Path, tmp_path: Path) -> None:
        first = build_part(tree, "runs", ("runs",), tmp_path / "a")
        second = build_part(tree, "runs", ("runs",), tmp_path / "b")
        assert first.sha256 == second.sha256

    def test_a_changed_file_changes_the_digest(self, tree: Path, tmp_path: Path) -> None:
        before = build_part(tree, "runs", ("runs",), tmp_path / "a")
        (tree / "runs" / "s1" / "run-a" / "manifest.json").write_text('{"status":"FAILED"}')
        after = build_part(tree, "runs", ("runs",), tmp_path / "b")
        assert before.sha256 != after.sha256

    def test_the_gzip_wrapper_carries_no_timestamp(self, tree: Path, tmp_path: Path) -> None:
        """A build timestamp in the container would change the digest hourly."""
        part = build_part(tree, "runs", ("runs",), tmp_path / "a")
        raw = (tmp_path / "a" / part.archive).read_bytes()
        # Bytes 4..8 of a gzip header are the modification time, little-endian.
        assert raw[4:8] == b"\x00\x00\x00\x00"


class TestContents:
    def test_tokenizers_are_excluded(self, tree: Path, tmp_path: Path) -> None:
        manifest = create_snapshot(
            tree, tmp_path / "snap", created_utc="2026-01-01T00:00:00+00:00", git_sha="abc"
        )
        cache = next(p for p in manifest.parts if p.name == "cache")
        assert cache.n_files == 2  # one response, one embedding, no tokenizer

    def test_every_run_file_is_carried(self, tree: Path, tmp_path: Path) -> None:
        manifest = create_snapshot(
            tree, tmp_path / "snap", created_utc="2026-01-01T00:00:00+00:00", git_sha="abc"
        )
        runs = next(p for p in manifest.parts if p.name == "runs")
        assert runs.n_files == 3

    def test_manifest_round_trips(self, tree: Path, tmp_path: Path) -> None:
        out = tmp_path / "snap"
        created = create_snapshot(tree, out, created_utc="2026-01-01T00:00:00+00:00", git_sha="abc")
        loaded = read_manifest(out / MANIFEST_NAME)
        assert loaded.git_sha == "abc"
        assert [p.sha256 for p in loaded.parts] == [p.sha256 for p in created.parts]


class TestRestore:
    def _snapshot(self, tree: Path, tmp_path: Path) -> Path:
        out = tmp_path / "snap"
        create_snapshot(tree, out, created_utc="2026-01-01T00:00:00+00:00", git_sha="abc")
        return out

    def test_restores_into_an_empty_tree(self, tree: Path, tmp_path: Path) -> None:
        snap = self._snapshot(tree, tmp_path)
        target = tmp_path / "fresh"
        target.mkdir()
        written = restore_snapshot(snap, target)
        assert written == {"runs": 3, "cache": 2}
        assert (target / "runs" / "s1" / "run-a" / "manifest.json").read_text() == (
            '{"status":"COMPLETED"}'
        )
        assert (target / "cache" / "responses" / "ab" / "abcd.json").is_file()

    def test_existing_files_are_kept_by_default(self, tree: Path, tmp_path: Path) -> None:
        """A restore must not silently replace a local run with a stale copy."""
        snap = self._snapshot(tree, tmp_path)
        target = tmp_path / "occupied"
        (target / "runs" / "s1" / "run-a").mkdir(parents=True)
        (target / "runs" / "s1" / "run-a" / "manifest.json").write_text("LOCAL")
        restore_snapshot(snap, target)
        assert (target / "runs" / "s1" / "run-a" / "manifest.json").read_text() == "LOCAL"

    def test_overwrite_replaces_them(self, tree: Path, tmp_path: Path) -> None:
        snap = self._snapshot(tree, tmp_path)
        target = tmp_path / "occupied2"
        (target / "runs" / "s1" / "run-a").mkdir(parents=True)
        (target / "runs" / "s1" / "run-a" / "manifest.json").write_text("LOCAL")
        restore_snapshot(snap, target, overwrite=True)
        assert (target / "runs" / "s1" / "run-a" / "manifest.json").read_text() == (
            '{"status":"COMPLETED"}'
        )

    def test_a_corrupt_archive_is_refused(self, tree: Path, tmp_path: Path) -> None:
        """Unattributable data under runs/ is worse than no data: everything
        downstream would analyse it without knowing."""
        snap = self._snapshot(tree, tmp_path)
        archive = snap / "runs.tar.gz"
        archive.write_bytes(gzip.compress(b"not a tarball"))
        target = tmp_path / "fresh2"
        target.mkdir()
        with pytest.raises(SnapshotError, match="corrupt"):
            restore_snapshot(snap, target)
        assert not (target / "runs").exists()

    def test_a_missing_archive_is_refused(self, tree: Path, tmp_path: Path) -> None:
        snap = self._snapshot(tree, tmp_path)
        (snap / "cache.tar.gz").unlink()
        with pytest.raises(SnapshotError, match="missing archive"):
            restore_snapshot(snap, tmp_path / "x")

    def test_a_single_part_can_be_restored(self, tree: Path, tmp_path: Path) -> None:
        snap = self._snapshot(tree, tmp_path)
        target = tmp_path / "partial"
        target.mkdir()
        written = restore_snapshot(snap, target, only="runs")
        assert written == {"runs": 3}
        assert not (target / "cache").exists()

    def test_an_unknown_part_is_an_error(self, tree: Path, tmp_path: Path) -> None:
        snap = self._snapshot(tree, tmp_path)
        with pytest.raises(SnapshotError, match="no part named"):
            restore_snapshot(snap, tmp_path / "y", only="nope")

    def test_missing_manifest_is_an_error(self, tmp_path: Path) -> None:
        with pytest.raises(SnapshotError, match="no snapshot manifest"):
            restore_snapshot(tmp_path / "nothing", tmp_path / "z")


class TestVerification:
    def test_verify_accepts_a_matching_archive(self, tree: Path, tmp_path: Path) -> None:
        part = build_part(tree, "runs", ("runs",), tmp_path / "a")
        verify_part(tmp_path / "a" / part.archive, part)

    def test_verify_rejects_a_mutated_archive(self, tree: Path, tmp_path: Path) -> None:
        part = build_part(tree, "runs", ("runs",), tmp_path / "a")
        archive = tmp_path / "a" / part.archive
        archive.write_bytes(archive.read_bytes() + b"tail")
        with pytest.raises(SnapshotError):
            verify_part(archive, part)

    def test_manifest_is_sorted_and_readable(self, tree: Path, tmp_path: Path) -> None:
        out = tmp_path / "snap"
        create_snapshot(tree, out, created_utc="2026-01-01T00:00:00+00:00", git_sha=None)
        payload = orjson.loads((out / MANIFEST_NAME).read_bytes())
        assert payload["git_sha"] is None
        assert payload["total_bytes"] > 0
