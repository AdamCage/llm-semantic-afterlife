"""One visual theme for the whole project.

Figures are a primary scientific output, so their appearance is a shared
decision, not a per-figure improvisation. Extend this module rather than setting
colours inside a plotting function.

Palette is Okabe–Ito, which is distinguishable under the common forms of colour
vision deficiency and survives greyscale printing. Continuous maps are
perceptually uniform; diverging maps are used only for genuinely signed
quantities (probability currents, differences) and always centred at zero.
"""

from __future__ import annotations

from typing import Any

import matplotlib as mpl
import plotly.graph_objects as go
import plotly.io as pio
import seaborn as sns
from cycler import cycler

#: Okabe–Ito qualitative palette, ordered for maximum separation of the first few.
PALETTE: tuple[str, ...] = (
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#009E73",  # bluish green
    "#CC79A7",  # reddish purple
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#8C564B",  # brown (extension)
    "#666666",  # grey (extension)
)

SEQUENTIAL = "viridis"
SEQUENTIAL_ALT = "magma"
DIVERGING = "RdBu_r"

#: Semantic colour roles, so that the same concept looks the same everywhere.
ROLE_COLORS: dict[str, str] = {
    "horizon": "#B00020",  # the context horizon t = W — the paper's landmark
    "ensemble": "#111111",  # ensemble mean / summary curve
    "trajectory": "#7F7F7F",  # individual trajectory traces
    "baseline": "#999999",  # shuffled / chance-level baselines
    "ci": "#0072B2",  # confidence bands
    "degenerate": "#D55E00",  # repetition-loop / degenerate trajectories
}

FONT_FAMILY = "DejaVu Sans, Segoe UI, Helvetica, Arial, sans-serif"
BASE_FONT_SIZE = 13
FIGURE_DPI = 200

#: Single- and double-column print sizes, in inches.
FIGSIZE_SINGLE = (5.5, 3.6)
FIGSIZE_DOUBLE = (11.0, 4.2)
FIGSIZE_SQUARE = (5.5, 5.2)

_PLOTLY_TEMPLATE_NAME = "afterlife"


def plotly_template() -> str:
    """Register (once) and return the project's plotly template name."""
    if _PLOTLY_TEMPLATE_NAME not in pio.templates:
        template = go.layout.Template()
        template.layout = go.Layout(
            font={"family": FONT_FAMILY, "size": BASE_FONT_SIZE, "color": "#1a1a1a"},
            title={
                "x": 0.0,
                "xanchor": "left",
                "y": 0.98,
                "yanchor": "top",
                "font": {"size": BASE_FONT_SIZE + 4},
            },
            paper_bgcolor="white",
            plot_bgcolor="white",
            colorway=list(PALETTE),
            xaxis={
                "showgrid": True,
                "gridcolor": "#E8E8E8",
                "zeroline": False,
                "linecolor": "#4D4D4D",
                "ticks": "outside",
                "mirror": False,
            },
            yaxis={
                "showgrid": True,
                "gridcolor": "#E8E8E8",
                "zeroline": False,
                "linecolor": "#4D4D4D",
                "ticks": "outside",
                "mirror": False,
            },
            legend={
                "bgcolor": "rgba(255,255,255,0.85)",
                "bordercolor": "#CCCCCC",
                "borderwidth": 1,
                "orientation": "h",
                "yanchor": "top",
                "y": -0.16,
                "x": 0,
            },
            margin={"l": 78, "r": 34, "t": 86, "b": 96},
            hovermode="closest",
            colorscale={"sequential": SEQUENTIAL, "diverging": DIVERGING},
        )
        pio.templates[_PLOTLY_TEMPLATE_NAME] = template
    pio.templates.default = f"plotly_white+{_PLOTLY_TEMPLATE_NAME}"
    return _PLOTLY_TEMPLATE_NAME


def apply_seaborn_theme() -> None:
    """Configure seaborn/matplotlib for print-quality panels."""
    sns.set_theme(
        context="paper",
        style="ticks",
        palette=list(PALETTE),
        font_scale=1.05,
        rc={
            "figure.dpi": 110,
            "savefig.dpi": FIGURE_DPI,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Segoe UI", "Helvetica", "Arial"],
            "axes.grid": True,
            "axes.grid.axis": "both",
            "grid.color": "#E8E8E8",
            "grid.linewidth": 0.7,
            "axes.edgecolor": "#4D4D4D",
            "axes.linewidth": 0.9,
            "axes.titlesize": BASE_FONT_SIZE + 2,
            "axes.titleweight": "semibold",
            "axes.titlelocation": "left",
            "axes.labelsize": BASE_FONT_SIZE,
            "legend.frameon": True,
            "legend.framealpha": 0.8,
            "legend.edgecolor": "#CCCCCC",
            "xtick.labelsize": BASE_FONT_SIZE - 2,
            "ytick.labelsize": BASE_FONT_SIZE - 2,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "image.cmap": SEQUENTIAL,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        },
    )
    mpl.rcParams["axes.prop_cycle"] = cycler(color=list(PALETTE))


def horizon_shapes(W: int, *, x_max: float, n_marks: int = 3) -> list[dict[str, Any]]:
    """Vertical markers at ``t = W, 2W, …`` for a plotly time axis.

    Every time-axis figure in this project marks the context horizon; it is the
    landmark the whole paper is organised around.
    """
    shapes: list[dict[str, Any]] = []
    for k in range(1, n_marks + 1):
        x = k * W
        if x > x_max:
            break
        shapes.append(
            {
                "type": "line",
                "x0": x,
                "x1": x,
                "yref": "paper",
                "y0": 0,
                "y1": 1,
                "line": {
                    "color": ROLE_COLORS["horizon"],
                    "width": 1.6 if k == 1 else 0.9,
                    "dash": "solid" if k == 1 else "dot",
                },
                "layer": "below",
            }
        )
    return shapes


def horizon_annotations(W: int, *, x_max: float, n_marks: int = 3) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for k in range(1, n_marks + 1):
        x = k * W
        if x > x_max:
            break
        out.append(
            {
                "x": x,
                "yref": "paper",
                "y": 1.005,
                "text": f"t = {k}W" if k > 1 else "context horizon (t = W)",
                "showarrow": False,
                "font": {"size": BASE_FONT_SIZE - 3, "color": ROLE_COLORS["horizon"]},
                "xanchor": "left",
                "yanchor": "bottom",
            }
        )
    return out


def turnover_axis(W: int, x_max: float, *, n_ticks: int = 6) -> dict[str, Any]:
    """Secondary x-axis expressing generated tokens as window turnovers ``t/W``.

    Absolute token counts are not comparable across ``W``; turnovers are, so both
    are always shown (rules: 30-visualization).
    """
    max_turnover = x_max / W
    step = max(1, round(max_turnover / n_ticks))
    ticks = list(range(0, int(max_turnover) + 1, step))
    return {
        "overlaying": "x",
        "side": "top",
        "title": {"text": "window turnovers t/W"},
        "tickmode": "array",
        "tickvals": [t * W for t in ticks],
        "ticktext": [str(t) for t in ticks],
        "range": [0, x_max],
        "showgrid": False,
    }
