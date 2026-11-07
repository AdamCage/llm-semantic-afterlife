"""Guards for the S13 synthesis language. No trajectories are read."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from s13_assemble import forbidden_prose, refuse_pooled_family


def test_forbidden_prose_catches_permanence_and_gemma_overclaim() -> None:
    assert forbidden_prose("The panels are counted by family.") == []
    hits = forbidden_prose(
        "The lock is absorbing. Full attention is unnecessary. Gemma disagrees across spaces."
    )
    assert "absorbing" in hits
    assert any("full attention" in hit for hit in hits)
    assert any("disagree" in hit for hit in hits)


def test_refuse_pooled_family() -> None:
    clean = pd.DataFrame({"family": ["Qwen3-8B", "OLMo-3-7B"]})
    refuse_pooled_family(clean)
    try:
        refuse_pooled_family(pd.DataFrame({"family": ["pooled"]}))
    except SystemExit as exc:
        assert "pooled" in str(exc)
    else:
        raise AssertionError("a pooled family row must stop the assembly")
