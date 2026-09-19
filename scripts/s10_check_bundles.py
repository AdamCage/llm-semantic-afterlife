"""Scan stage-10 artifact metas for missing data / captions / limitations."""

from __future__ import annotations

import json
from pathlib import Path

root = Path("artifacts/stage-10")
problems: list[str] = []
n = 0
for meta_path in sorted(root.rglob("*.meta.json")):
    n += 1
    base = meta_path.with_name(meta_path.name.removesuffix(".meta.json"))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    has_data = any(
        base.with_suffix(suffix).is_file() or Path(f"{base}.data{suffix}").is_file()
        for suffix in (".parquet", ".npz", ".csv")
    )
    if not has_data:
        problems.append(f"{base.relative_to(root)}: no source data")
    if not str(meta.get("caption") or "").strip():
        problems.append(f"{base.relative_to(root)}: no caption")
    if not str(meta.get("limitations") or "").strip():
        problems.append(f"{base.relative_to(root)}: no limitations")
print(f"metas={n} problems={len(problems)}")
for p in problems:
    print(p)
