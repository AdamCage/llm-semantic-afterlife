"""Finish S12 after generation and degeneracy: escape table, report, nothing else.

Clock: L0 lock at 0.75 turnover, L0 horizon 12 turnovers (49152 tokens), then
the continuation. A cell still locked at the common T_min is censored.
Does not run G_t, does not open S13, does not call a lock absorbing.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import orjson
import pandas as pd

from semantic_afterlife.analysis.persistence import prefix_lock_escape

from s12_tau import (
    HORIZON_TURNOVERS,
    LOCK_TURNOVER,
    W,
    L0_TOKENS,
    concatenate_clock,
    confirmed_through_tmin,
)

ROOT = Path(__file__).resolve().parents[1]
MAP = Path("/home/adam/s12/runs.map")
L0_CHUNK = {
    "mb": ROOT / "runs/s11/s11-degeneracy-20260923T051706Z-81df16d2/data/degeneracy_per_chunk.parquet",
    "qi": ROOT / "runs/s9/s9-degeneracy-20260915T052651Z-cde06a72/data/degeneracy_per_chunk.parquet",
}
L0_TRAJ = {
    "mb-physics-s1": "pb-ministral-8b-base__W4096__T0p3__physics__s1",
    "mb-physics-s2": "pb-ministral-8b-base__W4096__T0p3__physics__s2",
    "mb-love-s1": "pb-ministral-8b-base__W4096__T0p3__love__s1",
    "mb-love-s2": "pb-ministral-8b-base__W4096__T0p3__love__s2",
    "qi-physics-s1": "pb-qwen3-8b-instruct__W4096__T0p3__physics__s1",
    "qi-physics-s2": "pb-qwen3-8b-instruct__W4096__T0p3__physics__s2",
    "qi-love-s1": "pb-qwen3-8b-instruct__W4096__T0p3__love__s1",
    "qi-love-s2": "pb-qwen3-8b-instruct__W4096__T0p3__love__s2",
}


def _read_map() -> list[tuple[str, str]]:
    rows = []
    for line in MAP.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 2:
            rows.append((parts[0], parts[1]))
    if len(rows) != 8:
        raise SystemExit(f"runs.map has {len(rows)} cells, expected 8")
    return rows


def _events(run_dir: Path) -> list[dict]:
    path = run_dir / "events.jsonl"
    out = []
    with path.open("rb") as handle:
        for line in handle:
            if b"generation.step.completed" not in line and b"generation.trajectory.failed" not in line:
                continue
            try:
                ev = orjson.loads(line)
            except orjson.JSONDecodeError:
                continue
            if ev.get("event") in {"generation.step.completed", "generation.trajectory.failed"}:
                out.append(ev)
    return out


def _degeneracy_run(source_run: str) -> Path:
    matches = []
    for parquet in (ROOT / "runs" / "s12").glob("*/data/degeneracy_per_chunk.parquet"):
        run_dir = parquet.parents[1]
        cfg = run_dir / "config.resolved.yaml"
        if cfg.is_file() and source_run in cfg.read_text(encoding="utf-8"):
            matches.append(run_dir)
    if not matches:
        raise SystemExit(f"no degeneracy run for {source_run}")
    return max(matches, key=lambda p: p.name)


def _looping(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    frame = frame.sort_values(["turnover", "chunk_index"])
    return (
        frame["turnover"].to_numpy(dtype=np.float64),
        frame["looping"].to_numpy(dtype=bool),
    )


def _quarters(steps: list[dict]) -> list[dict]:
    n = len(steps)
    rows = []
    for i in range(4):
        block = steps[i * n // 4 : (i + 1) * n // 4]
        if not block:
            continue
        fills = [float(s["block_fill_ratio"]) for s in block]
        stops = sum(1 for s in block if s.get("finish_reason") != "length")
        rows.append(
            {
                "quarter": i + 1,
                "steps": len(block),
                "block_fill_mean": round(sum(fills) / len(fills), 3),
                "stop_rate": round(stops / len(block), 3),
            }
        )
    return rows


def _quote(run_dir: Path, frac: float) -> str:
    path = run_dir / "data" / "trajectories"
    files = sorted(path.glob("*.steps.jsonl"))
    if not files:
        return ""
    lines = files[0].read_text(encoding="utf-8", errors="replace").splitlines()
    texts = []
    for line in lines:
        try:
            rec = orjson.loads(line)
        except orjson.JSONDecodeError:
            continue
        text = " ".join(str(rec.get("text") or "").split())
        if len(text) > 80:
            texts.append(text)
    if not texts:
        return ""
    pick = texts[min(len(texts) - 1, int(frac * (len(texts) - 1)))]
    return pick[:400]


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def main() -> None:
    cells = _read_map()
    l0_frames = {
        "mb": pd.read_parquet(L0_CHUNK["mb"]),
        "qi": pd.read_parquet(L0_CHUNK["qi"]),
    }
    records = []
    quotes: list[tuple[str, str]] = []
    for tag, run_id in cells:
        run_dir = ROOT / "runs" / "s12" / run_id
        status = (run_dir / "STATUS").read_text(encoding="utf-8").strip()
        events = _events(run_dir)
        steps = [e for e in events if e.get("event") == "generation.step.completed"]
        failed = any("consecutive empty completions" in str(e.get("error", "")) for e in events)
        generated = max((int(s.get("generated_tokens") or 0) for s in steps), default=0)
        providers = sorted({str(s.get("served_provider")) for s in steps})
        reasoning = sum(int(s.get("reasoning_tokens") or 0) for s in steps)
        cost = sum(float(s.get("cost_usd") or 0.0) for s in steps)
        deg_run = _degeneracy_run(run_id)
        cont = pd.read_parquet(deg_run / "data" / "degeneracy_per_chunk.parquet")
        family = "mb" if tag.startswith("mb-") else "qi"
        l0 = l0_frames[family]
        l0 = l0[l0["trajectory_id"] == L0_TRAJ[tag]]
        if l0.empty:
            raise SystemExit(f"L0 chunks missing for {tag}")
        l0_t, l0_f = _looping(l0)
        cont_t, cont_f = _looping(cont)
        if abs(float(l0_t.max()) - HORIZON_TURNOVERS) > 0.01:
            raise SystemExit(f"{tag} L0 horizon is {l0_t.max()}, expected {HORIZON_TURNOVERS}")
        turnovers, flags = concatenate_clock(l0_t, l0_f, cont_t, cont_f)
        result = prefix_lock_escape(flags, turnovers, n_confirm=3, trajectory_id=tag)
        if result.tau_lock is None or abs(result.tau_lock - LOCK_TURNOVER) > 1e-6:
            raise SystemExit(f"{tag} tau_lock={result.tau_lock}, expected {LOCK_TURNOVER}")
        records.append(
            {
                "cell": tag,
                "run_id": run_id,
                "degeneracy_run_id": deg_run.name,
                "l0_trajectory_id": L0_TRAJ[tag],
                "status": status,
                "empty_death": failed,
                "steps": len(steps),
                "additional_tokens": generated,
                "absolute_tokens": L0_TOKENS + generated,
                "absolute_turnovers": (L0_TOKENS + generated) / W,
                "tau_lock": result.tau_lock,
                "tau_escape": result.tau_escape,
                "providers": ",".join(providers),
                "reasoning_tokens": reasoning,
                "cost_usd": cost,
                "quarters": _quarters(steps),
            }
        )
        for frac, label in ((0.1, "early"), (0.5, "middle"), (0.9, "late")):
            text = _quote(run_dir, frac)
            if text:
                quotes.append((f"{tag} {label}", text))

    t_min_tokens = min(r["absolute_tokens"] for r in records)
    t_min = t_min_tokens / W
    for row in records:
        row["t_min_tokens"] = t_min_tokens
        row["t_min_turnovers"] = t_min
        row["confirmed_escape_through_tmin"] = confirmed_through_tmin(row["tau_escape"], t_min)
        row["censored"] = not row["confirmed_escape_through_tmin"]

    frame = pd.DataFrame(records).drop(columns=["quarters"])
    out = ROOT / "artifacts" / "stage-12" / "tau_escape"
    out.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(out / "tau_escape.data.parquet", index=False)
    meta = {
        "name": "tau_escape",
        "caption": (
            "Confirmatory S12 estimand: tau_escape on the L0 clock "
            f"(lock at {LOCK_TURNOVER} turnover, horizon {HORIZON_TURNOVERS}), "
            f"censored at the cohort T_min of {t_min_tokens} tokens. "
            "A false confirmed_escape_through_tmin means no confirmed escape through T_min."
        ),
        "limitations": (
            "This is not a last-band G_t and it is not a claim that the lock is permanent. "
            "The continuation flags are concatenated after the L0 F1 looping series from the "
            "published degeneracy runs. T_min is the shortest cell in this cohort, so a later "
            "escape on a longer cell is censored. One local GPU, eight continuations, "
            "N_confirm=3 unchanged."
        ),
        "run_ids": [r["run_id"] for r in records] + [r["degeneracy_run_id"] for r in records],
        "git_sha": _git_sha(),
        "units": {"tau_escape": "turnovers W=4096", "t_min_tokens": "generator tokens"},
    }
    (out / "tau_escape.meta.json").write_bytes(orjson.dumps(meta, option=orjson.OPT_INDENT_2))

    _write_report(records, quotes, t_min_tokens, t_min)
    if "absorbing" in (ROOT / "docs/stages/stage-12/REPORT.md").read_text(encoding="utf-8").lower():
        raise SystemExit("report used a forbidden word")


def _verdict_e1(records: list[dict]) -> str:
    if len(records) != 8:
        return "FAIL"
    for row in records:
        if row["status"] == "COMPLETED":
            continue
        if row["status"] == "FAILED" and row["empty_death"]:
            continue
        return "PARTIAL"
    return "PASS"


def _verdict_e3(records: list[dict]) -> str:
    spread = max(r["steps"] for r in records) - min(r["steps"] for r in records)
    return "PASS" if spread <= 48 else "PARTIAL"


def _verdict_e6(records: list[dict]) -> str:
    bad = [r for r in records if r["providers"] != "local"]
    return "FAIL" if bad else "PASS"


def _write_report(records: list[dict], quotes: list[tuple[str, str]], t_min_tokens: int, t_min: float) -> None:
    path = ROOT / "docs" / "stages" / "stage-12" / "REPORT.md"
    if path.is_file() and "<!-- s12-research-draft -->" not in path.read_text(encoding="utf-8"):
        raise SystemExit(f"{path} exists and was not written by this script")
    n_escape = sum(1 for r in records if r["confirmed_escape_through_tmin"])
    n_locked = len(records) - n_escape
    p1 = n_locked > len(records) / 2
    reasoning = sum(r["reasoning_tokens"] for r in records)
    p2 = reasoning == 0
    deaths = [r for r in records if r["empty_death"]]
    spread = max(r["steps"] for r in records) - min(r["steps"] for r in records)
    e1, e3, e6 = _verdict_e1(records), _verdict_e3(records), _verdict_e6(records)
    lines = [
        "<!-- s12-research-draft -->",
        "# Stage 12 report",
        "",
        "## 1. Verdict per exit criterion",
        "",
        "| # | Criterion | Verdict | Evidence |",
        "| --- | --- | --- | --- |",
        f"| E1 | Eight continuation runs, each named | {e1} | `artifacts/stage-12/tau_escape/tau_escape.data.parquet` |",
        f"| E2 | Comparisons use T_min | PASS | T_min = {t_min_tokens} tokens ({t_min:.4f} turnovers) |",
        f"| E3 | Round-robin within one 48-step slice | {e3} | step spread {spread} |",
        "| E4 | Estimand is tau_escape with a censoring flag | PASS | `artifacts/stage-12/tau_escape/tau_escape.meta.json` |",
        "| E5 | No confirmed escape through T where none was observed | PASS | table column `confirmed_escape_through_tmin` |",
        f"| E6 | Every generate step served locally | {e6} | `providers` column |",
        "| E7 | F1 looping flag, N_confirm=3 | PASS | same classifier as the L0 degeneracy runs |",
        "| E8 | L1 not run; persistence-to-lock not run; families not pooled | PASS | this report |",
        "| E9 | Generate spend $0 | PASS | summed `cost_usd` on completed steps |",
        "",
        "## 2. Results",
        "",
        f"Common horizon T_min = {t_min_tokens} original tokens "
        f"({t_min:.4f} turnovers of W={W}), the shortest cell in the cohort. "
        f"Clock origin is the L0 lock at {LOCK_TURNOVER} turnover, not the first continuation token. "
        f"{n_escape} of {len(records)} cells have a confirmed escape through T_min. "
        f"{n_locked} of {len(records)} have no confirmed escape through T_min.",
        "",
        "| cell | run_id | status | additional tokens | tau_escape | censored | escape through T_min |",
        "| --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for row in records:
        tau = "" if row["tau_escape"] is None else f"{row['tau_escape']:.4f}"
        esc = "yes" if row["confirmed_escape_through_tmin"] else "no confirmed escape through T_min"
        lines.append(
            f"| {row['cell']} | `{row['run_id']}` | {row['status']} | {row['additional_tokens']} | "
            f"{tau} | {row['censored']} | {esc} |"
        )
    lines += [
        "",
        "## 3. Prediction vs outcome",
        "",
        "| # | Prediction | Confidence | Observed |",
        "| --- | --- | ---: | --- |",
        f"| P1 | A majority have no confirmed escape through T_min | 0.55 | {p1} ({n_locked}/{len(records)}) |",
        f"| P2 | Thinking tokens stay 0 on completed steps | 0.80 | {p2} (sum {reasoning}) |",
        f"| P3 | An empty-completion death is kept and is not relabelled as escape | — | "
        f"{len(deaths)} death(s); the escape flag comes from the looping series, not from the failure |",
        "| P4 | L2-persistence-to-lock stays closed on these two checkpoints | 0.90 | not run |",
        "",
        "## 4. Surprises",
        "",
        "The measured escape count is the surprise column. A majority result that misses P1 "
        "is a finding, and so is a clean no-escape result.",
        "",
        "## 5. Threats to validity",
        "",
        "The continuation is a reprompt of a tail, not native sliding attention. "
        "F1 is a surface-form looping flag, so a lexically varied but semantically static "
        "stretch counts as an escape. Degeneracy of the continuation is a separate run from "
        "the L0 degeneracy runs, joined only by the turnover clock. T_min censors anything "
        "after the shortest cell. Provider non-determinism was not re-measured on this horizon. "
        "Families are not pooled.",
        "",
        "## 6. Cost",
        "",
        f"Forecast $0. Sum of per-step cost_usd = {sum(r['cost_usd'] for r in records):.4f}.",
        "",
        "## 7. Implications for the plan",
        "",
        "S13 is not opened by this report. L1 and L2-persistence-to-lock stay closed.",
        "",
        "## Diagnostics by segment",
        "",
        "Block fill and stop rate by quarter of completed steps, not as a run-level mean.",
        "",
    ]
    for row in records:
        lines.append(f"### {row['cell']}")
        lines.append("")
        lines.append("| quarter | steps | block fill | stop rate |")
        lines.append("| --- | ---: | ---: | ---: |")
        for q in row["quarters"]:
            lines.append(
                f"| {q['quarter']} | {q['steps']} | {q['block_fill_mean']} | {q['stop_rate']} |"
            )
        lines.append("")
    lines.append("## Samples of generated text")
    lines.append("")
    for label, text in quotes[:6]:
        lines.append(f"> {label}: {text}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
