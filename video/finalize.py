"""Master the rendered video, bundle reusable media and verify publication outputs."""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

VIDEO = Path(__file__).resolve().parent
ROOT = VIDEO.parent
OUT = VIDEO / "output"
PRODUCTION = VIDEO / "production"
RAW = ROOT / "runs" / "media-semantic-afterlife-20261109-v1"


def digest(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, check=True, text=True, encoding="utf-8")


def main() -> None:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    episode = json.loads((VIDEO / "episode.json").read_text(encoding="utf-8"))
    timeline = json.loads((VIDEO / "film/src/episode.generated.json").read_text(encoding="utf-8"))
    original = OUT / "semantic-afterlife.raw.mp4"
    # Two-pass EBU R128 loudness mastering; preserve the composition's ducking.
    measurement = command(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(original),
            "-vn",
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
            "-f",
            "null",
            "NUL",
        ]
    )
    start = measurement.stderr.rfind("{\n")
    loudness = json.JSONDecoder().raw_decode(measurement.stderr[start:])[0]
    write(PRODUCTION / "loudness-before.json", loudness)
    mastering = (
        "loudnorm=I=-16:TP=-1.5:LRA=11:linear=true:"
        f"measured_I={loudness['input_i']}:measured_TP={loudness['input_tp']}:"
        f"measured_LRA={loudness['input_lra']}:measured_thresh={loudness['input_thresh']}:"
        f"offset={loudness['target_offset']}"
    )
    chapter_lines = [";FFMETADATA1", "title=" + episode["title"], "artist=Semantic Afterlife"]
    for scene in timeline["scenes"]:
        chapter_lines.extend(
            [
                "[CHAPTER]",
                "TIMEBASE=1/1000",
                f"START={round(scene['from'] / timeline['fps'] * 1000)}",
                f"END={round((scene['from'] + scene['duration']) / timeline['fps'] * 1000)}",
                "title=" + scene["title"],
            ]
        )
    metadata = OUT / "chapters.ffmetadata"
    metadata.write_text("\n".join(chapter_lines) + "\n", encoding="utf-8")
    final = OUT / "semantic-afterlife.ru.mp4"
    command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(original),
            "-i",
            str(OUT / "semantic-afterlife.ru.srt"),
            "-f",
            "ffmetadata",
            "-i",
            str(metadata),
            "-map",
            "0:v",
            "-map",
            "0:a",
            "-map",
            "1:0",
            "-map_metadata",
            "2",
            "-map_chapters",
            "2",
            "-c:v",
            "copy",
            "-af",
            mastering,
            "-ar",
            "48000",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-c:s",
            "mov_text",
            "-metadata:s:s:0",
            "language=rus",
            "-metadata:s:a:0",
            "language=rus",
            "-movflags",
            "+faststart",
            str(final),
        ]
    )
    audio = OUT / "semantic-afterlife.ru.mp3"
    command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(final),
            "-vn",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(audio),
        ]
    )
    probe = json.loads(
        command(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_format",
                "-show_streams",
                "-show_chapters",
                "-of",
                "json",
                str(final),
            ]
        ).stdout
    )
    write(PRODUCTION / "ffprobe.json", probe)
    streams = probe["streams"]
    assert next(s for s in streams if s["codec_type"] == "video")["nb_frames"] == str(
        timeline["duration"]
    )
    assert abs(float(probe["format"]["duration"]) - timeline["duration"] / timeline["fps"]) < 0.1
    assert len(probe["chapters"]) == len(timeline["scenes"])
    assert {"video", "audio", "subtitle"} <= {s["codec_type"] for s in streams}
    # Decode the complete deliverable, rather than treating a successful mux as proof.
    command(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(final),
            "-map",
            "0:v",
            "-map",
            "0:a",
            "-f",
            "null",
            "NUL",
        ]
    )
    check = command(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(final),
            "-vn",
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
            "-f",
            "null",
            "NUL",
        ]
    )
    after = json.JSONDecoder().raw_decode(check.stderr[check.stderr.rfind("{\n") :])[0]
    write(PRODUCTION / "loudness-after.json", after)
    assert -17 < float(after["input_i"]) < -15
    assert float(after["input_tp"]) < -1.0
    # Publish reusable generated narration, music and provider request records.
    media_files = [
        *sorted((VIDEO / "film/public/voice").glob("*.mp3")),
        VIDEO / "film/public/score.mp3",
    ]
    with zipfile.ZipFile(
        OUT / "media-assets.zip", "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        for path in media_files:
            archive.write(path, path.relative_to(VIDEO).as_posix())
        for path in sorted(RAW.glob("*.json")):
            archive.write(path, "provider-record/" + path.name)
    inputs = json.loads((PRODUCTION / "inputs.json").read_text(encoding="utf-8"))
    for rel, expected in inputs["input_sha256"].items():
        assert digest(ROOT / rel) == expected, f"Source changed: {rel}"
    receipts = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted((PRODUCTION / "voice").glob("*.json"))
    ]
    assert len(receipts) == len(timeline["scenes"])
    for receipt in receipts:
        assert (
            digest(VIDEO / f"film/public/voice/{receipt['scene_id']}.mp3")
            == receipt["audio_sha256"]
        )
    ledger_path = ROOT / "runs/_ledger/spend.jsonl"
    ledger = [
        json.loads(line)
        for line in ledger_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    charges = [r for r in ledger if r.get("run_id") == RAW.name]
    assert len(charges) == len(receipts)
    assert abs(sum(r["cost_usd"] for r in charges) - sum(r["cost_usd"] for r in receipts)) < 1e-6
    # Recover historical successful-event entries once without rewriting the ledger.
    event_path = RAW / "events.jsonl"
    existing_events = (
        [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()]
        if event_path.exists()
        else []
    )
    present = {r["scene"] for r in existing_events}
    with event_path.open("a", encoding="utf-8") as handle:
        for receipt in receipts:
            if receipt["scene_id"] not in present:
                handle.write(
                    json.dumps(
                        {
                            "event": "tts_completed_receipt_reconciled",
                            "scene": receipt["scene_id"],
                            "receipt": receipt,
                            "reconciled_at": datetime.now(UTC).isoformat(),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
    source_files = [
        VIDEO / "episode.json",
        VIDEO / "produce.py",
        VIDEO / "align.py",
        VIDEO / "finalize.py",
        *sorted((VIDEO / "film/src").glob("*")),
        VIDEO / "film/package-lock.json",
    ]
    manifest = {
        "id": RAW.name,
        "type": "editorial_media_build",
        "research_stage": None,
        "created_at": datetime.now(UTC).isoformat(),
        "base_git_sha": inputs["git_sha"],
        "working_tree_source_sha256": {
            p.relative_to(ROOT).as_posix(): digest(p) for p in source_files if p.is_file()
        },
        "scientific_input_sha256": inputs["input_sha256"],
        "tts_calls": len(receipts),
        "tts_cost_usd_catalog": sum(r["cost_usd"] for r in receipts),
        "tts_cost_rub_catalog": sum(r["cost_rub"] for r in receipts),
        "image_generation_billing": "Built-in app context; project-dollar amount unknown, not recorded as zero",
        "duration_seconds": timeline["duration"] / timeline["fps"],
        "fps": timeline["fps"],
        "width": timeline["width"],
        "height": timeline["height"],
        "checks": {
            "full_decode": "pass",
            "frame_count": "pass",
            "all_sources_intact": "pass",
            "ledger_receipts_reconciled": "pass",
            "chapters": len(probe["chapters"]),
            "subtitle_stream": "rus",
            "loudness_lufs": after["input_i"],
            "true_peak_dbtp": after["input_tp"],
        },
    }
    write(PRODUCTION / "manifest.json", manifest)
    write(RAW / "manifest.json", manifest)
    (RAW / "episode.json").write_bytes((VIDEO / "episode.json").read_bytes())
    with zipfile.ZipFile(
        OUT / "media-assets.zip", "a", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        for path in [RAW / "manifest.json", RAW / "episode.json", event_path]:
            archive.write(path, "provider-record/" + path.name)
    deliverables = [
        final,
        audio,
        OUT / "semantic-afterlife.ru.srt",
        OUT / "semantic-afterlife.ru.vtt",
        OUT / "media-assets.zip",
    ]
    checksums = {p.name: {"sha256": digest(p), "bytes": p.stat().st_size} for p in deliverables}
    write(PRODUCTION / "deliverables.json", checksums)
    (OUT / "SHA256SUMS").write_text(
        "".join(f"{v['sha256']}  {k}\n" for k, v in checksums.items()), encoding="ascii"
    )
    print(json.dumps(manifest["checks"], indent=2), flush=True)
    print(json.dumps(checksums, indent=2), flush=True)


if __name__ == "__main__":
    main()
