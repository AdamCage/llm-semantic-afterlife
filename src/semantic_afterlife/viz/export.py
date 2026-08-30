"""Figure export: the mandatory bundle.

Per ``.cursor/rules/30-visualization.mdc`` a figure is not an artifact unless it
ships with the tidy data that produced it and metadata naming the runs, the code
version, and the caption. Anyone who opens ``artifacts/stage-N/`` with no other
context must be able to check the figure against its own numbers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import orjson
import pandas as pd

from ..logging_utils import get_logger

logger = get_logger("viz")


@dataclass(slots=True)
class FigureMeta:
    """Everything a reader needs to trust and reuse a figure."""

    name: str
    caption: str
    run_ids: list[str]
    git_sha: str | None = None
    config_sha256: str | None = None
    alt_text: str | None = None
    units: dict[str, str] = field(default_factory=dict)
    limitations: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "caption": self.caption,
            "alt_text": self.alt_text or self.caption,
            "limitations": self.limitations,
            "run_ids": self.run_ids,
            "git_sha": self.git_sha,
            "config_sha256": self.config_sha256,
            "units": self.units,
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
            **self.extra,
        }


def _write_sidecars(
    out_dir: Path,
    meta: FigureMeta,
    data: pd.DataFrame | dict[str, np.ndarray] | None,
) -> list[Path]:
    written: list[Path] = []
    if isinstance(data, pd.DataFrame):
        path = out_dir / f"{meta.name}.data.parquet"
        data.to_parquet(path, index=False)
        written.append(path)
    elif isinstance(data, dict):
        # Matrices (recurrence plots, transition matrices) are not naturally
        # tabular; store them as npz and say so in the metadata.
        path = out_dir / f"{meta.name}.data.npz"
        np.savez_compressed(path, **data)
        written.append(path)
        meta.extra["data_format"] = "npz"
    else:
        logger.warning("figure %s exported without source data", meta.name)
        meta.extra["data_format"] = "none"

    meta_path = out_dir / f"{meta.name}.meta.json"
    meta_path.write_bytes(orjson.dumps(meta.as_dict(), option=orjson.OPT_INDENT_2))
    written.append(meta_path)
    return written


def save_plotly_figure(
    figure: Any,
    out_dir: Path,
    meta: FigureMeta,
    *,
    data: pd.DataFrame | dict[str, np.ndarray] | None = None,
    width: int = 1100,
    height: int = 620,
    static: bool = True,
) -> list[Path]:
    """Write ``html`` + ``png`` + ``svg`` + tidy data + metadata."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    html_path = out_dir / f"{meta.name}.html"
    figure.write_html(
        html_path,
        include_plotlyjs="cdn",
        full_html=True,
        config={"displaylogo": False, "toImageButtonOptions": {"format": "svg"}},
    )
    written.append(html_path)

    if static:
        for suffix in ("png", "svg"):
            path = out_dir / f"{meta.name}.{suffix}"
            try:
                figure.write_image(path, width=width, height=height, scale=2)
            except Exception as exc:
                # kaleido is an optional native dependency; a missing static
                # renderer must not lose the interactive figure or the data.
                logger.warning("static export of %s failed (%s): %s", meta.name, suffix, exc)
                meta.extra.setdefault("static_export_error", str(exc))
            else:
                written.append(path)

    written.extend(_write_sidecars(out_dir, meta, data))
    logger.info("figure %s -> %s", meta.name, out_dir)
    return written


def save_matplotlib_figure(
    figure: Any,
    out_dir: Path,
    meta: FigureMeta,
    *,
    data: pd.DataFrame | dict[str, np.ndarray] | None = None,
    dpi: int = 200,
) -> list[Path]:
    """Write ``png`` + ``svg`` + ``pdf`` + tidy data + metadata."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for suffix in ("png", "svg", "pdf"):
        path = out_dir / f"{meta.name}.{suffix}"
        figure.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
        written.append(path)
    written.extend(_write_sidecars(out_dir, meta, data))
    logger.info("figure %s -> %s", meta.name, out_dir)
    return written


def write_index(out_dir: Path, *, stage: str, title: str) -> Path:
    """Assemble ``INDEX.md`` from the ``.meta.json`` sidecars present on disk.

    Generated from the sidecars rather than maintained by hand, so the index
    cannot drift from the figures it describes.
    """
    entries: list[dict[str, Any]] = []
    for meta_path in sorted(out_dir.rglob("*.meta.json")):
        try:
            entries.append(
                {
                    "path": meta_path.parent.relative_to(out_dir),
                    **orjson.loads(meta_path.read_bytes()),
                }
            )
        except orjson.JSONDecodeError:
            logger.warning("unreadable figure metadata: %s", meta_path)

    lines = [
        f"# {title}",
        "",
        f"Artifacts for stage {stage}. Generated by `afterlife report`; do not edit by hand.",
        "",
        f"{len(entries)} figures/tables.",
        "",
    ]
    for entry in entries:
        name = entry["name"]
        rel = Path(entry["path"]) / name
        lines.append(f"## {name}")
        lines.append("")
        lines.append(entry.get("caption", ""))
        if entry.get("limitations"):
            lines.append("")
            lines.append(f"**Does not establish:** {entry['limitations']}")
        lines.append("")
        formats = [
            f"[`{ext}`]({rel.as_posix()}.{ext})"
            for ext in ("html", "png", "svg", "pdf", "csv")
            if (out_dir / f"{rel}.{ext}").is_file()
        ]
        data_files = [
            f"[`{ext}`]({rel.as_posix()}.data.{ext})"
            for ext in ("parquet", "npz")
            if (out_dir / f"{rel}.data.{ext}").is_file()
        ]
        if formats:
            lines.append(f"- formats: {', '.join(formats)}")
        if data_files:
            lines.append(f"- source data: {', '.join(data_files)}")
        if entry.get("run_ids"):
            lines.append(f"- runs: {', '.join(f'`{r}`' for r in entry['run_ids'])}")
        if entry.get("git_sha"):
            lines.append(f"- git: `{entry['git_sha'][:12]}`")
        lines.append("")

    path = out_dir / "INDEX.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
