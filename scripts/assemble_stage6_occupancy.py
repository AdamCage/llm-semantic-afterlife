#!/usr/bin/env python3
"""Assemble Stage 6 third-space occupancy from S5.1 + S2.2 T=0.3 four.

Joins ``gemini-embed-001`` (Stage 6 embed runs) with the two S5 spaces.
F4 remains the ten domain seeds; F6 remains the two twin pairs. CLI
``analyze separation`` on an S5.1 frame alone is still the wrong F4
number. Geometry ``α`` is not headlined. A lock is not a semantic basin.
Gemini is a closed architecture and cannot alone prove
architecture-independence.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from assemble_stage5_occupancy import (  # noqa: E402
    S22_GEN,
    S51_DEGENERACY,
    S51_GEN,
    _git_sha,
    _load_embed,
    _load_steps,
    _load_verdicts,
    _plotly_matrix,
    _require_completed,
    late_quotes,
    looping_figure,
    matrix_figure,
    pca_figure,
    protocol_by_quarter,
    protocol_by_seed_quarter,
    separation_figure,
    twins_figure,
)

from semantic_afterlife.analysis.occupancy import (  # noqa: E402
    OCCUPANCY_SPACE_ORDER,
    TWIN_PAIRS,
    last_band_seed_matrix,
    last_chunk_2d_illustration,
    lock_rate_by_seed,
    occupancy_embed_runs,
    require_occupancy_grid,
    split_domain_twin,
)
from semantic_afterlife.analysis.separation import (  # noqa: E402
    SeparationParams,
    compute_separation,
    trajectories_from_frame,
)
from semantic_afterlife.analysis.twins import TwinParams, compute_twin_contrast  # noqa: E402
from semantic_afterlife.config import get_settings  # noqa: E402
from semantic_afterlife.reporting.tables import save_table  # noqa: E402
from semantic_afterlife.viz.export import (  # noqa: E402
    FigureMeta,
    save_matplotlib_figure,
    save_plotly_figure,
)
from semantic_afterlife.viz.theme import PALETTE, ROLE_COLORS, apply_seaborn_theme  # noqa: E402

S6_GEMINI_S51 = occupancy_embed_runs("gemini-embed-001")[0]
S6_GEMINI_S22 = occupancy_embed_runs("gemini-embed-001")[1]

# Scientific-review limitations. A CI excluding 0 is the pre-registered
# F4 rule, not a thick robustness margin. Last-band F6 CI∋0 is not
# occupancy of one lock. Do not narrate the S5 bge-m3 waterloo point-Δ
# story as gemini's.
F4_LIMITATIONS = (
    "The pre-registered separated verdict is a last-band CI that excludes 0, "
    "not a thick robustness margin and not a recovered semantic state. "
    "gemini-embed-001 last-band gap 0.150 [0.029, 0.266] is an NHST whisker "
    "on n=20 with n_within_pairs=9: reused S2.2 physics s1 has 47 chunks vs "
    "48 on its pair, so the last-band D_within diagonal is NaN "
    "(n_chunk_pairs=0). That lower bound is closer to 0 than bge-m3's 0.065. "
    "gemini-embed-001 is closed; three-space sign agreement answers an "
    "embedding-artifact objection, not architecture-independence from gemini "
    "alone."
)
F6_LIMITATIONS = (
    "n=2 last-band pairs per family. A last-band CI that includes 0 is "
    "no detected divergence, not occupancy of one lock. In "
    "gemini-embed-001, waterloo Δ is 0.033 [0.001, 0.065] at band 0 "
    "(divergent on a 0.001 lower bound, seed still in the window) and −0.031 "
    "[−0.286, 0.223] at band 12 (sign flip; CI includes 0). That is not a "
    "vanished contrast. Gemini reactor never excluded 0, including at band 0. "
    "Do not narrate the S5 bge-m3 waterloo point-Δ≈0.05 story as gemini's. "
    "Extra replicates would be required to claim sameness. gemini is closed."
)


def last_band_gap_figure(
    last_band: pd.DataFrame, *, run_ids: list[str], git_sha: str | None
) -> tuple[plt.Figure, pd.DataFrame, FigureMeta]:
    apply_seaborn_theme()
    block = last_band.copy()
    block["embedding"] = pd.Categorical(block["embedding"], OCCUPANCY_SPACE_ORDER, ordered=True)
    block = block.sort_values("embedding")
    figure, ax = plt.subplots(figsize=(7.2, 4.2))
    xs = np.arange(len(block))
    ys = block["gap"].to_numpy()
    yerr = np.vstack([ys - block["gap_ci_low"].to_numpy(), block["gap_ci_high"].to_numpy() - ys])
    colors = [PALETTE[i] for i in range(len(block))]
    ax.errorbar(xs, ys, yerr=yerr, fmt="none", ecolor="#333333", capsize=5, linewidth=1.4)
    ax.scatter(xs, ys, c=colors, s=64, zorder=3)
    ax.axhline(0.0, color=ROLE_COLORS["baseline"], ls="--", lw=1.0)
    ax.set_xticks(xs)
    ax.set_xticklabels(list(block["embedding"].astype(str)), rotation=20, ha="right")
    ax.set_ylabel("last-band D_between − D_within")
    figure.suptitle("Ten-domain last-band gap in three embedding spaces", x=0.01, ha="left")
    figure.tight_layout()
    meta = FigureMeta(
        name="domain_gap_three_spaces",
        caption=(
            "F4 last-band domain gap with a 95% trajectory-bootstrap CI in "
            "bge-m3, qwen3-embed-8b, and gemini-embed-001 on the same 28 "
            "occupancy trajectories. Pre-registered sign is CI excludes 0; "
            "gemini's lower bound is 0.029. Twin pairs are excluded."
        ),
        run_ids=run_ids,
        git_sha=git_sha,
        limitations=F4_LIMITATIONS,
        units={"gap": "cosine-distance contrast"},
    )
    return figure, block.reset_index(drop=True), meta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--s51-gen", default=S51_GEN)
    parser.add_argument("--s22-gen", default=S22_GEN)
    parser.add_argument(
        "--s51-degeneracy",
        default="artifacts/stage-5/degeneracy/degeneracy_verdicts.csv",
    )
    parser.add_argument(
        "--s22-degeneracy",
        default="artifacts/stage-2/mechanism/degeneracy/degeneracy_verdicts.csv",
    )
    args = parser.parse_args()

    settings = get_settings()
    root = settings.paths.root
    git_sha = _git_sha(root)
    out_dir = settings.paths.stage_artifacts("s6") / "occupancy"
    out_dir.mkdir(parents=True, exist_ok=True)

    _require_completed(args.s51_gen, settings)
    _require_completed(args.s22_gen, settings)
    for slug in OCCUPANCY_SPACE_ORDER:
        s51_id, s22_id = occupancy_embed_runs(slug)
        _require_completed(s51_id, settings)
        _require_completed(s22_id, settings)

    s51_deg = _load_verdicts(root / args.s51_degeneracy, source="s5.1", gen_run=args.s51_gen)
    s22_deg = _load_verdicts(root / args.s22_degeneracy, source="s2.2", gen_run=args.s22_gen)
    s22_deg = s22_deg[s22_deg["semantic_seed"].isin(("physics", "surreal"))].copy()
    verdicts = pd.concat([s51_deg, s22_deg], ignore_index=True)
    domain_v, twin_v = split_domain_twin(verdicts)
    require_occupancy_grid(domain_v, twin_v)
    rates = lock_rate_by_seed(verdicts)

    sep_rows: list[pd.DataFrame] = []
    twin_rows: list[pd.DataFrame] = []
    domain_last_rows: list[pd.DataFrame] = []
    twin_last_rows: list[pd.DataFrame] = []
    matrix_rows: list[pd.DataFrame] = []
    gemini_n_domain: int | None = None
    gemini_n_twin: int | None = None

    for slug in OCCUPANCY_SPACE_ORDER:
        s51_id, s22_id = occupancy_embed_runs(slug)
        s51 = _load_embed(settings, s51_id, slug)
        s22 = _load_embed(settings, s22_id, slug)
        s22 = s22[s22["semantic_seed"].isin(("physics", "surreal"))].copy()
        joined = pd.concat([s51, s22], ignore_index=True)
        domain, twin = split_domain_twin(joined)
        require_occupancy_grid(domain, twin)
        if slug == "gemini-embed-001":
            gemini_n_domain = int(domain["trajectory_id"].nunique())
            gemini_n_twin = int(twin["trajectory_id"].nunique())

        domain_traj = trajectories_from_frame(domain)
        twin_traj = trajectories_from_frame(twin)
        sep = compute_separation(domain_traj, params=SeparationParams())
        twins = compute_twin_contrast(twin_traj, twin_pairs=list(TWIN_PAIRS), params=TwinParams())
        matrix = last_band_seed_matrix(domain_traj).assign(embedding=slug)

        sep.per_band = sep.per_band.assign(embedding=slug)
        twins.per_band = twins.per_band.assign(embedding=slug)
        last = sep.per_band.sort_values("band").iloc[-1]
        domain_last_rows.append(
            pd.DataFrame(
                [
                    {
                        "embedding": slug,
                        "scope": "domain_10",
                        "n_trajectories": int(sep.scalars["n_trajectories"]),
                        "last_band": float(last["band"]),
                        "d_within": float(last["d_within"]),
                        "d_between": float(last["d_between"]),
                        "gap": float(last["gap"]),
                        "gap_ci_low": float(last["gap_ci_low"]),
                        "gap_ci_high": float(last["gap_ci_high"]),
                        "separated": bool(last["separated"]),
                    }
                ]
            )
        )
        last_scopes = twins.per_band.loc[twins.per_band.groupby("scope")["band"].idxmax()]
        last_scopes = last_scopes[
            last_scopes["scope"].eq("all")
            | last_scopes["scope"].astype(str).str.contains("+", regex=False)
        ]
        twin_last_rows.append(last_scopes.assign(embedding=slug))
        sep_rows.append(sep.per_band)
        twin_rows.append(twins.per_band)
        matrix_rows.append(matrix)
        pca = last_chunk_2d_illustration(domain).assign(embedding=slug)
        run_pair = [s51_id, s22_id]
        figure, tidy, meta = matrix_figure(
            matrix, embedding=slug, run_ids=run_pair, git_sha=git_sha
        )
        if slug == "gemini-embed-001":
            meta.limitations = (
                (meta.limitations or "")
                + " gemini-embed-001 is closed; this panel cannot alone prove "
                "architecture-independence."
            )
        save_matplotlib_figure(figure, out_dir, meta, data=tidy)
        plt.close(figure)
        figure, tidy, meta = _plotly_matrix(
            matrix, embedding=slug, run_ids=run_pair, git_sha=git_sha
        )
        save_plotly_figure(figure, out_dir, meta, data=tidy)
        figure, tidy, meta = pca_figure(pca, embedding=slug, run_ids=run_pair, git_sha=git_sha)
        save_matplotlib_figure(figure, out_dir, meta, data=tidy)
        plt.close(figure)

    sep_all = pd.concat(sep_rows, ignore_index=True)
    twin_all = pd.concat(twin_rows, ignore_index=True)
    last_band = pd.concat(domain_last_rows, ignore_index=True)
    twin_last_all = pd.concat(twin_last_rows, ignore_index=True)
    matrix_tidy = pd.concat(matrix_rows, ignore_index=True)

    s5_sign = {
        row.embedding: bool(row.separated)
        for row in last_band[last_band["embedding"] != "gemini-embed-001"].itertuples()
    }
    last_band = last_band.assign(
        s5_spaces_separated=all(s5_sign.values()) if s5_sign else False,
        agrees_s5_sign=last_band["separated"]
        if not s5_sign
        else last_band["separated"].eq(all(s5_sign.values())),
    )

    s51_steps = _load_steps(settings.paths.find_run(args.s51_gen).events)
    s22_steps = _load_steps(
        settings.paths.find_run(args.s22_gen).events, seeds={"physics", "surreal"}
    )
    steps = pd.concat([s51_steps, s22_steps], ignore_index=True)
    protocol = protocol_by_quarter(steps)
    protocol_seed = protocol_by_seed_quarter(steps)

    quote_ids = [
        "or-qwen3-8b__W4096__T0p3__finance__s1",
        "or-qwen3-8b__W4096__T0p3__philosophy__s1",
        "or-qwen3-8b__W4096__T0p3__noise__s1",
        "or-qwen3-8b__W4096__T0p3__love__s1",
        "or-qwen3-8b__W4096__T0p3__waterloo-lost__s1",
        "or-qwen3-8b__W4096__T0p3__physics__s1",
    ]
    s51_chunks = pd.read_parquet(settings.paths.find_run(args.s51_gen).chunks())
    s22_chunks = pd.read_parquet(settings.paths.find_run(args.s22_gen).chunks())
    chunks = pd.concat([s51_chunks, s22_chunks], ignore_index=True)
    quotes = late_quotes(chunks, quote_ids)

    run_ids = [
        args.s51_gen,
        occupancy_embed_runs("bge-m3")[0],
        S51_DEGENERACY,
        args.s22_gen,
        occupancy_embed_runs("bge-m3")[1],
        S6_GEMINI_S51,
        S6_GEMINI_S22,
    ]

    grid_note = pd.DataFrame(
        [
            {
                "gemini_domain_trajectories": gemini_n_domain,
                "gemini_twin_trajectories": gemini_n_twin,
                "expected_domain": 20,
                "expected_twin": 8,
                "s51_gemini_run_id": S6_GEMINI_S51,
                "s22_gemini_run_id": S6_GEMINI_S22,
            }
        ]
    )

    save_table(
        verdicts.sort_values(["source", "semantic_seed", "stochastic_seed"]),
        out_dir,
        FigureMeta(
            name="degeneracy_verdicts_occupancy",
            caption=(
                "Per-trajectory degeneracy verdicts for the 28-cell occupancy "
                "grid reused in Stage 6 (24 S5.1 + 4 S2.2 raw T=0.3 "
                "physics/surreal). Thresholds 0.083 / late Jaccard 0.0122 "
                "were not moved. Degenerate rows are kept."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=(
                "Degeneracy is a surface-form measure. A trajectory can be "
                "lexically varied and still semantically static. Stage 6 did "
                "not retune the bar."
            ),
        ),
    )
    save_table(
        rates,
        out_dir,
        FigureMeta(
            name="lock_rate_by_seed",
            caption=(
                "Degenerate count per seed as k/n on the reused S5 occupancy "
                "grid. Domain overall is 20 trajectories; love remains 1/2."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations="n=2 per seed. A 2/2 cell is a count, not CI [1, 1].",
        ),
    )
    save_table(
        sep_all,
        out_dir,
        FigureMeta(
            name="domain_separation_per_band",
            caption=(
                "Ten-domain D_between − D_within per turnover band in three "
                "embedding spaces, including gemini-embed-001. Twin pairs are "
                "excluded."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=(
                "The lock is the sample; degenerate rows are kept. gemini is "
                "closed and cannot alone prove architecture-independence."
            ),
        ),
    )
    save_table(
        last_band,
        out_dir,
        FigureMeta(
            name="domain_separation_last_band",
            caption=(
                "F4 last-band gap on the ten domain seeds in three spaces, with "
                "a 95% trajectory-bootstrap CI. Separated iff the CI excludes 0 "
                "from above. agrees_s5_sign compares each space to the S5 "
                "two-space sign (both S5 spaces were separated)."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=F4_LIMITATIONS,
        ),
    )
    save_table(
        twin_all,
        out_dir,
        FigureMeta(
            name="twin_per_band",
            caption=(
                "F6 twin contrast per turnover band in three spaces. scope=all "
                "is the pooled twins; family scopes are waterloo and reactor. "
                "Δ = D_twin_matched − D_control."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=F6_LIMITATIONS,
        ),
    )
    save_table(
        twin_last_all,
        out_dir,
        FigureMeta(
            name="twin_last_band",
            caption=(
                "F6 last-band twin Δ per family and pooled, three embedding "
                "spaces including gemini-embed-001. divergent is the F6 verdict."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=F6_LIMITATIONS,
        ),
    )
    save_table(
        matrix_tidy,
        out_dir,
        FigureMeta(
            name="last_band_distance_matrix",
            caption=(
                "Tidy last-band 10×10 cosine-distance matrix among domain seeds, "
                "three spaces. Diagonal = D_within."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=(
                "Occupancy map in the original space. Not a cluster count. "
                "gemini-embed-001 is closed."
            ),
        ),
    )
    save_table(
        protocol,
        out_dir,
        FigureMeta(
            name="protocol_by_quarter",
            caption=(
                "Block fill and stop rate by quarter for the reused S5 lock "
                "generate runs. Stage 6 minted no generate run_id. Scopes: "
                "s5_scientific_28, s5_1_new_24, domain_20."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations="A run-level mean is not the object; use quarter 4.",
        ),
    )
    save_table(
        protocol_seed,
        out_dir,
        FigureMeta(
            name="protocol_by_seed_quarter",
            caption=(
                "Block fill and stop rate by seed and quarter at W=4096 T=0.3, "
                "reused from S5 generate. n=2 per seed."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations="n=2. Stage 6 did not retune sampling.",
        ),
    )
    save_table(
        quotes,
        out_dir,
        FigureMeta(
            name="late_chunk_quotes",
            caption=(
                "Last-chunk text heads from the reused S5 generate runs (not "
                "re-generated). Three domain seeds, love s1, one twin member, "
                "and physics s1."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations="Heads are truncated to 1600 characters. Stage 6 did not generate.",
        ),
    )
    save_table(
        grid_note,
        out_dir,
        FigureMeta(
            name="gemini_grid_counts",
            caption=(
                "Trajectory counts in gemini-embed-001 after joining S5.1 and "
                "raw T=0.3 physics/surreal from S2.2. F3 requires 20 domain + "
                "8 twin."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=(
                "S2.2 gemini parquet also contains prefill and T=1.0 surplus "
                "rows; occupancy assemble drops them via is_raw_lock_trajectory."
            ),
        ),
    )

    spaces = list(OCCUPANCY_SPACE_ORDER)
    figure, tidy, meta = looping_figure(rates, run_ids=run_ids, git_sha=git_sha)
    save_matplotlib_figure(figure, out_dir, meta, data=tidy)
    plt.close(figure)

    figure, tidy, meta = separation_figure(
        sep_all, run_ids=run_ids, git_sha=git_sha, embeddings=spaces
    )
    meta.limitations = F4_LIMITATIONS
    save_matplotlib_figure(figure, out_dir, meta, data=tidy)
    plt.close(figure)

    figure, tidy, meta = twins_figure(twin_all, run_ids=run_ids, git_sha=git_sha, embeddings=spaces)
    meta.limitations = F6_LIMITATIONS
    save_matplotlib_figure(figure, out_dir, meta, data=tidy)
    plt.close(figure)

    figure, tidy, meta = last_band_gap_figure(last_band, run_ids=run_ids, git_sha=git_sha)
    save_matplotlib_figure(figure, out_dir, meta, data=tidy)
    plt.close(figure)

    print(f"wrote {out_dir}")
    print(rates.to_string(index=False))
    print(last_band.to_string(index=False))
    print(twin_last_all.to_string(index=False))
    print(grid_note.to_string(index=False))
    q4 = protocol[protocol["quarter"] == 4]
    print(q4.to_string(index=False))


if __name__ == "__main__":
    main()
