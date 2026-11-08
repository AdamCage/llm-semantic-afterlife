"""Editorial media build; never generates or re-estimates research data.

Run from the repository root with `uv run python video/produce.py COMMAND`.
The episode JSON is the authority for narration and production parameters.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict
from scipy.io import wavfile

from semantic_afterlife.config import Settings
from semantic_afterlife.ledger import Ledger, Usage
from semantic_afterlife.viz.theme import PALETTE

ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "video"
PUBLIC = VIDEO / "film" / "public"
PRODUCTION = VIDEO / "production"


class Voice(BaseModel):
    model: str
    voice: str
    response_format: str
    price_rub_per_character: float
    budget_usd: float


class Soundtrack(BaseModel):
    seed: int
    bpm: float
    sample_rate: int
    music_gain: float
    ducked_gain: float
    transition_gain: float


class Scene(BaseModel):
    id: str
    chapter: str
    title: str
    visual: str
    asset: str | None = None
    lines: list[str]
    narration: str
    sources: list[str]
    inference: str | None = None


class Episode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    language: str
    fps: int
    width: int
    height: int
    voice: Voice
    soundtrack: Soundtrack
    scenes: list[Scene]


def load() -> Episode:
    return Episode.model_validate_json((VIDEO / "episode.json").read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.file_digest(path.open("rb"), "sha256").hexdigest()


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def append(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")


def run(command: list[str]) -> str:
    return subprocess.run(
        command, check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout


def ledger(settings: Settings, episode: Episode) -> Ledger:
    return Ledger(
        settings.paths.ledger,
        run_id="media-semantic-afterlife-20261109-v1",
        per_run_ceiling_usd=settings.afterlife_budget_usd_per_run,
        total_ceiling_usd=settings.afterlife_budget_usd_total,
        stage_ceiling_usd=episode.voice.budget_usd,
    )


def estimate(episode: Episode, settings: Settings) -> None:
    chars = sum(len(scene.narration) for scene in episode.scenes)
    rub = chars * episode.voice.price_rub_per_character
    account = ledger(settings, episode)
    print(
        json.dumps(
            {
                "characters": chars,
                "words": sum(len(s.narration.split()) for s in episode.scenes),
                "estimate_rub": rub,
                "estimate_usd": rub * settings.afterlife_usd_per_rub,
                "production_cap_usd": episode.voice.budget_usd,
                **account.summary(),
            },
            indent=2,
        )
    )


def tts(episode: Episode, settings: Settings, only: str | None) -> None:
    account = ledger(settings, episode)
    estimate(episode, settings)
    audio_dir = PUBLIC / "voice"
    audio_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = settings.paths.runs / "media-semantic-afterlife-20261109-v1"
    raw_dir.mkdir(parents=True, exist_ok=True)
    # Keep a public provenance subset separately; raw headers never enter Git.
    with httpx.Client(timeout=settings.afterlife_request_timeout_s) as client:
        catalog = client.get(settings.routerai_base_url + "/models")
        catalog.raise_for_status()
        model = next(m for m in catalog.json()["data"] if m["id"] == episode.voice.model)
        actual_rate = float(model["pricing"]["prompt"])
        if actual_rate > episode.voice.price_rub_per_character:
            raise RuntimeError(
                "TTS price increased; refresh the estimate before sending paid requests"
            )
        save_json(PRODUCTION / "tts-model.json", model)
        for scene in episode.scenes:
            if only is not None and scene.id != only:
                continue
            request = {
                "model": episode.voice.model,
                "voice": episode.voice.voice,
                "response_format": episode.voice.response_format,
                "input": scene.narration,
            }
            digest = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
            dest = audio_dir / f"{scene.id}.mp3"
            receipt = PRODUCTION / "voice" / f"{scene.id}.json"
            if dest.exists() and receipt.exists():
                previous = json.loads(receipt.read_text(encoding="utf-8"))
                if previous["request_sha256"] == digest and previous["audio_sha256"] == sha(dest):
                    print(f"{scene.id}: verified cached narration", flush=True)
                    continue
                raise RuntimeError(
                    f"Scene {scene.id} changed: version the production before regenerating"
                )
            if (raw_dir / f"{scene.id}.pending.json").exists():
                raise RuntimeError(
                    f"Scene {scene.id} has an unresolved paid attempt; reconcile before retry"
                )
            rub = len(scene.narration) * actual_rate
            usd = rub * settings.afterlife_usd_per_rub
            account.reserve(usd, what=f"narration scene {scene.id}")
            pending = raw_dir / f"{scene.id}.pending.json"
            save_json(
                pending,
                {"request": request, "estimated_rub": rub, "ts": datetime.now(UTC).isoformat()},
            )
            response = client.post(
                settings.routerai_base_url + "/audio/speech",
                json=request,
                headers={"Authorization": f"Bearer {settings.api_key('routerai')}"},
            )
            safe_headers = {
                k: v
                for k, v in response.headers.items()
                if k in {"content-type", "content-length", "x-generation-id", "x-request-id"}
                or "cost" in k
                or "usage" in k
            }
            save_json(
                raw_dir / f"{scene.id}.response.json",
                {"status": response.status_code, "headers": safe_headers},
            )
            (raw_dir / f"{scene.id}.response.bin").write_bytes(response.content)
            response.raise_for_status()
            if "audio" not in response.headers.get(
                "content-type", ""
            ) and not response.content.startswith((b"ID3", b"\xff")):
                raise RuntimeError(
                    "TTS response is not audio; paid attempt retained for reconciliation"
                )
            # RouterAI prices TTS by character. Until provider billing is
            # reconciled, book the full catalog charge (never pretend it is free).
            account.record(
                Usage(0, 0, usd, cost_rub=rub),
                kind="media_tts",
                scene_id=scene.id,
                model=episode.voice.model,
                n_characters=len(scene.narration),
                pricing_unit="character",
                accounting_basis="catalog_character_charge",
                provider_generation_id=response.headers.get("x-generation-id"),
            )
            append(
                raw_dir / "events.jsonl",
                {
                    "event": "tts_completed",
                    "scene": scene.id,
                    "request_sha256": digest,
                    "audio_sha256": hashlib.sha256(response.content).hexdigest(),
                    "cost_rub": rub,
                    "cost_usd": usd,
                    "ts": datetime.now(UTC).isoformat(),
                },
            )
            dest.write_bytes(response.content)
            save_json(
                receipt,
                {
                    "scene_id": scene.id,
                    "request_sha256": digest,
                    "audio_sha256": sha(dest),
                    "model": episode.voice.model,
                    "voice": episode.voice.voice,
                    "characters": len(scene.narration),
                    "cost_rub": rub,
                    "cost_usd": usd,
                    "accounting_basis": "catalog_character_charge",
                    "response_headers": safe_headers,
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            pending.rename(raw_dir / f"{scene.id}.request.json")
            print(f"{scene.id}: {len(response.content)} bytes, {rub:.3f} RUB", flush=True)


def clean_records(path: Path) -> list[dict[str, Any]]:
    frame = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    return json.loads(frame.to_json(orient="records"))


def prepare(episode: Episode) -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    PRODUCTION.mkdir(parents=True, exist_ok=True)
    cursor = 0
    timeline: list[dict[str, Any]] = []
    script = [f"# {episode.title}\n", "Russian narration; sources are not spoken.\n"]
    captions: list[dict[str, Any]] = []
    for scene in episode.scenes:
        for source in scene.sources:
            if not (ROOT / source).exists():
                raise FileNotFoundError(source)
        voice = PUBLIC / "voice" / f"{scene.id}.mp3"
        if voice.exists():
            seconds = float(
                run(
                    [
                        "ffprobe",
                        "-v",
                        "error",
                        "-show_entries",
                        "format=duration",
                        "-of",
                        "default=nw=1:nk=1",
                        str(voice),
                    ]
                )
            )
        else:
            # Timing-only storyboard, never labelled finished narration.
            seconds = len(scene.narration.split()) / 2.2
        lead = round(0.7 * episode.fps)
        speech_frames = math.ceil(seconds * episode.fps)
        duration = lead + speech_frames + round(1.3 * episode.fps)
        item = {
            **scene.model_dump(),
            "from": cursor,
            "duration": duration,
            "lead": lead,
            "speechFrames": speech_frames,
            "voiceReady": voice.exists(),
        }
        timeline.append(item)
        # Sentence-level timing is proportional until alignment is available;
        # this metadata is explicit so it cannot masquerade as forced alignment.
        import re

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", scene.narration) if s.strip()]
        total = sum(len(s) for s in sentences)
        offset = float(cursor + lead)
        for sentence in sentences:
            length = speech_frames * len(sentence) / total
            captions.append(
                {
                    "text": sentence,
                    "startMs": offset / episode.fps * 1000,
                    "endMs": (offset + length) / episode.fps * 1000,
                    "timestampMs": None,
                    "confidence": None,
                }
            )
            offset += length
        script.extend(
            [
                f"## {scene.id}. {scene.title}\n",
                scene.narration + "\n",
                "Sources: " + ", ".join(f"`{s}`" for s in scene.sources) + "\n",
            ]
        )
        cursor += duration
    data = {
        "title": episode.title,
        "fps": episode.fps,
        "width": episode.width,
        "height": episode.height,
        "duration": cursor,
        "scenes": timeline,
        "palette": PALETTE,
        "replication": clean_records(
            ROOT / "artifacts/occupancy-replication/domain_separation_last_band.csv"
        ),
        "familyGap": clean_records(ROOT / "artifacts/stage-13/gt_published/gt_published.csv"),
        "completion": clean_records(ROOT / "artifacts/stage-13/completion/completion.csv"),
        "escape": clean_records(
            ROOT / "artifacts/stage-13/tau_escape_s12/tau_escape_s12.data.parquet"
        ),
    }
    save_json(VIDEO / "film" / "src" / "episode.generated.json", data)
    save_json(PRODUCTION / "captions.approximate.json", captions)
    (VIDEO / "SCRIPT.ru.md").write_text("\n".join(script), encoding="utf-8")
    inputs = {"video/episode.json": sha(VIDEO / "episode.json")}
    for scene in episode.scenes:
        for source in scene.sources:
            path = ROOT / source
            if path.is_file():
                inputs[source] = sha(path)
    save_json(
        PRODUCTION / "inputs.json",
        {
            "git_sha": run(["git", "rev-parse", "HEAD"]).strip(),
            "input_sha256": inputs,
            "duration_seconds": cursor / episode.fps,
            "narration_complete": all(s["voiceReady"] for s in timeline),
        },
    )
    print(f"Prepared {len(timeline)} scenes, {cursor / episode.fps:.2f}s")


def sound(episode: Episode) -> None:
    """Original slow ambient score: pads, soft felt-like notes, no sampled music."""
    data = json.loads((VIDEO / "film/src/episode.generated.json").read_text(encoding="utf-8"))
    cfg = episode.soundtrack
    sr = cfg.sample_rate
    duration = data["duration"] / episode.fps
    n = math.ceil(duration * sr)
    # Float32 stereo keeps the ten-minute score bounded in memory.
    music = np.zeros((n, 2), dtype=np.float32)
    rng = np.random.default_rng(cfg.seed)
    beat = 60 / cfg.bpm
    bar = beat * 4
    # D minor add9 / Bb maj7 / F add9 / C suspended; sparse, consonant.
    chords = [
        (50, 57, 60, 64, 69),
        (46, 53, 57, 60, 65),
        (48, 53, 57, 60, 67),
        (48, 55, 58, 62, 67),
    ]

    def add_note(
        start: float, length: float, midi: int, gain: float, pan: float, pad: bool
    ) -> None:
        left = max(0, round(start * sr))
        count = min(round(length * sr), n - left)
        if count <= 0:
            return
        t = np.arange(count, dtype=np.float32) / sr
        freq = 440 * 2 ** ((midi - 69) / 12)
        if pad:
            envelope = np.sin(np.pi * np.minimum(t / length, 1)) ** 2
            tone = np.sin(2 * np.pi * freq * t) + 0.23 * np.sin(2 * np.pi * freq * 2.002 * t)
        else:
            envelope = (1 - np.exp(-t * 32)) * np.exp(-t * 1.5)
            tone = np.sin(2 * np.pi * freq * t) + 0.18 * np.sin(2 * np.pi * freq * 2 * t)
        note = np.asarray(tone * envelope * gain, dtype=np.float32)
        music[left : left + count, 0] += note * math.cos((pan + 1) * np.pi / 4)
        music[left : left + count, 1] += note * math.sin((pan + 1) * np.pi / 4)

    for index, start in enumerate(np.arange(0, duration, bar * 2)):
        chord = chords[index % len(chords)]
        for j, midi in enumerate(chord):
            add_note(float(start), bar * 2.25, midi, 0.105, (j - 2) / 3, True)
        for j in (0, 3, 5, 7):
            midi = chord[int(rng.integers(1, len(chord)))] + 12
            add_note(
                float(start + j * beat),
                beat * 3.2,
                midi,
                0.14,
                float(rng.uniform(-0.65, 0.65)),
                False,
            )
    # Airy transition pings, keyed to cuts, not a constant percussion loop.
    for item in data["scenes"]:
        at = item["from"] / episode.fps
        add_note(at + 0.08, 1.8, 74, cfg.transition_gain, -0.35, False)
        add_note(at + 0.28, 1.6, 81, cfg.transition_gain * 0.55, 0.35, False)
    # A deterministic scene envelope ducks the music during all speech.
    envelope = np.full(n, cfg.music_gain, dtype=np.float32)
    for item in data["scenes"]:
        start = round((item["from"] + item["lead"]) / episode.fps * sr)
        end = min(n, start + round(item["speechFrames"] / episode.fps * sr))
        ramp = min(round(0.4 * sr), start)
        envelope[start - ramp : start] = np.linspace(cfg.music_gain, cfg.ducked_gain, ramp)
        envelope[start:end] = cfg.ducked_gain
        ramp_end = min(n, end + round(0.8 * sr))
        envelope[end:ramp_end] = np.linspace(cfg.ducked_gain, cfg.music_gain, ramp_end - end)
    fade = min(round(sr * 5), n)
    envelope[:fade] *= np.linspace(0, 1, fade)
    envelope[-fade:] *= np.linspace(1, 0, fade)
    music *= envelope[:, None]
    dest = PUBLIC / "score.wav"
    wavfile.write(dest, sr, (np.clip(music, -1, 1) * 32767).astype(np.int16))
    run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(dest),
            "-codec:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(PUBLIC / "score.mp3"),
        ]
    )
    save_json(
        PRODUCTION / "score.json",
        {
            "type": "original_procedural_composition",
            "seed": cfg.seed,
            "sample_rate": sr,
            "duration_seconds": duration,
            "peak_dbfs": float(20 * np.log10(np.max(np.abs(music)))),
            "sha256": sha(dest),
            "sampled_third_party_music": False,
        },
    )
    print(f"Original stereo score: {duration:.2f}s, {dest.stat().st_size} bytes")


def main() -> None:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["estimate", "tts", "prepare", "sound"])
    parser.add_argument("--scene")
    args = parser.parse_args()
    episode = load()
    settings = Settings()
    if args.command == "estimate":
        estimate(episode, settings)
    elif args.command == "tts":
        tts(episode, settings, args.scene)
    elif args.command == "prepare":
        prepare(episode)
    else:
        sound(episode)


if __name__ == "__main__":
    main()
