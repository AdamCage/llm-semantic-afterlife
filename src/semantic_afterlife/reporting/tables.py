"""Table export.

Every table ships in four forms: ``csv`` (canonical, diffable), ``parquet``
(typed), ``md`` (readable inside a stage report) and ``html`` (styled, for
browsing artifacts). A metadata sidecar carries the caption and provenance, so a
table is as self-describing as a figure.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..logging_utils import get_logger
from ..viz.export import FigureMeta, _write_sidecars

logger = get_logger("reporting")


def _style(frame: pd.DataFrame, *, caption: str) -> str:
    numeric = frame.select_dtypes("number").columns
    styler = (
        frame.style.set_caption(caption)
        .format(precision=4, na_rep="—")
        .set_table_styles(
            [
                {
                    "selector": "caption",
                    "props": [
                        ("caption-side", "top"),
                        ("text-align", "left"),
                        ("font-weight", "600"),
                        ("padding", "0.4em 0"),
                        ("font-size", "1.05em"),
                    ],
                },
                {
                    "selector": "th",
                    "props": [
                        ("background-color", "#F2F4F7"),
                        ("text-align", "left"),
                        ("padding", "0.35em 0.6em"),
                        ("border-bottom", "2px solid #4D4D4D"),
                    ],
                },
                {"selector": "td", "props": [("padding", "0.3em 0.6em")]},
                {"selector": "tr:nth-child(even)", "props": [("background-color", "#FAFBFC")]},
                {
                    "selector": "table",
                    "props": [
                        ("border-collapse", "collapse"),
                        ("font-family", "DejaVu Sans, Segoe UI, Helvetica, sans-serif"),
                        ("font-size", "0.92em"),
                    ],
                },
            ]
        )
        .hide(axis="index")
    )
    if len(numeric):
        styler = styler.background_gradient(cmap="Blues", subset=list(numeric), axis=0)
    return str(styler.to_html())


def save_table(
    frame: pd.DataFrame,
    out_dir: Path,
    meta: FigureMeta,
    *,
    float_format: str = "%.6g",
) -> list[Path]:
    """Write ``csv`` + ``parquet`` + ``md`` + ``html`` + metadata sidecar."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    csv_path = out_dir / f"{meta.name}.csv"
    frame.to_csv(csv_path, index=False, float_format=float_format, encoding="utf-8")
    written.append(csv_path)

    md_path = out_dir / f"{meta.name}.md"
    md_path.write_text(
        f"**{meta.name}** — {meta.caption}\n\n"
        + frame.to_markdown(index=False, floatfmt=".4g")
        + "\n",
        encoding="utf-8",
    )
    written.append(md_path)

    html_path = out_dir / f"{meta.name}.html"
    try:
        html_path.write_text(_style(frame, caption=meta.caption), encoding="utf-8")
    except Exception as exc:
        # Styling depends on optional matplotlib colormaps; the canonical CSV
        # must never be lost to a cosmetic failure.
        logger.warning("styled HTML for table %s failed: %s", meta.name, exc)
    else:
        written.append(html_path)

    written.extend(_write_sidecars(out_dir, meta, frame))
    logger.info("table %s -> %s", meta.name, out_dir)
    return written


def describe_numeric(frame: pd.DataFrame, by: list[str], columns: list[str]) -> pd.DataFrame:
    """Grouped mean / sd / n for a set of columns.

    ``n`` is always included: an aggregate without its sample size is not
    reportable (rules: 30-visualization).
    """
    grouped = frame.groupby(by, dropna=False)[columns]
    out = grouped.agg(["mean", "std", "count"])
    out.columns = [f"{col}_{stat}" for col, stat in out.columns]
    return out.reset_index()
