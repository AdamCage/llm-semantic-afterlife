"""Portable research-video production. Python 3.11+, FFmpeg; numpy for music only.

No dependency on the source research repository. Run --help for commands.
All paths are resolved from --project, never from the shell working directory.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
    )


def sha(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    # A corrupt accounting log is an error, never silently skipped.
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def append(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab") as handle:
        handle.write((json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n").encode())
        handle.flush()
        os.fsync(handle.fileno())


def inside(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes its configured root: {relative}")
    return path


def run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args, cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8"
    )


def ffprobe(path: Path) -> dict[str, Any]:
    return json.loads(
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
                str(path),
            ]
        ).stdout
    )


def load(project: Path) -> dict[str, Any]:
    config = read(project / "episode.json")
    if config.get("schema_version") != 1:
        raise ValueError("Expected episode.json schema_version=1")
    if not config.get("production_id") or not re.fullmatch(
        r"[a-zA-Z0-9_-]+", config["production_id"]
    ):
        raise ValueError("production_id must be a stable filename-safe ID")
    for key in ("fps", "width", "height"):
        if not isinstance(config.get(key), int) or config[key] <= 0:
            raise ValueError(f"{key} must be a positive integer")
    if not config.get("scenes"):
        raise ValueError("At least one scene is required")
    ids: set[str] = set()
    for scene in config["scenes"]:
        sid = scene.get("id", "")
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", sid) or sid in ids:
            raise ValueError(f"Unsafe or duplicate scene ID: {sid}")
        ids.add(sid)
        if not scene.get("title") or not scene.get("narration", "").strip():
            raise ValueError(f"Scene {sid} needs a title and narration")
        if scene.get("visual") not in {"title", "cards", "figure", "image", "quote", "process"}:
            raise ValueError(f"Unknown visual in scene {sid}")
    return config


def validate(project: Path) -> dict[str, Any]:
    cfg = load(project)
    root = (project / cfg["research_root"]).resolve()
    evidence = read(project / "evidence.json")
    sources: dict[str, Any] = {}
    source_hashes: dict[str, str] = {}
    for item in evidence["sources"]:
        if item["id"] in sources:
            raise ValueError("Duplicate evidence source ID")
        path = inside(root, item["path"])
        if not path.is_file() or not item.get("locator"):
            raise ValueError(f"Evidence needs a real file and exact locator: {item['id']}")
        if item.get("status") != "verified":
            raise ValueError(f"Unverified source: {item['id']}")
        sources[item["id"]] = item
        source_hashes[item["id"]] = sha(path)
    claims: dict[str, Any] = {}
    for claim in evidence["claims"]:
        if claim["id"] in claims or claim.get("kind") not in {
            "empirical",
            "interpretation",
            "practical",
            "explanation",
        }:
            raise ValueError("Duplicate claim ID or invalid claim kind")
        if not claim.get("statement") or not claim.get("limitations"):
            raise ValueError(f"Claim {claim['id']} needs a statement and limitations")
        refs = claim.get("sources", [])
        if not refs or any(ref not in sources for ref in refs):
            raise ValueError(f"Claim {claim['id']} has missing evidence")
        if (
            claim["kind"] == "empirical"
            and cfg.get("require_run_ids")
            and not all(sources[ref].get("run_ids") for ref in refs)
        ):
            raise ValueError(f"Empirical claim {claim['id']} requires run IDs")
        if claim["kind"] == "practical" and not isinstance(claim.get("tested_in_this_study"), bool):
            raise ValueError("Practical claims must state tested_in_this_study explicitly")
        claims[claim["id"]] = claim
    for scene in cfg["scenes"]:
        refs = scene.get("claim_ids", [])
        if not refs or any(ref not in claims for ref in refs):
            raise ValueError(f"Scene {scene['id']} has no valid claim map")
        if (
            scene["visual"] in {"figure", "image"}
            and not inside(project, scene.get("asset", "")).is_file()
        ):
            raise ValueError(f"Scene {scene['id']} needs an actual asset")
        if scene["visual"] == "figure":
            if (
                not scene.get("caption")
                or not scene.get("limitations")
                or not scene.get("data_sources")
            ):
                raise ValueError("Figures need caption, limitations and tidy-data source IDs")
            if any(s not in sources for s in scene["data_sources"]):
                raise ValueError("Figure data source is missing")
        if scene["visual"] == "image" and scene.get("asset_origin") not in {
            "ai",
            "licensed",
            "original",
        }:
            raise ValueError("Images need asset_origin: ai, licensed or original")
    result = {
        "mechanical_validation": "pass",
        "scientific_judgment": "not_performed",
        "source_hashes": source_hashes,
        "claims": len(claims),
        "scenes": len(cfg["scenes"]),
    }
    write(project / "record/validation.json", result)
    return result


def init(project: Path) -> None:
    if project.exists() and any(project.iterdir()):
        raise ValueError("init refuses a nonempty directory")
    project.mkdir(parents=True, exist_ok=True)
    assets = Path(__file__).resolve().parents[1] / "assets"
    shutil.copytree(assets / "starter", project, dirs_exist_ok=True)
    shutil.copytree(assets / "renderer", project / "renderer", dirs_exist_ok=True)
    print(f"Created portable project: {project}")


def price(cfg: dict[str, Any]) -> float:
    speech = cfg["speech"]
    url = speech["base_url"].rstrip("/")
    parsed = urllib.parse.urlsplit(url)
    if (
        speech.get("provider") != "routerai"
        or parsed.scheme != "https"
        or parsed.hostname != "routerai.ru"
        or parsed.port not in {None, 443}
        or parsed.username
        or parsed.password
        or parsed.path != "/api/v1"
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "This adapter sends credentials only to the official RouterAI HTTPS API; adapt explicitly for another provider"
        )
    with urllib.request.urlopen(url + "/models", timeout=30) as response:
        models = json.load(response)["data"]
    model = next(m for m in models if m["id"] == speech["model"])
    if speech.get("pricing_unit") != "rub_per_character":
        raise ValueError(
            "This adapter requires verified RUB-per-character pricing, not token pricing"
        )
    rate = float(model["pricing"]["prompt"])
    if not math.isfinite(rate) or rate <= 0:
        raise ValueError("Invalid catalog price")
    if rate > float(speech["max_rub_per_character"]):
        raise ValueError("Catalog rate exceeds configured maximum; review price and estimate")
    return rate


def budget_paths(project: Path, cfg: dict[str, Any]) -> tuple[Path, float, float, float]:
    budget = cfg["budget"]
    ledger = (project / budget["ledger_path"]).resolve()
    research_root = (project / cfg["research_root"]).resolve()
    host_ledger = (
        research_root / os.environ.get("AFTERLIFE_RUNS_DIR", "runs") / "_ledger/spend.jsonl"
    )
    if host_ledger.exists() and ledger != host_ledger.resolve():
        raise ValueError(
            "An existing research spend ledger was found; configure that ledger instead of bypassing it"
        )
    production = float(budget["production_usd"])
    per_run = min(
        float(budget["per_run_usd"]), float(os.environ.get("AFTERLIFE_BUDGET_USD_PER_RUN", "inf"))
    )
    total = min(
        float(budget["project_usd"]), float(os.environ.get("AFTERLIFE_BUDGET_USD_TOTAL", "inf"))
    )
    if not all(math.isfinite(x) and x > 0 for x in [production, per_run, total]):
        raise ValueError(
            "Configure finite positive authorised production, per-run and project budgets"
        )
    return ledger, production, per_run, total


def estimate(project: Path) -> dict[str, Any]:
    validate(project)
    cfg = load(project)
    rate = price(cfg)
    ledger, production, per_run, total = budget_paths(project, cfg)
    entries = jsonl(ledger)
    spend = sum(float(x.get("cost_usd", 0)) for x in entries)
    current = sum(
        float(x.get("cost_usd", 0)) for x in entries if x.get("run_id") == cfg["production_id"]
    )
    chars = sum(len(s["narration"]) for s in cfg["scenes"])
    rub = chars * rate
    conversion = float(cfg["speech"]["usd_per_rub"])
    if not math.isfinite(conversion) or conversion <= 0:
        raise ValueError("Set an explicit current positive RUB-to-USD accounting conversion")
    result = {
        "episode_sha256": sha(project / "episode.json"),
        "evidence_sha256": sha(project / "evidence.json"),
        "model": cfg["speech"]["model"],
        "rate_rub_per_character": rate,
        "characters": chars,
        "estimate_rub_all_scenes": rub,
        "estimate_usd_all_scenes": rub * conversion,
        "project_spend_usd": spend,
        "this_production_spend_usd": current,
        "remaining_project_usd": total - spend,
        "production_cap_usd": production,
        "per_run_cap_usd": per_run,
        "project_cap_usd": total,
        "estimated_at_unix": time.time(),
    }
    write(project / "record/estimate.json", result)
    return result


@contextlib.contextmanager
def locked(ledger: Path) -> Iterator[None]:
    ledger.parent.mkdir(parents=True, exist_ok=True)
    lock = ledger.with_suffix(ledger.suffix + ".media-lock")
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.write(fd, f"pid={os.getpid()}".encode())
        os.close(fd)
        yield
    finally:
        lock.unlink()


def request_body(cfg: dict[str, Any], scene: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": cfg["speech"]["model"],
        "voice": cfg["speech"]["voice"],
        "input": scene["narration"],
        "response_format": "mp3",
    }


def tts(project: Path, only: str | None) -> None:
    validate(project)
    cfg = load(project)
    previous = read(project / "record/estimate.json")
    if previous["episode_sha256"] != sha(project / "episode.json") or previous[
        "evidence_sha256"
    ] != sha(project / "evidence.json"):
        raise ValueError("Inputs changed since estimate; estimate again")
    if time.time() - previous["estimated_at_unix"] > 86400:
        raise ValueError("Estimate older than 24 hours; refresh it")
    rate = price(cfg)
    if rate > previous["rate_rub_per_character"]:
        raise ValueError("Price increased since estimate")
    key = os.environ.get(cfg["speech"]["api_key_env"])
    if not key:
        raise ValueError(
            "Configure the named API-key environment variable; never paste it into source"
        )
    ledger, production, per_run, total = budget_paths(project, cfg)
    scenes = cfg["scenes"]
    if only and only not in {s["id"] for s in scenes}:
        raise ValueError("Unknown --scene")
    for scene in scenes:
        sid = scene["id"]
        if only and sid != only:
            continue
        body = request_body(cfg, scene)
        request_sha = hashlib.sha256(
            json.dumps(body, sort_keys=True, ensure_ascii=False).encode()
        ).hexdigest()
        output = project / "media/voice" / f"{sid}.mp3"
        receipt_path = project / "record/voice" / f"{sid}.json"
        pending = project / "record/pending" / f"{sid}.json"
        if receipt_path.exists():
            receipt = read(receipt_path)
            if (
                output.exists()
                and receipt["request_sha256"] == request_sha
                and receipt["audio_sha256"] == sha(output)
            ):
                print(f"{sid}: verified cache", flush=True)
                continue
            raise ValueError(
                f"Scene {sid} changed or cache damaged: use a new version/production ID"
            )
        if pending.exists():
            raise ValueError(f"Unresolved paid attempt for {sid}; reconcile before retrying")
        rub = len(scene["narration"]) * rate
        usd = rub * cfg["speech"]["usd_per_rub"]
        # Book a conservative estimated charge BEFORE sending. It remains
        # counted after timeouts or crashes; no automatic retries/unreserving.
        with locked(ledger):
            if pending.exists() or receipt_path.exists():
                raise ValueError(
                    "Another worker already started/completed this scene; inspect state before continuing"
                )
            entries = jsonl(ledger)
            spent = sum(float(x.get("cost_usd", 0)) for x in entries)
            ours = sum(
                float(x.get("cost_usd", 0))
                for x in entries
                if x.get("run_id") == cfg["production_id"]
            )
            if ours + usd > min(production, per_run) or spent + usd > total:
                raise ValueError("Budget ceiling would be exceeded")
            attempt = uuid.uuid4().hex
            write(
                pending,
                {
                    "attempt_id": attempt,
                    "body": body,
                    "request_sha256": request_sha,
                    "estimated_rub": rub,
                    "estimated_usd": usd,
                    "timestamp": time.time(),
                },
            )
            append(
                ledger,
                {
                    "ts": time.time(),
                    "run_id": cfg["production_id"],
                    "kind": "media_tts_estimate",
                    "attempt_id": attempt,
                    "scene_id": sid,
                    "cost_usd": usd,
                    "cost_rub": rub,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "n_characters": len(scene["narration"]),
                    "accounting_basis": "conservative_catalog_estimate_booked_before_request",
                },
            )
        request = urllib.request.Request(
            cfg["speech"]["base_url"].rstrip("/") + "/audio/speech",
            data=json.dumps(body, ensure_ascii=False).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(
                request, timeout=cfg["speech"]["timeout_seconds"]
            ) as response:
                audio = response.read()
                headers = {
                    k.lower(): v
                    for k, v in response.headers.items()
                    if k.lower()
                    in {"content-type", "x-generation-id", "x-request-id", "content-length"}
                }
        except urllib.error.HTTPError as error:
            write(
                project / "record/errors" / f"{attempt}.json",
                {
                    "status": error.code,
                    "body": error.read().decode(errors="replace").replace(key, "[REDACTED]"),
                },
            )
            raise
        if not audio or (
            "audio" not in headers.get("content-type", "")
            and not audio.startswith((b"ID3", b"\xff"))
        ):
            raise ValueError("Response is not audio; pending attempt retained for reconciliation")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(audio)
        # Validate decoding before considering the cached response complete.
        ffprobe(output)
        receipt = {
            "scene_id": sid,
            "attempt_id": attempt,
            "request_sha256": request_sha,
            "audio_sha256": sha(output),
            "catalog_estimate_rub": rub,
            "catalog_estimate_usd": usd,
            "headers": headers,
            "billing_status": "catalog_estimate_not_provider_invoice",
        }
        write(receipt_path, receipt)
        append(project / "record/events.jsonl", {"event": "tts_completed", **receipt})
        pending.rename(project / "record/pending" / f"{sid}.completed.json")
        print(f"{sid}: cached {len(audio)} bytes; catalog estimate {rub:.3f} RUB", flush=True)


def prepare(project: Path, storyboard: bool) -> dict[str, Any]:
    validation = validate(project)
    cfg = load(project)
    public = project / "renderer/public"
    public.mkdir(exist_ok=True, parents=True)
    cursor = 0
    timeline = []
    script = [f"# {cfg['title']}\n"]
    hashes = {
        "episode.json": sha(project / "episode.json"),
        "evidence.json": sha(project / "evidence.json"),
    }
    for scene in cfg["scenes"]:
        voice = project / "media/voice" / f"{scene['id']}.mp3"
        ready = voice.is_file()
        if not ready and not storyboard:
            raise ValueError(
                f"Missing narration: {scene['id']}; --storyboard is explicitly non-final"
            )
        seconds = (
            float(ffprobe(voice)["format"]["duration"])
            if ready
            else len(scene["narration"].split()) / cfg["storyboard_words_per_second"]
        )
        lead = round(cfg["scene_lead_seconds"] * cfg["fps"])
        speech = math.ceil(seconds * cfg["fps"])
        length = lead + speech + round(cfg["scene_tail_seconds"] * cfg["fps"])
        item = {
            **scene,
            "from": cursor,
            "duration": length,
            "lead": lead,
            "speech_frames": speech,
            "voice_ready": ready,
        }
        if ready:
            target = public / "voice" / voice.name
            target.parent.mkdir(exist_ok=True)
            shutil.copyfile(voice, target)
            hashes[voice.relative_to(project).as_posix()] = sha(voice)
        if scene.get("asset"):
            path = inside(project, scene["asset"])
            filename = f"{scene['id']}{path.suffix.lower()}"
            (public / "visuals").mkdir(exist_ok=True)
            shutil.copyfile(path, public / "visuals" / filename)
            item["render_asset"] = "visuals/" + filename
            hashes[scene["asset"]] = sha(path)
        timeline.append(item)
        script += [
            f"## {scene['id']}. {scene['title']}\n",
            scene["narration"] + "\n",
            "Claim IDs: " + ", ".join(scene["claim_ids"]) + "\n",
        ]
        cursor += length
    data = {
        **cfg,
        "duration": cursor,
        "scenes": timeline,
        "storyboard": storyboard or not all(s["voice_ready"] for s in timeline),
    }
    write(project / "renderer/src/episode.generated.json", data)
    write(
        project / "record/build-inputs.json",
        {
            "project_hashes": hashes,
            "evidence_source_hashes": validation["source_hashes"],
            "duration_frames": cursor,
            "storyboard": data["storyboard"],
        },
    )
    (project / "SCRIPT.md").write_bytes(("\n".join(script)).encode())
    return {
        "duration_seconds": cursor / cfg["fps"],
        "scenes": len(timeline),
        "storyboard": data["storyboard"],
    }


def music(project: Path) -> None:
    import wave

    import numpy as np

    cfg = load(project)
    timeline = read(project / "renderer/src/episode.generated.json")
    settings = cfg["music"]
    sr = settings["sample_rate"]
    seconds = timeline["duration"] / cfg["fps"]
    samples = math.ceil(seconds * sr)
    score = np.zeros((samples, 2), dtype=np.float32)
    rng = np.random.default_rng(settings["seed"])
    beat = 60 / settings["bpm"]

    def note(start: float, duration: float, midi: int, gain: float, pan: float, pad: bool) -> None:
        left = round(start * sr)
        count = min(round(duration * sr), samples - left)
        if count <= 0:
            return
        t = np.arange(count, dtype=np.float32) / sr
        frequency = 440 * 2 ** ((midi - 69) / 12)
        envelope = (
            np.sin(np.pi * t / duration) ** 2 if pad else (1 - np.exp(-32 * t)) * np.exp(-1.5 * t)
        )
        tone = np.sin(2 * np.pi * frequency * t) + 0.18 * np.sin(4 * np.pi * frequency * t)
        signal = np.asarray(gain * tone * envelope, dtype=np.float32)
        score[left : left + count, 0] += signal * math.cos((pan + 1) * math.pi / 4)
        score[left : left + count, 1] += signal * math.sin((pan + 1) * math.pi / 4)

    for index, start in enumerate(np.arange(0, seconds, 8 * beat)):
        chord = settings["chords_midi"][index % len(settings["chords_midi"])]
        for j, midi in enumerate(chord):
            note(float(start), 9 * beat, midi, 0.1, (j / max(1, len(chord) - 1) - 0.5) * 1.3, True)
        for step in [0, 3, 5, 7]:
            note(
                float(start + step * beat),
                beat * 3,
                int(rng.choice(chord)) + 12,
                0.14,
                float(rng.uniform(-0.6, 0.6)),
                False,
            )
    gain = np.full(samples, settings["gap_gain"], dtype=np.float32)
    for scene in timeline["scenes"]:
        at = scene["from"] / cfg["fps"]
        note(at + 0.08, 1.8, 74, settings["transition_gain"], -0.3, False)
        start = round((scene["from"] + scene["lead"]) / cfg["fps"] * sr)
        end = min(samples, start + round(scene["speech_frames"] / cfg["fps"] * sr))
        before = max(0, start - round(0.4 * sr))
        after = min(samples, end + round(0.8 * sr))
        gain[before:start] = np.linspace(
            settings["gap_gain"], settings["speech_gain"], start - before
        )
        gain[start:end] = settings["speech_gain"]
        gain[end:after] = np.linspace(settings["speech_gain"], settings["gap_gain"], after - end)
    fade = min(round(sr * settings["fade_seconds"]), samples)
    gain[:fade] *= np.linspace(0, 1, fade)
    gain[-fade:] *= np.linspace(1, 0, fade)
    score *= gain[:, None]
    raw = project / "output/score.wav"
    raw.parent.mkdir(exist_ok=True)
    with wave.open(str(raw), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sr)
        handle.writeframes((np.clip(score, -1, 1) * 32767).astype("<i2").tobytes())
    target = project / "renderer/public/score.mp3"
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(raw),
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(target),
        ]
    )
    write(
        project / "record/music.json",
        {
            "origin": "original_procedural",
            "seed": settings["seed"],
            "third_party_samples": False,
            "sha256": sha(target),
        },
    )


def master(project: Path) -> dict[str, Any]:
    validate(project)
    cfg = load(project)
    timeline = read(project / "renderer/src/episode.generated.json")
    inputs = read(project / "record/build-inputs.json")
    if timeline["storyboard"]:
        raise ValueError("Cannot master a storyboard as a final release")
    for relative, expected in inputs["project_hashes"].items():
        if sha(inside(project, relative)) != expected:
            raise ValueError(f"Build input changed: {relative}; prepare/render again")
    if validate(project)["source_hashes"] != inputs["evidence_source_hashes"]:
        raise ValueError("Research evidence changed since preparation")
    original = project / "output/raw.mp4"
    output = project / "output/video.mp4"
    levels = cfg["mastering"]
    target = f"loudnorm=I={levels['lufs']}:TP={levels['true_peak']}:LRA={levels['lra']}"
    measured = run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(original),
            "-vn",
            "-af",
            target + ":print_format=json",
            "-f",
            "null",
            os.devnull,
        ]
    )
    loud = json.JSONDecoder().raw_decode(measured.stderr[measured.stderr.rfind("{\n") :])[0]
    settings = (
        target
        + f":linear=true:measured_I={loud['input_i']}:measured_TP={loud['input_tp']}:measured_LRA={loud['input_lra']}:measured_thresh={loud['input_thresh']}:offset={loud['target_offset']}"
    )
    chapter_lines = [";FFMETADATA1", "title=" + cfg["title"].replace("=", "\\=").replace("\n", " ")]
    for scene in timeline["scenes"]:
        chapter_lines += [
            "[CHAPTER]",
            "TIMEBASE=1/1000",
            f"START={round(scene['from'] / cfg['fps'] * 1000)}",
            f"END={round((scene['from'] + scene['duration']) / cfg['fps'] * 1000)}",
            "title=" + scene["title"].replace("=", "\\=").replace("\n", " "),
        ]
    chapters = project / "output/chapters.ffmetadata"
    chapters.write_bytes(("\n".join(chapter_lines) + "\n").encode())
    args = [
        "ffmpeg",
        "-v",
        "error",
        "-y",
        "-i",
        str(original),
        "-f",
        "ffmetadata",
        "-i",
        str(chapters),
    ]
    subtitle = project / "output/subtitles.srt"
    if subtitle.exists():
        args += ["-i", str(subtitle)]
    args += [
        "-map",
        "0:v:0",
        "-map",
        "0:a:0",
        "-map_metadata",
        "1",
        "-map_chapters",
        "1",
        "-c:v",
        "copy",
        "-af",
        settings,
        "-ar",
        "48000",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
    ]
    if subtitle.exists():
        args += [
            "-map",
            "2:0",
            "-c:s",
            "mov_text",
            "-metadata:s:s:0",
            "language=" + cfg["subtitle_language"],
        ]
    args += ["-movflags", "+faststart", str(output)]
    run(args)
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-y",
            "-i",
            str(output),
            "-vn",
            "-c:a",
            "libmp3lame",
            "-b:a",
            "192k",
            str(project / "output/audio.mp3"),
        ]
    )
    run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(output),
            "-map",
            "0:v",
            "-map",
            "0:a",
            "-f",
            "null",
            os.devnull,
        ]
    )
    probe = ffprobe(output)
    video = next(s for s in probe["streams"] if s["codec_type"] == "video")
    if (
        int(video["nb_frames"]) != timeline["duration"]
        or abs(float(probe["format"]["duration"]) - timeline["duration"] / cfg["fps"]) > 0.12
    ):
        raise ValueError("Final frame count or duration mismatch")
    check = run(
        [
            "ffmpeg",
            "-hide_banner",
            "-i",
            str(output),
            "-vn",
            "-af",
            target + ":print_format=json",
            "-f",
            "null",
            os.devnull,
        ]
    )
    after = json.JSONDecoder().raw_decode(check.stderr[check.stderr.rfind("{\n") :])[0]
    if (
        abs(float(after["input_i"]) - levels["lufs"]) > 1
        or float(after["input_tp"]) > levels["true_peak"] + 0.5
    ):
        raise ValueError("Encoded loudness/true peak outside tolerance")
    if len(probe.get("chapters", [])) != len(timeline["scenes"]):
        raise ValueError("Missing chapters")
    write(project / "record/ffprobe.json", probe)
    write(project / "record/loudness.json", after)
    manifest = {
        "production_id": cfg["production_id"],
        "smoke_test": bool(cfg.get("smoke_test", False)),
        "full_decode": "pass",
        "input_integrity": "pass",
        "duration_seconds": timeline["duration"] / cfg["fps"],
        "chapters": len(probe["chapters"]),
        "has_subtitles": subtitle.exists(),
        "loudness": after,
        "scientific_review": "not_established_by_this_script",
    }
    write(project / "record/master.json", manifest)
    return manifest


def bundle(project: Path) -> dict[str, Any]:
    cfg = load(project)
    read(project / "record/master.json")
    output = project / "output"
    with zipfile.ZipFile(
        output / "media-assets.zip", "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        for folder in [project / "media", project / "record"]:
            if folder.exists():
                for path in sorted(folder.rglob("*")):
                    if path.is_file() and not path.name.endswith(".lock"):
                        archive.write(path, path.relative_to(project).as_posix())
        archive.write(project / "renderer/public/score.mp3", "renderer/public/score.mp3")
        for path in [project / "episode.json", project / "evidence.json"]:
            archive.write(path, path.name)
    deliverables = [output / "video.mp4", output / "audio.mp3", output / "media-assets.zip"]
    for filename in ["subtitles.srt", "subtitles.vtt"]:
        if (output / filename).exists():
            deliverables.append(output / filename)
    values = {p.name: {"bytes": p.stat().st_size, "sha256": sha(p)} for p in deliverables}
    write(project / "record/deliverables.json", values)
    (output / "SHA256SUMS").write_bytes(
        "".join(f"{v['sha256']}  {k}\n" for k, v in values.items()).encode()
    )
    print(f"Bundled {cfg['production_id']}")
    return values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=["init", "validate", "estimate", "tts", "prepare", "music", "master", "bundle"],
    )
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--scene")
    parser.add_argument("--storyboard", action="store_true")
    args = parser.parse_args()
    project = args.project.resolve()
    operations = {
        "init": lambda: init(project),
        "validate": lambda: validate(project),
        "estimate": lambda: estimate(project),
        "tts": lambda: tts(project, args.scene),
        "prepare": lambda: prepare(project, args.storyboard),
        "music": lambda: music(project),
        "master": lambda: master(project),
        "bundle": lambda: bundle(project),
    }
    result = operations[args.command]()
    if result is not None:
        print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
