"""Assemble Paper B S13 from published S9–S12 artifacts. No generation.

Copies last-band tables, completion counts, quarter diagnostics, and the
S12 censoring table. Does not re-estimate G_t and does not recompute flags.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import orjson
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from semantic_afterlife.config import load_experiment_config
from semantic_afterlife.runctx import run_context
from semantic_afterlife.viz.export import (
    FigureMeta,
    save_matplotlib_figure,
    save_plotly_figure,
    write_index,
)
from semantic_afterlife.viz.theme import PALETTE, ROLE_COLORS, apply_seaborn_theme, plotly_template

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "stages" / "stage13_synthesis.yaml"

CELLS: dict[tuple[str, str], tuple[str, str, str]] = {
    ("s9", "instruct-nf4"): ("Qwen3-8B", "Instruct NF4", "nf4"),
    ("s9", "base-nf4"): ("Qwen3-8B", "Base NF4", "nf4"),
    ("s9", "instruct-int8"): ("Qwen3-8B", "Instruct INT8", "int8"),
    ("s9", "base-int8"): ("Qwen3-8B", "Base INT8", "int8"),
    ("s10", "base-nf4"): ("OLMo-3-7B", "Base NF4", "nf4"),
    ("s10", "sft-nf4"): ("OLMo-3-7B", "SFT NF4", "nf4"),
    ("s10", "dpo-nf4"): ("OLMo-3-7B", "DPO NF4", "nf4"),
    ("s10", "rlvr-nf4"): ("OLMo-3-7B", "RLVR NF4", "nf4"),
    ("s10", "base-int8"): ("OLMo-3-7B", "Base INT8", "int8"),
    ("s10", "rlvr-int8"): ("OLMo-3-7B", "RLVR INT8", "int8"),
    ("s11", "ministral-base"): ("Ministral-3-8B", "Base", "nf4"),
    ("s11", "ministral-instruct"): ("Ministral-3-8B", "Instruct", "nf4"),
    ("s11", "gemma-base"): ("Gemma-4-12B", "Base", "nf4"),
    ("s11", "gemma-it"): ("Gemma-4-12B", "IT", "nf4"),
}

EXPECTED_COMPLETION: dict[tuple[str, str], tuple[int, int]] = {
    ("s9", "instruct-nf4"): (38, 2),
    ("s9", "base-nf4"): (31, 9),
    ("s9", "instruct-int8"): (9, 1),
    ("s9", "base-int8"): (8, 2),
    ("s10", "base-nf4"): (27, 13),
    ("s10", "sft-nf4"): (19, 21),
    ("s10", "dpo-nf4"): (3, 37),
    ("s10", "rlvr-nf4"): (4, 36),
    ("s10", "base-int8"): (5, 5),
    ("s10", "rlvr-int8"): (0, 10),
    ("s11", "ministral-base"): (40, 0),
    ("s11", "ministral-instruct"): (40, 0),
    ("s11", "gemma-base"): (38, 2),
    ("s11", "gemma-it"): (0, 40),
}

HEADLINE_ORDER: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Qwen3-8B", ("Base NF4", "Instruct NF4")),
    ("OLMo-3-7B", ("Base NF4", "SFT NF4", "DPO NF4", "RLVR NF4")),
    ("Ministral-3-8B", ("Base", "Instruct")),
    ("Gemma-4-12B", ("Base", "IT")),
)
SPACES: tuple[tuple[str, str], ...] = (
    ("local-bge-m3", "BGE-M3"),
    ("qwen3-embed-8b", "Qwen3-Embedding-8B"),
)

_FORBIDDEN: tuple[tuple[str, str], ...] = (
    ("absorbing", "absorbing"),
    ("full attention is unnecessary", "full attention is unnecessary"),
    ("full attention on every layer", "full attention on every layer"),
    ("gemma disagrees", "gemma disagrees"),
    ("disagrees across spaces", "disagrees across spaces"),
)

LIMITATIONS = (
    "P1 reprompt of a tail, raw_bytes, local NF4. Native sliding attention was not measured. "
    "Last-band G_t is seed-conditioned ensemble persistence in one embedding space. "
    "The two spaces are not on a common scale and are not pooled. Families are not pooled. "
    "A CI that includes 0 is not an established sign. An unidentified last-band is not a "
    "sign flip and is not drawn as zero. INT8 rows are concordance, not a third headline. "
    "Provider non-determinism was not re-measured on these horizons. "
    "L0 is finite: 12 turnovers, 49152 tokens. "
    "S12 is a separate censored count through 4999168 original tokens, not a pooled rate "
    "and not a permanence claim. "
    "Gemma Base BGE is an identified negative. The Gemma Base Qwen-embed sign is not "
    "established. Cross-space sign agreement for Gemma is not identified. "
    "Lock-table n is not the 12W completer count."
)


def forbidden_prose(text: str) -> list[str]:
    """Return banned phrases present in text. Used to stop the assembly."""
    lowered = text.lower()
    return [label for needle, label in _FORBIDDEN if needle in lowered]


def refuse_pooled_family(frame: pd.DataFrame) -> None:
    if "family" not in frame.columns:
        raise SystemExit("synthesis table has no family column")
    bad = frame["family"].astype(str).str.lower().isin({"pooled", "all", "combined"})
    if bool(bad.any()):
        raise SystemExit("pooled family row")


def _artifact(number: int, *parts: str) -> Path:
    return ROOT.joinpath("artifacts", f"stage-{number}", *parts)


def _annotate(frame: pd.DataFrame, stage: str, source: Path) -> pd.DataFrame:
    out = frame.copy()
    out["stage"] = stage
    out["source_artifact"] = source.relative_to(ROOT).as_posix()
    keys = list(zip(out["stage"], out["cell"], strict=True))
    missing = [key for key in keys if key not in CELLS]
    if missing:
        raise SystemExit(f"unexpected cell in {source}: {missing[:3]}")
    mapped = [CELLS[key] for key in keys]
    out["family"] = [item[0] for item in mapped]
    out["checkpoint"] = [item[1] for item in mapped]
    out["quantization"] = [item[2] for item in mapped]
    refuse_pooled_family(out)
    return out


def load_gt() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for number in (9, 10, 11):
        path = _artifact(number, "gt_last_band", "gt_last_band.csv")
        frames.append(_annotate(pd.read_csv(path), f"s{number}", path))
    out = pd.concat(frames, ignore_index=True)
    if len(out) != 26:
        raise SystemExit(f"expected 26 published G_t rows, found {len(out)}")
    refuse_pooled_family(out)
    return out


def load_completion() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for number in (9, 10, 11):
        path = _artifact(number, "generate_status", "generate_status.csv")
        frames.append(_annotate(pd.read_csv(path), f"s{number}", path))
    out = pd.concat(frames, ignore_index=True)
    if len(out) != 14:
        raise SystemExit(f"expected 14 completion rows, found {len(out)}")
    for key, (n_completed, n_failed) in EXPECTED_COMPLETION.items():
        hit = out[(out["stage"] == key[0]) & (out["cell"] == key[1])]
        if len(hit) != 1:
            raise SystemExit(f"missing completion row {key}")
        got = (int(hit.iloc[0]["n_completed"]), int(hit.iloc[0]["n_failed"]))
        if got != (n_completed, n_failed):
            raise SystemExit(
                f"completion {key} is {got}, closed report has {(n_completed, n_failed)}"
            )
    refuse_pooled_family(out)
    return out


def load_protocol() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for number in (9, 10, 11):
        path = _artifact(number, "protocol_by_quarter", "protocol_by_quarter.csv")
        frames.append(_annotate(pd.read_csv(path), f"s{number}", path))
    out = pd.concat(frames, ignore_index=True)
    if not set(out["quarter"].astype(int)).issuperset({1, 2, 3, 4}):
        raise SystemExit("protocol table is missing a quarter")
    refuse_pooled_family(out)
    return out


def load_s12() -> pd.DataFrame:
    path = _artifact(12, "tau_escape", "tau_escape.data.parquet")
    out = pd.read_parquet(path)
    if len(out) != 8:
        raise SystemExit(f"S12 table has {len(out)} rows")
    if set(out["absolute_tokens"].astype(int)) != {4999168}:
        raise SystemExit("S12 absolute token counts are not the common T_min")
    if not np.allclose(out["absolute_turnovers"].astype(float), 1220.5):
        raise SystemExit("S12 absolute turnovers are not 1220.5")
    flags = out["confirmed_escape_through_tmin"].astype("boolean")
    censored = out["censored"].astype("boolean")
    if bool(flags.isna().any()) or bool(flags.any()):
        raise SystemExit("S12 escape flag is not false on every row")
    if bool(censored.isna().any()) or not bool(censored.all()):
        raise SystemExit("S12 censored flag is not true on every row")
    if not bool(out["tau_escape"].isna().all()):
        raise SystemExit("S12 tau_escape is not blank on every row")
    out = out.copy()
    out["family"] = np.where(out["cell"].str.startswith("mb-"), "Ministral-3-8B", "Qwen3-8B")
    out["source_artifact"] = path.relative_to(ROOT).as_posix()
    refuse_pooled_family(out)
    return out


def _ids(frame: pd.DataFrame, *columns: str) -> list[str]:
    found: list[str] = []
    for column in columns:
        if column not in frame.columns:
            continue
        for value in frame[column].dropna().astype(str):
            if value and value not in found:
                found.append(value)
    return found


def _fmt(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "—"
    if isinstance(value, (bool, np.bool_)):
        return "yes" if bool(value) else "no"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        return format(float(value), ".6g")
    return str(value)


def _md_table(frame: pd.DataFrame, columns: list[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    rule = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, rule]
    for _, row in frame.iterrows():
        lines.append("| " + " | ".join(_fmt(row[column]) for column in columns) + " |")
    return "\n".join(lines)


def _space_label(slug: str) -> str:
    for key, label in SPACES:
        if key == slug:
            return label
    return slug


def _one_gt(frame: pd.DataFrame, family: str, checkpoint: str, embedding: str) -> pd.Series:
    hit = frame[
        (frame["family"] == family)
        & (frame["checkpoint"] == checkpoint)
        & (frame["embedding"] == embedding)
        & (frame["quantization"] == "nf4")
    ]
    if len(hit) != 1:
        raise SystemExit(f"expected one NF4 row for {family} {checkpoint} {embedding}")
    return hit.iloc[0]


def check_gemma(frame: pd.DataFrame) -> None:
    bge = _one_gt(frame, "Gemma-4-12B", "Base", "local-bge-m3")
    qwen = _one_gt(frame, "Gemma-4-12B", "Base", "qwen3-embed-8b")
    if not (float(bge["last_band_G"]) < 0 and bool(bge["ci_excludes_0"])):
        raise SystemExit("Gemma Base BGE is not the published identified negative")
    if bool(qwen["ci_excludes_0"]):
        raise SystemExit("Gemma Base Qwen-embed is published as not established")


def _errorbar(ax: plt.Axes, x: float, row: pd.Series, color: str) -> None:
    y = float(row["last_band_G"])
    lo = float(row["G_lo"])
    hi = float(row["G_hi"])
    established = bool(row["ci_excludes_0"])
    ax.errorbar(
        [x],
        [y],
        yerr=[[y - lo], [hi - y]],
        fmt="o",
        color=color,
        mfc=color if established else "white",
        mec=color,
        capsize=3,
        markersize=6,
    )


def plot_gt(frame: pd.DataFrame) -> tuple[plt.Figure, go.Figure, pd.DataFrame]:
    apply_seaborn_theme()
    plotly_template()
    headline = frame[frame["quantization"] == "nf4"].copy()
    plotted = headline[np.isfinite(headline["last_band_G"].astype(float))].copy()
    plotted["space_label"] = plotted["embedding"].map(_space_label)
    fig, axes = plt.subplots(2, 4, figsize=(12.6, 6.6), sharex="col")
    interactive = make_subplots(
        rows=2,
        cols=4,
        subplot_titles=[family for family, _ in HEADLINE_ORDER] + [""] * 4,
        vertical_spacing=0.16,
        horizontal_spacing=0.05,
    )
    for row_i, (embedding, space_label) in enumerate(SPACES):
        color = PALETTE[row_i]
        for col_i, (family, checkpoints) in enumerate(HEADLINE_ORDER):
            ax = axes[row_i][col_i]
            xs = np.arange(len(checkpoints))
            sub = plotted[(plotted["family"] == family) & (plotted["embedding"] == embedding)]
            for x, checkpoint in zip(xs, checkpoints, strict=True):
                hit = sub[sub["checkpoint"] == checkpoint]
                if hit.empty:
                    continue
                point = hit.iloc[0]
                _errorbar(ax, float(x), point, color)
                y = float(point["last_band_G"])
                lo = float(point["G_lo"])
                hi = float(point["G_hi"])
                interactive.add_trace(
                    go.Scatter(
                        x=[checkpoint],
                        y=[y],
                        mode="markers",
                        name=space_label,
                        legendgroup=space_label,
                        showlegend=col_i == 0 and checkpoint == checkpoints[0],
                        marker={
                            "color": color if bool(point["ci_excludes_0"]) else "white",
                            "line": {"color": color, "width": 1.5},
                            "size": 9,
                        },
                        error_y={
                            "type": "data",
                            "array": [hi - y],
                            "arrayminus": [y - lo],
                            "color": color,
                            "thickness": 1.2,
                        },
                        hovertext=(
                            f"{family} {checkpoint} {space_label}<br>"
                            f"G_t={y:.6g} [{lo:.6g}, {hi:.6g}]<br>"
                            f"ci_excludes_0={bool(point['ci_excludes_0'])}<br>"
                            f"{point['generate_run_id']}"
                        ),
                    ),
                    row=row_i + 1,
                    col=col_i + 1,
                )
            ax.axhline(0.0, color=ROLE_COLORS["baseline"], linewidth=0.8)
            ax.set_xticks(xs, list(checkpoints), rotation=35, ha="right")
            if row_i == 0:
                ax.set_title(family)
            if col_i == 0:
                ax.set_ylabel(f"{space_label}\nlast-band G_t")
            interactive.update_yaxes(title_text=space_label, row=row_i + 1, col=1)
    fig.tight_layout()
    interactive.update_layout(
        title="Published NF4 last-band G_t, one panel per family and space",
        template=plotly_template(),
        height=720,
        width=1200,
    )
    return fig, interactive, plotted


def plot_s12(frame: pd.DataFrame) -> tuple[plt.Figure, go.Figure]:
    apply_seaborn_theme()
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    interactive = go.Figure()
    for family, color in (("Ministral-3-8B", PALETTE[0]), ("Qwen3-8B", PALETTE[1])):
        sub = frame[frame["family"] == family]
        ax.scatter(
            sub["absolute_turnovers"].astype(float),
            sub["cell"],
            color=color,
            label=family,
            s=36,
            zorder=3,
        )
        interactive.add_trace(
            go.Scatter(
                x=sub["absolute_turnovers"].astype(float),
                y=sub["cell"],
                mode="markers",
                name=family,
                marker={"color": color, "size": 10},
                hovertext=sub["run_id"],
            )
        )
    for xpos, label in ((0.75, "lock event 0.75"), (12.0, "L0 series ends 12.0")):
        ax.axvline(xpos, color=ROLE_COLORS["baseline"], linewidth=0.8, linestyle="--")
        interactive.add_vline(x=xpos, line_dash="dash", line_color="#999999", annotation_text=label)
    ax.set_xlabel("absolute turnover from L0 token 0 (W = 4096)")
    ax.set_ylabel("cell")
    ax.set_title("S12 censoring time on the absolute L0 axis")
    ax.legend(frameon=True)
    fig.tight_layout()
    interactive.update_layout(
        title="S12 censoring time on the absolute L0 axis",
        xaxis_title="absolute turnover from L0 token 0 (W = 4096)",
        yaxis_title="cell",
        template=plotly_template(),
        height=520,
        width=900,
    )
    return fig, interactive


def _write_table(
    directory: Path,
    name: str,
    frame: pd.DataFrame,
    *,
    caption: str,
    run_ids: list[str],
    git_sha: str | None,
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(directory / f"{name}.data.parquet", index=False)
    frame.to_csv(directory / f"{name}.csv", index=False)
    meta = {
        "name": name,
        "caption": caption,
        "alt_text": caption,
        "limitations": LIMITATIONS,
        "run_ids": run_ids,
        "git_sha": git_sha,
        "units": {"last_band_G": "L2-normalised distance gap in that embedding space"},
    }
    (directory / f"{name}.meta.json").write_bytes(orjson.dumps(meta, option=orjson.OPT_INDENT_2))
    hits = forbidden_prose(caption + LIMITATIONS)
    if hits:
        raise SystemExit(f"table caption banned phrase: {hits}")


def _save_figure(
    mpl_fig: plt.Figure,
    plotly_fig: go.Figure,
    directory: Path,
    meta: FigureMeta,
    data: pd.DataFrame,
) -> None:
    hits = forbidden_prose(meta.caption + (meta.limitations or ""))
    if hits:
        raise SystemExit(f"figure caption banned phrase: {hits}")
    save_matplotlib_figure(mpl_fig, directory, meta, data=data)
    save_plotly_figure(plotly_fig, directory, meta, data=data, static=False)
    plt.close(mpl_fig)


def _quotes() -> list[str]:
    report = ROOT / "docs" / "stages" / "stage-12" / "REPORT.md"
    kept = [
        line
        for line in report.read_text(encoding="utf-8").splitlines()
        if line.startswith("> ") and len(line.strip()) > 40 and not forbidden_prose(line)
    ]
    if len(kept) < 3:
        raise SystemExit("closed S12 report did not yield three usable quotations")
    return [
        "> Quoted from docs/stages/stage-12/REPORT.md. Printed there as Ministral physics only.",
        *kept[:4],
    ]


def _gt_view(frame: pd.DataFrame) -> pd.DataFrame:
    view = frame.copy()
    view["space"] = view["embedding"].map(_space_label)
    columns = [
        "stage",
        "family",
        "checkpoint",
        "quantization",
        "space",
        "last_band_G",
        "G_lo",
        "G_hi",
        "ci_excludes_0",
        "n_within_pairs",
        "n_between_pairs",
        "n_confirmed_escape",
        "generate_run_id",
        "source_artifact",
    ]
    return view[columns]


def write_report(
    *,
    run_id: str,
    gt: pd.DataFrame,
    completion: pd.DataFrame,
    protocol: pd.DataFrame,
    s12: pd.DataFrame,
) -> None:
    gt_view = _gt_view(gt)
    headline = gt_view[gt_view["quantization"] == "nf4"]
    ends = protocol[
        protocol["quarter"].astype(int).isin([1, 4]) & (protocol["quantization"] == "nf4")
    ]
    ends = ends.sort_values(["stage", "family", "checkpoint", "quarter"])
    end_view = ends[
        [
            "stage",
            "family",
            "checkpoint",
            "quarter",
            "n_trajectories",
            "block_fill_mean",
            "stop_rate_mean",
            "generate_run_id",
        ]
    ]
    comp_view = completion[
        [
            "stage",
            "family",
            "checkpoint",
            "n_completed",
            "n_failed",
            "generate_run_id",
            "source_artifact",
        ]
    ]
    s12_view = s12[
        [
            "cell",
            "family",
            "run_id",
            "absolute_tokens",
            "absolute_turnovers",
            "tau_escape",
            "censored",
            "confirmed_escape_through_tmin",
        ]
    ]
    lines = [
        "# Stage 13 report — Paper B read from closed artifacts",
        "",
        "Assembly run `" + run_id + "`. No new generation.",
        "",
        "## 1. Verdict per exit criterion",
        "",
        "| # | Criterion | Verdict | Evidence |",
        "| --- | --- | --- | --- |",
        "| E1 | One S13 run at $0 and no new generate | PASS | `" + run_id + "` |",
        "| E2 | Published G_t rows, families not pooled | PASS | `artifacts/stage-13/gt_published/gt_published.data.parquet` |",
        "| E3 | Gemma Base BGE identified negative; Qwen-embed sign not established | PASS | `artifacts/stage-13/gt_nf4/gt_nf4.data.parquet` |",
        "| E4 | S12 0/8 on its own table | PASS | `artifacts/stage-13/tau_escape_s12/tau_escape_s12.data.parquet` |",
        "| E5 | Figure bundles carry the published scalar and its interval | PASS | `artifacts/stage-13/INDEX.md` |",
        "| E6 | S13 ledger spend $0 | PASS | `" + run_id + "` |",
        "| E7 | Four threats named below | PASS | section 5 |",
        "",
        "## 2. Results",
        "",
        "S9–S11 are the Paper B story. Each family keeps its own rows. "
        "The plotted quantity is the published last-band G_t in the original "
        "embedding space, with the published interval. Open markers are rows "
        "whose published `ci_excludes_0` is false. Missing markers are unidentified "
        "last bands (OLMo DPO NF4 in both spaces; Gemma IT in both spaces) and are "
        "not drawn as zero.",
        "",
        _md_table(headline, list(headline.columns)),
        "",
        "Gemma Base BGE is an identified negative: G_t = "
        + _fmt(_one_gt(gt, "Gemma-4-12B", "Base", "local-bge-m3")["last_band_G"])
        + ", interval ["
        + _fmt(_one_gt(gt, "Gemma-4-12B", "Base", "local-bge-m3")["G_lo"])
        + ", "
        + _fmt(_one_gt(gt, "Gemma-4-12B", "Base", "local-bge-m3")["G_hi"])
        + "], `ci_excludes_0` yes. "
        "Gemma Base Qwen-embed is "
        + _fmt(_one_gt(gt, "Gemma-4-12B", "Base", "qwen3-embed-8b")["last_band_G"])
        + " ["
        + _fmt(_one_gt(gt, "Gemma-4-12B", "Base", "qwen3-embed-8b")["G_lo"])
        + ", "
        + _fmt(_one_gt(gt, "Gemma-4-12B", "Base", "qwen3-embed-8b")["G_hi"])
        + "], `ci_excludes_0` no, so that sign is not established. "
        "Cross-space sign agreement for Gemma is not identified. "
        "Source: `artifacts/stage-11/gt_last_band/gt_last_band.csv`, copied to "
        "`artifacts/stage-13/gt_published/gt_published.data.parquet`.",
        "",
        "Completion counts are the published `generate_status.csv` rows. "
        "A failed cell stays in the sample. It is missing data, not an unlock. "
        "Run-level block-fill means in that file are not the claim.",
        "",
        _md_table(comp_view, list(comp_view.columns)),
        "",
        "S12 is not in the G_t table. 0 of 8 cells have a confirmed escape through "
        "T_min = 4999168 original tokens. The clock is absolute turnovers from L0 "
        "token 0. The lock event is at 0.75. The L0 series ends at 12.0. Censoring "
        "time is 1220.5, which is 1219.75 turnovers after the lock. Families are "
        "counted, not pooled. Source: `artifacts/stage-12/tau_escape/tau_escape.data.parquet`.",
        "",
        _md_table(s12_view, list(s12_view.columns)),
        "",
        "### Block fill and stop rate by quarter",
        "",
        "First and final quarter of each NF4 cell, copied from "
        "`protocol_by_quarter.csv`. All four quarters are in "
        "`artifacts/stage-13/protocol_by_quarter/protocol_by_quarter.data.parquet`. "
        "A run-level mean is not the claim.",
        "",
        _md_table(end_view, list(end_view.columns)),
        "",
        "## 3. Prediction vs outcome",
        "",
        "| # | Prediction | Confidence | Observed |",
        "| --- | --- | ---: | --- |",
        "| P1 | No pooled family row | 0.90 | true |",
        "| P2 | Gemma Base BGE identified negative; Qwen-embed CI does not exclude 0 | 0.95 | true |",
        "| P3 | S12 flag false on 8/8 and absent from the G_t table | 0.95 | true |",
        "| P4 | This command does not generate or embed | 0.99 | true |",
        "| P5 | New prose avoids the banned phrases in `forbidden_prose` | 0.90 | true |",
        "",
        "## 4. Surprises",
        "",
        "The assembly did not change a published flag. The negative Gemma Base "
        "BGE gap and the OLMo completion collapse were already in the closed "
        "reports. OLMo SFT NF4 is positive in both spaces as a point; the BGE "
        "interval includes 0, so that BGE gap is not established. That reading "
        "is the S10 table, not a new estimand.",
        "",
        "## 5. Threats to validity",
        "",
        LIMITATIONS,
        "",
        "Qwen-embed for S9–S11 was the hosted endpoint at realised cost $0 "
        "(ADR-0027, ADR-0028, ADR-0029). BGE-M3 was local. The two pipelines "
        "are not one embedding measurement.",
        "",
        "## 6. Cost",
        "",
        "Forecast $0. S13 ledger spend on `" + run_id + "` is $0. No GPU generate.",
        "",
        "## 7. Implications for the plan",
        "",
        "S13 closes the stage ladder. There is no S14. L1 and "
        "L2-persistence-to-lock stay closed. Paper A text in `paper/main.tex` "
        "is not rewritten. A Paper B section may be added only after this "
        "report's gate exits 0.",
        "",
        "## Samples of generated text",
        "",
        "These lines are quotations of the closed S12 report. This stage did not "
        "generate them. They are Ministral physics only (`mb-physics-s1`, "
        "`mb-physics-s2`).",
        "",
        *_quotes(),
        "",
    ]
    text = "\n".join(lines) + "\n"
    hits = forbidden_prose(text)
    if hits:
        raise SystemExit(f"report banned phrase: {hits}")
    path = ROOT / "docs" / "stages" / "stage-13" / "REPORT.md"
    path.write_text(text, encoding="utf-8", newline="\n")


def write_notes(*, run_id: str, gt: pd.DataFrame, s12: pd.DataFrame) -> None:
    bge = _one_gt(gt, "Gemma-4-12B", "Base", "local-bge-m3")
    qwen = _one_gt(gt, "Gemma-4-12B", "Base", "qwen3-embed-8b")
    text = "\n".join(
        [
            "# Paper B notes (S13)",
            "",
            "Written from the assembly `" + run_id + "`. Numbers below are copies.",
            "",
            "## Allowed",
            "",
            "- S9–S11, read by family, are the Paper B story. "
            "Artifact: `artifacts/stage-13/gt_published/gt_published.data.parquet`.",
            "- Gemma Base BGE last-band G_t is "
            + _fmt(bge["last_band_G"])
            + " ["
            + _fmt(bge["G_lo"])
            + ", "
            + _fmt(bge["G_hi"])
            + "], ci_excludes_0 yes, an identified negative. "
            "generate_run_id `" + str(bge["generate_run_id"]) + "`.",
            "- Gemma Base Qwen-embed last-band G_t is "
            + _fmt(qwen["last_band_G"])
            + " ["
            + _fmt(qwen["G_lo"])
            + ", "
            + _fmt(qwen["G_hi"])
            + "], ci_excludes_0 no. The sign is not established. "
            "generate_run_id `" + str(qwen["generate_run_id"]) + "`.",
            "- S12 is 0 of 8 confirmed escapes through 4999168 original tokens, "
            "censored, families counted separately. "
            "Artifact: `artifacts/stage-13/tau_escape_s12/tau_escape_s12.data.parquet`. "
            "Source run ids are the eight `run_id` values in that table "
            f"({len(s12)} rows).",
            "",
            "## Do not write",
            "",
            "- A pooled family rate, or one instruct effect.",
            "- Permanence language banned by ADR-0025 section 3.",
            "- The S11 necessary-condition sentence about attention on every layer.",
            "- A claim that the two Gemma spaces have opposite established signs.",
            "- A claim that S12 shows the lock cannot break after T_min.",
            "- A statistic taken from a 2-D projection.",
            "",
            "## Limitations the manuscript must name",
            "",
            LIMITATIONS,
            "",
        ]
    )
    hits = forbidden_prose(text)
    if hits:
        raise SystemExit(f"notes banned phrase: {hits}")
    path = ROOT / "paper" / "notes" / "paper-b.md"
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    experiment, resolved, sha = load_experiment_config(CONFIG)
    if experiment.n_trajectories != 0:
        raise SystemExit("S13 config expanded to trajectories; refusing to assemble")
    gt = load_gt()
    completion = load_completion()
    protocol = load_protocol()
    s12 = load_s12()
    check_gemma(gt)
    if set(s12["cell"]).intersection(set(gt["cell"])):
        raise SystemExit("S12 cells collided with the G_t table")
    with run_context(
        stage="s13",
        slug="paperb-synthesis",
        config_resolved=resolved,
        config_sha256=sha,
        stage_budget_usd=0.0,
    ) as ctx:
        run_id = ctx.run_id
        git_sha = ctx.manifest.git.get("sha")
        data_dir = ctx.paths.data_dir
        gt.to_parquet(data_dir / "gt_published.parquet", index=False)
        completion.to_parquet(data_dir / "completion.parquet", index=False)
        protocol.to_parquet(data_dir / "protocol_by_quarter.parquet", index=False)
        s12.to_parquet(data_dir / "tau_escape_s12.parquet", index=False)
        gt_ids = _ids(gt, "generate_run_id", "embed_run_id", "persistence_run_id")
        s12_ids = _ids(s12, "run_id", "degeneracy_run_id")
        _write_table(
            ROOT / "artifacts" / "stage-13" / "gt_published",
            "gt_published",
            _gt_view(gt),
            caption=(
                "Published last-band G_t from S9, S10, and S11, copied by family. "
                "NF4 rows are the headline. INT8 rows are concordance."
            ),
            run_ids=[run_id, *gt_ids],
            git_sha=git_sha,
        )
        _write_table(
            ROOT / "artifacts" / "stage-13" / "completion",
            "completion",
            completion[
                [
                    "stage",
                    "family",
                    "checkpoint",
                    "quantization",
                    "n_planned",
                    "n_completed",
                    "n_failed",
                    "generate_run_id",
                    "source_artifact",
                ]
            ],
            caption=(
                "Published completion counts. Failed cells stay in the sample. "
                "They are missing from last-band pairs, not unlocks."
            ),
            run_ids=[run_id, *_ids(completion, "generate_run_id")],
            git_sha=git_sha,
        )
        _write_table(
            ROOT / "artifacts" / "stage-13" / "protocol_by_quarter",
            "protocol_by_quarter",
            protocol[
                [
                    "stage",
                    "family",
                    "checkpoint",
                    "quantization",
                    "quarter",
                    "n_trajectories",
                    "n_steps",
                    "block_fill_mean",
                    "stop_rate_mean",
                    "generate_run_id",
                    "source_artifact",
                ]
            ],
            caption=("Published block fill and stop rate by quarter. Not a run-level mean."),
            run_ids=[run_id, *_ids(protocol, "generate_run_id")],
            git_sha=git_sha,
        )
        mpl_gt, plotly_gt, plotted = plot_gt(gt)
        _save_figure(
            mpl_gt,
            plotly_gt,
            ROOT / "artifacts" / "stage-13" / "gt_nf4",
            FigureMeta(
                name="gt_nf4",
                caption=(
                    "Published NF4 last-band G_t. Rows are embedding spaces and are not "
                    "on one scale. Columns are families and are not averaged. Filled "
                    "markers: published CI excludes 0. Open markers: the CI includes 0. "
                    "OLMo DPO NF4 and Gemma IT have no last-band point in either space "
                    "and are omitted, not drawn at zero."
                ),
                limitations=LIMITATIONS,
                run_ids=[
                    run_id,
                    *_ids(plotted, "generate_run_id", "embed_run_id", "persistence_run_id"),
                ],
                git_sha=git_sha,
                units={"last_band_G": "L2-normalised distance gap in that embedding space"},
                alt_text=(
                    "Four families by two embedding spaces. Each panel shows published "
                    "last-band G_t with its interval. No pooled mean."
                ),
            ),
            plotted,
        )
        mpl_s12, plotly_s12 = plot_s12(s12)
        _save_figure(
            mpl_s12,
            plotly_s12,
            ROOT / "artifacts" / "stage-13" / "tau_escape_s12",
            FigureMeta(
                name="tau_escape_s12",
                caption=(
                    "S12 censoring time. Eight cells at absolute turnover 1220.5 from "
                    "L0 token 0. The lock event is at 0.75. The L0 series ends at 12.0. "
                    "tau_escape is blank and censored is true on every row. "
                    "0 of 8 have a confirmed escape through 4999168 original tokens. "
                    "The two families are coloured and counted, not pooled."
                ),
                limitations=LIMITATIONS,
                run_ids=[run_id, *s12_ids],
                git_sha=git_sha,
                units={"absolute_turnovers": "turnovers of W=4096 from L0 token 0"},
            ),
            s12[
                [
                    "cell",
                    "family",
                    "run_id",
                    "absolute_tokens",
                    "absolute_turnovers",
                    "tau_escape",
                    "censored",
                    "confirmed_escape_through_tmin",
                    "source_artifact",
                ]
            ],
        )
        write_index(
            ROOT / "artifacts" / "stage-13",
            stage="s13",
            title="Stage 13 — Paper B synthesis",
        )
        write_report(run_id=run_id, gt=gt, completion=completion, protocol=protocol, s12=s12)
        write_notes(run_id=run_id, gt=gt, s12=s12)
        if ctx.ledger.run_spend_usd != 0:
            raise SystemExit("S13 run spent money")
        ctx.events.event(
            "synthesis.assembled",
            n_gt=len(gt),
            n_s12=len(s12),
            n_plotted=len(plotted),
        )


if __name__ == "__main__":
    main()
