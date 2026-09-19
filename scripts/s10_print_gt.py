"""Print last-band G_t and lock counts for completed S10 persistence runs."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path("runs/s10")
for persist in sorted(ROOT.glob("s10-persistence-*")):
    if (persist / "SUPERSEDED").is_file():
        continue
    status = (persist / "STATUS").read_text(encoding="utf-8").strip() if (persist / "STATUS").is_file() else "?"
    gt_path = persist / "data" / "persistence_gt.parquet"
    if not gt_path.is_file():
        print(f"{status}\t{persist.name}\tNO_GT")
        continue
    man = json.loads((persist / "manifest.json").read_text(encoding="utf-8"))
    src = (man.get("config_resolved") or {}).get("source_run_id", "")
    last = pd.read_parquet(gt_path).iloc[-1]
    locks_path = persist / "data" / "persistence_locks.parquet"
    n_lock = n_esc = n = 0
    if locks_path.is_file():
        locks = pd.read_parquet(locks_path)
        n = len(locks)
        n_lock = int(locks["confirmed_lock"].sum())
        n_esc = int(locks["confirmed_escape"].sum())
    print(
        f"{status}\t{persist.name}\tsrc={src}\t"
        f"G={float(last['G']):.4f} [{float(last['G_lo']):.4f},{float(last['G_hi']):.4f}] "
        f"lock={n_lock}/{n} esc={n_esc}"
    )
