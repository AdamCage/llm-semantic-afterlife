"""List S11 generate runs and STATUS. No generate."""

from __future__ import annotations

from pathlib import Path

ROOT = Path("runs/s11")
if not ROOT.is_dir():
    print("NO_RUNS")
    raise SystemExit(0)
for run_dir in sorted(ROOT.glob("s11-paperb-*")):
    if not run_dir.is_dir():
        continue
    status = (
        (run_dir / "STATUS").read_text(encoding="utf-8").strip()
        if (run_dir / "STATUS").is_file()
        else "NOSTATUS"
    )
    superseded = (run_dir / "SUPERSEDED").is_file()
    flag = " SUPERSEDED" if superseded else ""
    print(f"{status}{flag}\t{run_dir.name}")
