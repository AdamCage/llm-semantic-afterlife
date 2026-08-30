from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("AFTERLIFE_EXECUTION_MODE", "mock")

from semantic_afterlife.paths import repo_root
from semantic_afterlife.tokenization import WhitespaceTokenizer


@pytest.fixture
def whitespace_tokenizer() -> WhitespaceTokenizer:
    return WhitespaceTokenizer()


@pytest.fixture(scope="session")
def repo() -> Path:
    return repo_root()


@pytest.fixture
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point every output directory at a temp dir so tests never touch real runs."""
    monkeypatch.setenv("AFTERLIFE_EXECUTION_MODE", "mock")
    monkeypatch.setenv("AFTERLIFE_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("AFTERLIFE_ARTIFACTS_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setenv("AFTERLIFE_CACHE_DIR", str(tmp_path / "cache"))
    from semantic_afterlife.config import get_settings

    get_settings.cache_clear()
    yield tmp_path
    get_settings.cache_clear()
