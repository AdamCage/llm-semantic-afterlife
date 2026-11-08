"""Portable skill invariants; no live provider calls or publication."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/research-video/scripts"


def module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


video = module("portable_research_video", SCRIPTS / "video.py")
with patch.dict(sys.modules, {"video": video}):
    alignment = module("portable_research_alignment", SCRIPTS / "align.py")
    publisher = module("portable_research_publish", SCRIPTS / "publish.py")
installer = module("research_skill_installer", ROOT / "skills/install.py")


@pytest.fixture
def project(tmp_path: Path) -> Path:
    path = tmp_path / "a different research project"
    video.init(path)
    return path


def configure_budget(project: Path) -> dict:
    cfg = video.load(project)
    cfg["budget"] = {
        "ledger_path": "record/spend.jsonl",
        "production_usd": 0.5,
        "per_run_usd": 0.5,
        "project_usd": 1.0,
    }
    cfg["speech"]["usd_per_rub"] = 0.0125
    cfg["speech"]["max_rub_per_character"] = 0.002
    video.write(project / "episode.json", cfg)
    return cfg


def test_fresh_project_validates_without_source_repository(project: Path) -> None:
    assert video.validate(project)["mechanical_validation"] == "pass"
    assert video.prepare(project, True)["storyboard"] is True
    assert "semantic_afterlife" not in (SCRIPTS / "video.py").read_text(encoding="utf-8")


def test_changed_evidence_is_not_silently_accepted(project: Path) -> None:
    evidence = video.read(project / "evidence.json")
    evidence["sources"][0]["path"] = "not-here.csv"
    video.write(project / "evidence.json", evidence)
    with pytest.raises(ValueError, match="real file"):
        video.validate(project)


def test_paths_cannot_escape_evidence_boundary(project: Path) -> None:
    with pytest.raises(ValueError, match="escapes"):
        video.inside(project, "../other-project/private.txt")


def test_final_preparation_refuses_missing_voice(project: Path) -> None:
    with pytest.raises(ValueError, match="Missing narration"):
        video.prepare(project, False)


def test_figure_requires_tidy_data_and_limitations(project: Path) -> None:
    cfg = video.load(project)
    cfg["scenes"][0].update(visual="figure", asset="evidence/demo.txt")
    video.write(project / "episode.json", cfg)
    with pytest.raises(ValueError, match="tidy-data"):
        video.validate(project)


def test_existing_host_ledger_cannot_be_bypassed(project: Path) -> None:
    configure_budget(project)
    ledger = project / "runs/_ledger/spend.jsonl"
    ledger.parent.mkdir(parents=True)
    ledger.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="existing research spend ledger"):
        video.budget_paths(project, video.load(project))


def test_host_environment_can_only_lower_budget(project: Path) -> None:
    cfg = configure_budget(project)
    with patch.dict(
        os.environ, {"AFTERLIFE_BUDGET_USD_PER_RUN": "0.1", "AFTERLIFE_BUDGET_USD_TOTAL": "0.3"}
    ):
        _, _, per_run, total = video.budget_paths(project, cfg)
        assert per_run == 0.1
        assert total == 0.3


def test_timeout_keeps_conservative_charge_and_prevents_duplicate_send(project: Path) -> None:
    configure_budget(project)
    with (
        patch.object(video, "price", return_value=0.001),
        patch.dict(os.environ, {"ROUTERAI_API_KEY": "test-only-dummy"}),
        patch.object(
            video.urllib.request, "urlopen", side_effect=TimeoutError("observation expired")
        ) as network,
    ):
        video.estimate(project)
        with pytest.raises(TimeoutError):
            video.tts(project, "01")
        entries = video.jsonl(project / "record/spend.jsonl")
        assert len(entries) == 1 and entries[0]["cost_usd"] > 0
        assert (project / "record/pending/01.json").is_file()
        with pytest.raises(ValueError, match="Unresolved paid attempt"):
            video.tts(project, "01")
        assert network.call_count == 1


def test_corrupt_ledger_is_not_treated_as_free_budget(project: Path) -> None:
    cfg = configure_budget(project)
    ledger = project / cfg["budget"]["ledger_path"]
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text('{"cost_usd":', encoding="utf-8")
    with patch.object(video, "price", return_value=0.001), pytest.raises(json.JSONDecodeError):
        video.estimate(project)


def test_caption_alignment_preserves_anchors_and_bounds() -> None:
    words = ["Наука", "помогает", "проверять", "выводы."]
    heard = [
        {"word": "Наука", "start": 0.2, "end": 0.7},
        {"word": "проверять", "start": 1.3, "end": 1.8},
        {"word": "выводы", "start": 1.8, "end": 2.2},
    ]
    times, fraction = alignment.align(words, heard, 2.5)
    assert fraction == 0.75
    assert times[0] == (0.2, 0.7)
    assert 0.7 <= times[1][0] < times[1][1] <= 1.3
    assert all(0 <= start < end <= 2.5 for start, end in times)


def test_price_adapter_does_not_send_credentials_to_arbitrary_hosts(project: Path) -> None:
    cfg = video.load(project)
    cfg["speech"]["base_url"] = "https://example.invalid/api/v1"
    with (
        patch.object(video.urllib.request, "urlopen") as network,
        pytest.raises(ValueError, match="official RouterAI"),
    ):
        video.price(cfg)
    network.assert_not_called()


def test_publisher_dry_run_makes_no_network_mutations(project: Path) -> None:
    video.write(project / "record/master.json", {"full_decode": "pass"})
    file = project / "output/video.mp4"
    file.parent.mkdir()
    file.write_bytes(b"fixture-binary-for-dry-run-only")
    video.write(
        project / "record/deliverables.json",
        {file.name: {"bytes": file.stat().st_size, "sha256": video.sha(file)}},
    )
    notes = project / "release.md"
    notes.write_text("A concrete release description", encoding="utf-8")
    args = [
        "publish.py",
        "--project",
        str(project),
        "--repo",
        "example/research",
        "--tag",
        "video-v1",
        "--commit",
        "a" * 40,
        "--notes",
        str(notes),
        "--title",
        "Example",
    ]
    with patch.object(sys, "argv", args), patch.object(publisher, "gh") as network:
        publisher.main()
    network.assert_not_called()


def test_publisher_blocks_offline_fixture(project: Path) -> None:
    video.write(project / "record/master.json", {"full_decode": "pass", "smoke_test": True})
    notes = project / "release.md"
    notes.write_text("Fixture", encoding="utf-8")
    args = [
        "publish.py",
        "--project",
        str(project),
        "--repo",
        "example/research",
        "--tag",
        "video-v1",
        "--commit",
        "a" * 40,
        "--notes",
        str(notes),
        "--title",
        "Example",
        "--execute",
        "--publish",
    ]
    with (
        patch.object(sys, "argv", args),
        patch.object(publisher, "gh") as network,
        pytest.raises(ValueError, match="smoke-test"),
    ):
        publisher.main()
    network.assert_not_called()


def test_installer_preserves_existing_skills_and_backs_up_updates(tmp_path: Path) -> None:
    target = tmp_path / "codex/skills"
    paths = installer.install(target, False)
    assert len(paths) == 2
    marker = paths[0] / "local-customisation.txt"
    marker.write_text("preserve this", encoding="utf-8")
    with pytest.raises(FileExistsError):
        installer.install(target, False)
    installer.install(target, True)
    assert any(
        p.read_text(encoding="utf-8") == "preserve this"
        for p in (target.parent / "skill-backups").rglob("local-customisation.txt")
    )
