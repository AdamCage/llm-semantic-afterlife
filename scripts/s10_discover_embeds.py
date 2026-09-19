"""List S10 embed run_ids whose source_run_id is a generate run."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path("runs/s10")
SOURCES = {
    "s10-paperb-olmo-base-nf4-20260916T204957Z-6d7b4be3",
    "s10-paperb-olmo-sft-nf4-20260917T142201Z-2b7b5b6e",
    "s10-paperb-olmo-dpo-nf4-20260918T000412Z-64ad9f9f",
    "s10-paperb-olmo-rlvr-nf4-20260918T022536Z-30b5b3fc",
    "s10-paperb-olmo-base-int8-20260918T050048Z-2b2cdfd8",
    "s10-paperb-olmo-rlvr-int8-20260918T142301Z-7125ccca",
}


def _source(manifest: dict) -> str:
    resolved = manifest.get("config_resolved") or {}
    totals = manifest.get("totals") or {}
    return str(resolved.get("source_run_id") or totals.get("source_run_id") or "")


def main() -> None:
    rows: list[tuple[str, str, str, str]] = []
    for path in sorted(ROOT.glob("s10-embed-*/manifest.json")):
        if (path.parent / "SUPERSEDED").is_file():
            continue
        manifest = json.loads(path.read_text(encoding="utf-8"))
        source = _source(manifest)
        if source not in SOURCES:
            continue
        status = (path.parent / "STATUS").read_text(encoding="utf-8").strip()
        embeddings = list((path.parent / "data").glob("embeddings_*.parquet"))
        space = embeddings[0].stem.removeprefix("embeddings_") if embeddings else "none"
        rows.append((source, path.parent.name, status, space))
    wanted = sys.argv[1:] if len(sys.argv) > 1 else []
    for source, run_id, status, space in rows:
        if wanted and space not in wanted and source not in wanted:
            continue
        print(f"{status}\t{space}\t{source}\t{run_id}")


if __name__ == "__main__":
    main()
