"""Locally align the approved script to its narration; no hosted ASR charges.

Recognised words anchor the script with sequence matching. Unmatched words get
interpolated timing, explicitly recorded in the alignment report. The published
subtitles preserve the script rather than silently publishing ASR spelling.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import numpy as np
from faster_whisper import WhisperModel

VIDEO = Path(__file__).resolve().parent


def normalise(text: str) -> str:
    return re.sub(r"[^а-яa-z0-9]", "", text.lower().replace("ё", "е"))


def timecode(seconds: float, vtt: bool = False) -> str:
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{'.' if vtt else ','}{ms:03d}"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    data = json.loads((VIDEO / "film/src/episode.generated.json").read_text(encoding="utf-8"))
    model = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=6)
    captions: list[dict[str, Any]] = []
    report: list[dict[str, Any]] = []
    for scene in data["scenes"]:
        cache = VIDEO / "production" / "asr" / f"{scene['id']}.json"
        cache.parent.mkdir(exist_ok=True, parents=True)
        if cache.exists():
            recognised = json.loads(cache.read_text(encoding="utf-8"))
        else:
            decoded = subprocess.run(
                [
                    "ffmpeg",
                    "-v",
                    "error",
                    "-i",
                    str(VIDEO / f"film/public/voice/{scene['id']}.mp3"),
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
                language="ru",
                word_timestamps=True,
                beam_size=5,
                condition_on_previous_text=False,
            )
            recognised = [
                {"word": w.word, "start": w.start, "end": w.end, "probability": w.probability}
                for s in segments
                for w in s.words or []
            ]
            cache.write_text(json.dumps(recognised, ensure_ascii=False, indent=2), encoding="utf-8")
        words = scene["narration"].split()
        script_tokens = [normalise(w) for w in words]
        heard_tokens = [normalise(w["word"]) for w in recognised]
        matching = SequenceMatcher(None, script_tokens, heard_tokens, autojunk=False)
        anchors: dict[int, tuple[float, float]] = {}
        for block in matching.get_matching_blocks():
            for j in range(block.size):
                w = recognised[block.b + j]
                anchors[block.a + j] = (w["start"], w["end"])
        speech_duration = scene["speechFrames"] / data["fps"]
        positions = sorted(anchors)
        timing: list[tuple[float, float]] = []
        for i in range(len(words)):
            if i in anchors:
                timing.append(anchors[i])
                continue
            prev = max((j for j in positions if j < i), default=-1)
            next_ = min((j for j in positions if j > i), default=len(words))
            start = anchors[prev][1] if prev >= 0 else 0.0
            end = anchors[next_][0] if next_ < len(words) else speech_duration
            span = max(0.02, end - start) / (next_ - prev - 1)
            timing.append((start + (i - prev - 1) * span, start + (i - prev) * span))
        offset = (scene["from"] + scene["lead"]) / data["fps"]
        group: list[str] = []
        start_index = 0
        for i, word in enumerate(words):
            if not group:
                start_index = i
            group.append(word)
            if len(" ".join(group)) >= 64 or word.endswith((".", "?", "!")) or i == len(words) - 1:
                start = offset + timing[start_index][0]
                end = offset + max(timing[i][1], timing[start_index][0] + 0.15)
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
        coverage = len(anchors) / len(words)
        row = {
            "scene": scene["id"],
            "script_words": len(words),
            "recognised_words": len(recognised),
            "exact_word_anchor_fraction": coverage,
            "interpolated_word_count": len(words) - len(anchors),
            "last_recognised_end": recognised[-1]["end"] if recognised else None,
            "speech_duration": speech_duration,
        }
        report.append(row)
        print(json.dumps(row), flush=True)
    (VIDEO / "production/captions.json").write_text(
        json.dumps(captions, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (VIDEO / "production/alignment.json").write_text(
        json.dumps(
            {
                "model": "faster-whisper/base",
                "device": "cpu",
                "compute_type": "int8",
                "method": "exact normalised word anchors; unmatched script words interpolated",
                "scenes": report,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    output = VIDEO / "output"
    output.mkdir(exist_ok=True)
    srt, vtt = [], ["WEBVTT\n"]
    for i, c in enumerate(captions, 1):
        start, end = c["startMs"] / 1000, c["endMs"] / 1000
        srt.append(f"{i}\n{timecode(start)} --> {timecode(end)}\n{c['text']}\n")
        vtt.append(f"{timecode(start, True)} --> {timecode(end, True)}\n{c['text']}\n")
    (output / "semantic-afterlife.ru.srt").write_text("\n".join(srt), encoding="utf-8")
    (output / "semantic-afterlife.ru.vtt").write_text("\n".join(vtt), encoding="utf-8")


if __name__ == "__main__":
    main()
