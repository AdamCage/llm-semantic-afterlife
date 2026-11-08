"""Exercise the portable toolchain offline from research/TTS accounts.

Produces labelled DEMO video with synthetic tones, not spoken scientific results.
Downloads npm dependencies unless --skip-install. Never calls paid TTS or GitHub.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from video import bundle, init, load, master, music, prepare, run, validate, write


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--skip-install", action="store_true")
    args = parser.parse_args()
    project = args.project.resolve()
    if not (project / "episode.json").exists():
        init(project)
    cfg = load(project)
    if (project / "record/master.json").exists() and not cfg.get("smoke_test"):
        raise ValueError("Refusing to replace a real completed production")
    if (project / "media/voice").exists() and not cfg.get("smoke_test"):
        raise ValueError("Refusing to replace real voice assets")
    cfg["smoke_test"] = True
    cfg["title"] = "OFFLINE TOOLCHAIN DEMO — synthetic tones, not narration"
    cfg["production_id"] = "offline-smoke-test"
    write(project / "episode.json", cfg)
    voice = project / "media/voice"
    voice.mkdir(parents=True, exist_ok=True)
    for index, scene in enumerate(cfg["scenes"]):
        run(
            [
                "ffmpeg",
                "-v",
                "error",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency={220 + index * 110}:duration=1.2:sample_rate=48000",
                "-c:a",
                "libmp3lame",
                "-b:a",
                "128k",
                str(voice / f"{scene['id']}.mp3"),
            ]
        )
    validate(project)
    prepare(project, False)
    music(project)
    (project / "output/subtitles.srt").write_bytes(
        b"1\n00:00:00,700 --> 00:00:01,700\nOFFLINE DEMO - synthetic tones\n"
    )
    npm = shutil.which("npm")
    if not npm:
        raise FileNotFoundError("npm not found")
    renderer = project / "renderer"
    if not args.skip_install:
        subprocess.run([npm, "install", "--no-fund", "--no-audit"], cwd=renderer, check=True)
    subprocess.run([npm, "run", "check"], cwd=renderer, check=True)
    subprocess.run([npm, "run", "render", "--", "--log=error"], cwd=renderer, check=True)
    print(master(project))
    print(bundle(project))
    print("SMOKE TEST PASSED: no paid API, no public upload; synthetic tone fixture only")


if __name__ == "__main__":
    main()
