"""Independent mechanical video review; Python stdlib + FFmpeg/ffprobe.

Does not assess scientific entailment, listen to audio, publish or modify sources.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=True, capture_output=True, text=True, encoding="utf-8")


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def review(video: Path, project: Path | None, output: Path, snapshots: bool) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    checks: dict[str, Any] = {}
    probe = json.loads(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_format",
                "-show_streams",
                "-show_chapters",
                "-of",
                "json",
                str(video),
            ]
        ).stdout
    )
    streams = probe["streams"]
    v = next(s for s in streams if s["codec_type"] == "video")
    audio = [s for s in streams if s["codec_type"] == "audio"]
    checks["audio_stream_exists"] = bool(audio)
    checks["positive_duration"] = float(probe["format"]["duration"]) > 0
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(video),
            "-map",
            "0:v",
            "-map",
            "0:a?",
            "-f",
            "null",
            os.devnull,
        ]
    )
    checks["full_decode"] = True
    measurements: dict[str, Any] = {
        "sha256": sha(video),
        "bytes": video.stat().st_size,
        "duration_seconds": float(probe["format"]["duration"]),
        "width": v["width"],
        "height": v["height"],
        "fps": v["avg_frame_rate"],
    }
    timeline = None
    if project:
        cfg = read(project / "episode.json")
        timeline = read(project / "renderer/src/episode.generated.json")
        checks["not_storyboard"] = not timeline["storyboard"]
        checks["dimensions"] = (v["width"], v["height"]) == (cfg["width"], cfg["height"])
        numerator, denominator = map(int, v["avg_frame_rate"].split("/"))
        checks["fps"] = denominator > 0 and abs(numerator / denominator - cfg["fps"]) < 1e-6
        checks["frame_count"] = int(v.get("nb_frames", -1)) == timeline["duration"]
        checks["duration"] = (
            abs(measurements["duration_seconds"] - timeline["duration"] / cfg["fps"]) < 0.12
        )
        checks["chapters"] = len(probe.get("chapters", [])) == len(timeline["scenes"])
        if (project / "output/subtitles.srt").exists():
            checks["subtitle_stream"] = any(s["codec_type"] == "subtitle" for s in streams)
        delivered = project / "record/deliverables.json"
        if delivered.exists():
            entries = read(delivered)
            checks["deliverable_hashes"] = all(
                (project / "output" / name).is_file()
                and sha(project / "output" / name) == item["sha256"]
                for name, item in entries.items()
            )
        inputs = project / "record/build-inputs.json"
        if inputs.exists():
            values = read(inputs)
            checks["project_input_hashes"] = all(
                (project / path).is_file() and sha(project / path) == expected
                for path, expected in values["project_hashes"].items()
            )
            root = (project / cfg["research_root"]).resolve()
            sources = {s["id"]: s for s in read(project / "evidence.json")["sources"]}
            checks["evidence_hashes"] = all(
                sid in sources
                and (root / sources[sid]["path"]).is_file()
                and sha(root / sources[sid]["path"]) == expected
                for sid, expected in values["evidence_source_hashes"].items()
            )
        alignment = project / "record/alignment.json"
        if alignment.exists():
            measurements["alignment_spans_needing_review"] = [
                s["scene"] for s in read(alignment)["scenes"] if s.get("status") == "needs_review"
            ]
    if audio:
        audio_measurement = run(
            [
                "ffmpeg",
                "-hide_banner",
                "-i",
                str(video),
                "-vn",
                "-af",
                "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
                "-f",
                "null",
                os.devnull,
            ]
        )
        loudness = json.JSONDecoder().raw_decode(
            audio_measurement.stderr[audio_measurement.stderr.rfind("{\n") :]
        )[0]
        measurements["loudness"] = loudness
        if project:
            target = cfg["mastering"]
            checks["loudness"] = abs(float(loudness["input_i"]) - target["lufs"]) <= 1
            checks["true_peak"] = float(loudness["input_tp"]) <= target["true_peak"] + 0.5
    if snapshots:
        if timeline:
            times = [
                (s["from"] + min(s["duration"] // 2, s["lead"] + 4 * timeline["fps"]))
                / timeline["fps"]
                for s in timeline["scenes"]
            ]
        else:
            duration = measurements["duration_seconds"]
            times = [
                min(max(0, duration - 0.1), duration * fraction) for fraction in [0.1, 0.5, 0.9]
            ]
        for index, seconds in enumerate(times, 1):
            run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-y",
                    "-ss",
                    str(seconds),
                    "-i",
                    str(video),
                    "-frames:v",
                    "1",
                    str(output / f"scene-{index:02}.png"),
                ]
            )
        measurements["snapshots"] = len(times)
    result = {
        "mechanical_verdict": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "measurements": measurements,
        "scientific_entailment": "requires_source_reading",
        "visual_reading": "requires_inspection_of_frames_and_motion",
        "listening_review": "not_performed_by_script",
    }
    (output / "review.json").write_bytes(
        (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode()
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path)
    parser.add_argument("--video", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--snapshots", action="store_true")
    args = parser.parse_args()
    if args.project is None and args.video is None:
        parser.error("Provide --project or --video")
    project = args.project.resolve() if args.project else None
    if args.video:
        video = args.video.resolve()
    else:
        assert project is not None
        video = project / "output/video.mp4"
    output = (
        args.output.resolve()
        if args.output
        else (project / "record/review" if project else video.parent / "video-review")
    )
    result = review(video, project, output, args.snapshots)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if result["mechanical_verdict"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
