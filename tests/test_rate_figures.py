"""Stage 2 headline figures carry a CI and refuse a run-level fill mean."""

from __future__ import annotations

import pandas as pd

from semantic_afterlife.viz.figures import quarter_protocol_figure, rate_bar_figure


def test_rate_bar_figure_uses_supplied_interval() -> None:
    rates = pd.DataFrame(
        {
            "generator": ["a", "b"],
            "rate": [0.75, 0.25],
            "ci_low": [0.4, 0.05],
            "ci_high": [0.95, 0.55],
            "n": [8, 8],
            "n_positive": [6, 2],
        }
    )
    figure, tidy, meta = rate_bar_figure(
        rates,
        group_column="generator",
        run_ids=["run-x"],
        caption="test caption",
        limitations="test limitation: interval is not a claim about one trajectory.",
    )
    assert list(tidy["rate"]) == [0.75, 0.25]
    assert meta.limitations and "not a claim" in meta.limitations
    assert figure.layout.yaxis.range == (0, 1)


def test_quarter_protocol_figure_has_no_run_mean_column() -> None:
    rows = []
    for generator in ("g", "h"):
        for traj in (1, 2):
            for quarter, fill, stop in ((1, 1.0, 0.0), (2, 0.8, 0.2), (3, 0.5, 0.5), (4, 0.2, 0.8)):
                rows.append(
                    {
                        "generator": generator,
                        "trajectory_id": f"{generator}-{traj}",
                        "quarter": quarter,
                        "n_steps": 4,
                        "block_fill": fill,
                        "stop_rate": stop,
                    }
                )
    figure, tidy, meta = quarter_protocol_figure(pd.DataFrame(rows), run_ids=["run-y"])
    assert "block_fill_mean" not in tidy.columns
    assert set(tidy["quarter"]) == {1, 2, 3, 4}
    assert meta.limitations and "run-level mean" in meta.limitations
    assert len(figure.data) == 4  # two generators × two panels
