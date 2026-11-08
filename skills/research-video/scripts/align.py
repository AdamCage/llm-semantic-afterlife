"""Local word-anchored subtitles. Run with uv --with faster-whisper==1.2.1.

The script preserves authored wording and explicitly reports interpolated timing.
"""

from __future__ import annotations

import argparse
import difflib
import itertools
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from video import read, sha, write


def token(text: str) -> str:
    # Unicode letters/numerals, usable outside Russian too.
    return "".join(ch for ch in text.casefold().replace("ё", "е") if ch.isalnum())


def timestamp(seconds: float, vtt: bool = False) -> str:
    ms = max(0, round(seconds * 1000))
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    seconds_int, ms = divmod(ms, 1000)
    return f"{hours:02}:{minutes:02}:{seconds_int:02}{'.' if vtt else ','}{ms:03}"


def align(
    words: list[str], recognised: list[dict[str, Any]], duration: float
) -> tuple[list[tuple[float, float]], float]:
    matches = difflib.SequenceMatcher(
        None, [token(w) for w in words], [token(w["word"]) for w in recognised], autojunk=False
    )
    anchors: dict[int, tuple[float, float]] = {}
    for block in matches.get_matching_blocks():
        for j in range(block.size):
            item = recognised[block.b + j]
            anchors[block.a + j] = (item["start"], item["end"])
    times = []
    for index in range(len(words)):
        if index in anchors:
            times.append(anchors[index])
            continue
        left = max((i for i in anchors if i < index), default=-1)
        right = min((i for i in anchors if i > index), default=len(words))
        start = anchors[left][1] if left >= 0 else 0.0
        end = anchors[right][0] if right < len(words) else duration
        step = max(0.001, end - start) / (right - left - 1)
        times.append(
            (start + (index - left - 1) * step, min(duration, start + (index - left) * step))
        )
    return times, len(anchors) / max(1, len(words))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--model", default="base")
    args = parser.parse_args()
    project = args.project.resolve()
    import numpy as np
    from faster_whisper import WhisperModel

    cfg = read(project / "episode.json")
    timeline = read(project / "renderer/src/episode.generated.json")
    if timeline["storyboard"]:
        raise ValueError("Cannot align missing storyboard narration")
    model = WhisperModel(args.model, device="cpu", compute_type="int8", cpu_threads=4)
    captions = []
    report = []
    for scene in timeline["scenes"]:
        audio = project / "media/voice" / f"{scene['id']}.mp3"
        key = {"audio_sha256": sha(audio), "model": args.model, "language": cfg["language"]}
        cache = project / "record/asr" / f"{scene['id']}.json"
        if cache.exists() and read(cache)["key"] == key:
            recognised = read(cache)["words"]
        else:
            decoded = subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-i",
                    str(audio),
                    "-f",
                    "f32le",
                    "-ar",
                    "16000",
                    "-ac",
                    "1",
                    "pipe:1",
                ],
                capture_output=True,
                check=True,
            ).stdout
            segments, _ = model.transcribe(
                np.frombuffer(decoded, dtype=np.float32),
                language=cfg["language"],
                word_timestamps=True,
                beam_size=5,
                condition_on_previous_text=False,
            )
            recognised = [
                {"word": w.word, "start": w.start, "end": w.end}
                for s in segments
                for w in s.words or []
            ]
            write(cache, {"key": key, "words": recognised})
        words = scene["narration"].split()
        duration = scene["speech_frames"] / cfg["fps"]
        times, fraction = align(words, recognised, duration)
        offset = (scene["from"] + scene["lead"]) / cfg["fps"]
        begin = 0
        group: list[str] = []
        for index, word in enumerate(words):
            if not group:
                begin = index
            group.append(word)
            if (
                len(" ".join(group)) >= 64
                or re.search(r"[.!?。！？]$", word)
                or index == len(words) - 1
            ):
                start = offset + times[begin][0]
                end = offset + min(duration, max(times[index][1], times[begin][0] + 0.05))
                captions.append(
                    {
                        "text": " ".join(group),
                        "startMs": start * 1000,
                        "endMs": end * 1000,
                        "timestampMs": None,
                        "confidence": None,
                    }
                )
                group = []
        report.append(
            {
                "scene": scene["id"],
                "anchor_fraction": fraction,
                "speech_duration": duration,
                "last_asr_end": recognised[-1]["end"] if recognised else None,
                "status": "needs_review" if fraction < 0.8 else "timing_anchors_available",
            }
        )
        print(json.dumps(report[-1]), flush=True)
    for left, right in itertools.pairwise(captions):
        left["endMs"] = min(left["endMs"], right["startMs"])
    if any(c["endMs"] <= c["startMs"] for c in captions):
        raise ValueError("Nonpositive subtitle intervals; inspect alignment instead of publishing")
    write(project / "record/captions.json", captions)
    write(
        project / "record/alignment.json",
        {
            "method": "local ASR exact normalised word anchors; unmatched script words interpolated",
            "model": args.model,
            "scenes": report,
        },
    )
    output = project / "output"
    output.mkdir(exist_ok=True)
    srt, vtt = [], ["WEBVTT\n"]
    for index, caption in enumerate(captions, 1):
        start, end = caption["startMs"] / 1000, caption["endMs"] / 1000
        srt.append(f"{index}\n{timestamp(start)} --> {timestamp(end)}\n{caption['text']}\n")
        vtt.append(f"{timestamp(start, True)} --> {timestamp(end, True)}\n{caption['text']}\n")
    (output / "subtitles.srt").write_bytes("\n".join(srt).encode())
    (output / "subtitles.vtt").write_bytes("\n".join(vtt).encode())


if __name__ == "__main__":
    main()
