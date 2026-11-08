"""Install the versioned research video skills into the user's Codex skill folder.

Default refuses existing folders. --update replaces only these named skills,
after saving a versioned backup; never removes unrelated skills.
"""

from __future__ import annotations

import argparse
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path


def install(destination: Path, update: bool) -> list[Path]:
    source = Path(__file__).resolve().parent
    names = ["research-video", "research-video-review"]
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    if not update and any((destination / name).exists() for name in names):
        raise FileExistsError(
            "A skill already exists; inspect it, then use --update if replacement is intended"
        )
    installed = []
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    for name in names:
        src, target = source / name, destination / name
        if src.resolve() == target.resolve():
            raise ValueError("Source and install destination are identical")
        if target.exists():
            if target.is_symlink() or target.resolve().parent != destination:
                raise ValueError("Refusing to move a linked or out-of-scope skill directory")
            backup = destination.parent / "skill-backups" / f"{name}-{stamp}"
            if not backup.resolve().is_relative_to(
                (destination.parent / "skill-backups").resolve()
            ):
                raise ValueError("Backup escaped the intended skill-backups directory")
            backup.parent.mkdir(parents=True, exist_ok=True)
            target.rename(backup)
        shutil.copytree(
            src, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "node_modules")
        )
        installed.append(target)
    return installed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "skills",
    )
    parser.add_argument("--update", action="store_true")
    args = parser.parse_args()
    for path in install(args.destination, args.update):
        print(path)


if __name__ == "__main__":
    main()
