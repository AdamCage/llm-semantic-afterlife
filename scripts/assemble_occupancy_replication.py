#!/usr/bin/env python3
"""Assemble ADR-0022 occupancy replication F4 CIs.

One generate run holds the full 28-trajectory grid (physics/surreal included).
Writes under ``artifacts/occupancy-replication/`` and copies headline CSVs
to ``artifacts/tmlr-correctness/occupancy-replication/``. Does **not** overwrite
``artifacts/stage-5/occupancy/`` or ``artifacts/stage-6/occupancy/``.

``noise s2`` FAILED at 49151/49152 (WindowProtocolError). Its 47 chunks remain
in the parquet; that is missing-data, not a silent drop. Last-band
``D_within`` for a 47-vs-48 pair can be empty — report it, do not impute.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import pandas as pd

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from assemble_stage5_occupancy import (  # noqa: E402
    _git_sha,
    _load_embed,
    _load_verdicts,
    _require_completed,
    matrix_figure,
    separation_figure,
)
from matplotlib import pyplot as plt  # noqa: E402

from semantic_afterlife.analysis.occupancy import (  # noqa: E402
    OCCUPANCY_SPACE_ORDER,
    filter_raw_lock,
    last_band_seed_matrix,
    require_occupancy_grid,
    split_domain_twin,
)
from semantic_afterlife.analysis.rates import parse_trajectory_id  # noqa: E402
from semantic_afterlife.analysis.separation import (  # noqa: E402
    SeparationParams,
    compute_separation,
    trajectories_from_frame,
)
from semantic_afterlife.config import get_settings  # noqa: E402
from semantic_afterlife.errors import AnalysisError  # noqa: E402
from semantic_afterlife.reporting.tables import save_table  # noqa: E402
from semantic_afterlife.viz.export import FigureMeta, save_matplotlib_figure  # noqa: E402

GEN_DEFAULT = "s5-lock-occupancy-repl-20260907T091450Z-e8452acb"
ARCHIVAL_STAGE5 = Path("artifacts/stage-5/occupancy")
ARCHIVAL_STAGE6 = Path("artifacts/stage-6/occupancy")
# Published F4 last-band CIs. Replication sits beside these; do not replace.
ARCHIVAL_F4 = {
    "bge-m3": {"gap": 0.200895, "gap_ci_low": 0.0652385, "gap_ci_high": 0.332212},
    "qwen3-embed-8b": {"gap": 0.390151, "gap_ci_low": 0.150537, "gap_ci_high": 0.593395},
    "gemini-embed-001": {"gap": 0.150016, "gap_ci_low": 0.0289632, "gap_ci_high": 0.265854},
}
FORBIDDEN_OUT = frozenset(
    {
        Path("artifacts/stage-5/occupancy").resolve(),
        Path("artifacts/stage-6/occupancy").resolve(),
    }
)
EXPECTED_CHUNKS = 48
TMLR_REPL = Path("artifacts/tmlr-correctness/occupancy-replication")
HEADLINE_STEMS = (
    "domain_separation_last_band",
    "domain_separation_last_band_vs_archival",
    "domain_separation_per_band",
    "missing_data",
)
HEADLINE_SUFFIXES = (".csv", ".meta.json", ".md")


def _guard_out_dir(out_dir: Path) -> Path:
    resolved = out_dir.resolve()
    if resolved in FORBIDDEN_OUT:
        raise SystemExit(
            f"refusing to write {resolved}: ADR-0022 forbids overwriting Stage 5/6 occupancy CSVs"
        )
    if (
        ARCHIVAL_STAGE5.resolve() in resolved.parents
        or ARCHIVAL_STAGE6.resolve() in resolved.parents
    ):
        raise SystemExit(f"refusing to write under {resolved}: that is a Stage 5/6 occupancy tree")
    return out_dir


def copy_headline_csvs(source: Path, dest: Path) -> Path:
    """Copy F4 headline tables into the TMLR tree. ADR-0022 named this path."""
    dest.mkdir(parents=True, exist_ok=True)
    for stem in HEADLINE_STEMS:
        for suffix in HEADLINE_SUFFIXES:
            src = source / f"{stem}{suffix}"
            if src.is_file():
                shutil.copy2(src, dest / f"{stem}{suffix}")
    readme = dest / "README.md"
    readme.write_text(
        "# Occupancy replication (ADR-0022) — TMLR copies\n"
        "\n"
        "Headline CSVs copied from `artifacts/occupancy-replication/`.\n"
        "Canonical figures live there. This folder exists because ADR-0022\n"
        "named `artifacts/tmlr-correctness/occupancy-replication/`.\n"
        "This is **not** a restore of Stage 5/6 occupancy CSVs, and it does\n"
        "not replace archival `0.201 [0.065, 0.332]`.\n",
        encoding="utf-8",
    )
    return dest


def _verdicts_table(path: Path, *, source: str, gen_run: str) -> pd.DataFrame:
    """Load degeneracy verdicts from the analysis run, csv or parquet."""
    if path.suffix == ".parquet":
        frame = pd.read_parquet(path)
        filtered = filter_raw_lock(frame)
        parsed = pd.DataFrame(filtered["trajectory_id"].map(parse_trajectory_id).tolist())
        out = filtered.merge(parsed, on="trajectory_id", how="left", suffixes=("", "_parsed"))
        out["source"] = source
        out["generation_run_id"] = gen_run
        return out
    return _load_verdicts(path, source=source, gen_run=gen_run)


def missing_data_from_trajectories(trajectories: pd.DataFrame) -> pd.DataFrame:
    """FAILED or short-chunk trajectories. Do not impute last-band pairs."""
    rows: list[dict[str, object]] = []
    for row in trajectories.itertuples(index=False):
        n_chunks = int(row.n_chunks)
        status = str(row.status)
        if status == "COMPLETED" and n_chunks == EXPECTED_CHUNKS:
            continue
        error = "" if pd.isna(getattr(row, "error", None)) else str(row.error)
        if status == "FAILED":
            note = (
                "kept in occupancy parquet; not silently dropped; last-band "
                "D_within can be empty for unmatched 47-vs-48 pairs"
            )
        else:
            note = (
                "COMPLETED with 47 chunks; last-band pairs with a 48-chunk "
                "partner stop at turnover 11.75 (band 10), so band 12 D_within "
                "for this seed can be empty — report, do not impute"
            )
        rows.append(
            {
                "trajectory_id": str(row.trajectory_id),
                "status": status,
                "error": error,
                "generated_tokens": int(row.generated_tokens),
                "n_chunks": n_chunks,
                "roundtrip_failures": int(getattr(row, "roundtrip_failures", 0) or 0),
                "note": note,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gen", default=GEN_DEFAULT)
    parser.add_argument(
        "--embed-two-space", required=True, help="s5 embed run_id (bge-m3 + qwen3-embed-8b)"
    )
    parser.add_argument("--embed-gemini", required=True, help="s6 embed run_id (gemini-embed-001)")
    parser.add_argument(
        "--degeneracy",
        required=True,
        help="path to degeneracy_verdicts.csv or .parquet from the degeneracy run",
    )
    parser.add_argument(
        "--out",
        default="artifacts/occupancy-replication",
        type=Path,
        help="replication artifact directory; must not be a Stage 5/6 occupancy path",
    )
    args = parser.parse_args()
    out_dir = _guard_out_dir(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    settings = get_settings()
    root = settings.paths.root
    git_sha = _git_sha(root)

    gen_run = _require_completed(args.gen, settings)
    _require_completed(args.embed_two_space, settings)
    _require_completed(args.embed_gemini, settings)
    run_ids = [args.gen, args.embed_two_space, args.embed_gemini]

    deg_path = Path(args.degeneracy)
    if not deg_path.is_file():
        raise SystemExit(f"missing degeneracy table {deg_path}")
    verdicts = _verdicts_table(deg_path, source="occupancy-repl", gen_run=args.gen)
    domain_v, twin_v = split_domain_twin(verdicts)
    require_occupancy_grid(domain_v, twin_v)

    traj_path = gen_run.root / "data" / "trajectories.parquet"
    if not traj_path.is_file():
        raise SystemExit(f"missing {traj_path}")
    trajectories = pd.read_parquet(traj_path)
    missing = missing_data_from_trajectories(trajectories)
    noise_s2 = "or-qwen3-8b__W4096__T0p3__noise__s2"
    if missing.empty or noise_s2 not in set(missing["trajectory_id"].astype(str)):
        raise SystemExit(f"{noise_s2} missing from missing_data; refusing to drop the FAILED cell")

    domain_last_rows: list[pd.DataFrame] = []
    sep_rows: list[pd.DataFrame] = []
    matrix_rows: list[pd.DataFrame] = []
    embed_run_for = {
        "bge-m3": args.embed_two_space,
        "qwen3-embed-8b": args.embed_two_space,
        "gemini-embed-001": args.embed_gemini,
    }

    for slug in OCCUPANCY_SPACE_ORDER:
        frame = _load_embed(settings, embed_run_for[slug], slug)
        domain, twin = split_domain_twin(frame)
        require_occupancy_grid(domain, twin)
        domain_traj = trajectories_from_frame(domain)
        if len(domain_traj) != 20:
            raise AnalysisError(f"{slug}: expected 20 domain trajectories, got {len(domain_traj)}")
        sep = compute_separation(domain_traj, params=SeparationParams())
        matrix = last_band_seed_matrix(domain_traj).assign(embedding=slug)
        sep.per_band = sep.per_band.assign(embedding=slug)
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
        sep_rows.append(sep.per_band)
        matrix_rows.append(matrix)
        figure, tidy, meta = matrix_figure(matrix, embedding=slug, run_ids=run_ids, git_sha=git_sha)
        save_matplotlib_figure(figure, out_dir, meta, data=tidy)
        plt.close(figure)

    last_band = pd.concat(domain_last_rows, ignore_index=True)
    per_band = pd.concat(sep_rows, ignore_index=True)
    matrices = pd.concat(matrix_rows, ignore_index=True)

    compare_rows: list[dict[str, object]] = []
    for slug, archival in ARCHIVAL_F4.items():
        row = last_band.loc[last_band["embedding"] == slug].iloc[0]
        repl_sign = float(row["gap_ci_low"]) > 0
        archival_sign = archival["gap_ci_low"] > 0
        compare_rows.append(
            {
                "embedding": slug,
                "archival_gap": archival["gap"],
                "archival_gap_ci_low": archival["gap_ci_low"],
                "archival_gap_ci_high": archival["gap_ci_high"],
                "replication_gap": float(row["gap"]),
                "replication_gap_ci_low": float(row["gap_ci_low"]),
                "replication_gap_ci_high": float(row["gap_ci_high"]),
                "replication_separated": bool(row["separated"]),
                "sign_agrees": bool(repl_sign and archival_sign),
            }
        )
    compare = pd.DataFrame(compare_rows)

    f4_limitations = (
        "Replication of the occupancy generate, not a restore of "
        "s5-lock-occupancy-20260905T164327Z-6780902f. Hosted sampling is not "
        "deterministic; level mismatch vs archival CIs is expected. Sign agreement "
        "(CI excludes 0) is the claim. Band 12 has n_within_pairs=6 and "
        "n_between_pairs=114 because four domain trajectories stop at turnover "
        "11.75 (noise s2 FAILED; philosophy s1, programming s2, war s2 COMPLETED "
        "with 47 chunks). Band 10 still has the full 80/1440 pair set and also "
        "excludes 0; it is not the pre-registered F4 number. Do not impute missing "
        "last-band pairs. Do not replace archival 0.201 [0.065, 0.332]. Twin CIs "
        "are not headlined here."
    )
    save_table(
        last_band,
        out_dir,
        FigureMeta(
            name="domain_separation_last_band",
            caption=(
                "F4 last-band domain gap (D_between − D_within) with a 95% "
                "multiplicity-preserving trajectory bootstrap (n_boot=2000, seed=0) "
                "on the ADR-0022 replication generate. Ten domain seeds, two "
                "stochastic replicates. Twin pairs excluded. New run_ids."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=f4_limitations,
            units={"gap": "cosine-distance contrast", "last_band": "turnover band start"},
        ),
    )
    save_table(
        per_band,
        out_dir,
        FigureMeta(
            name="domain_separation_per_band",
            caption=(
                "F4 domain gap by turnover band on the occupancy replication "
                "trajectories. Last band is the pre-registered F4 number."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=f4_limitations,
            units={"gap": "cosine-distance contrast", "band": "turnover band start"},
        ),
    )
    save_table(
        compare,
        out_dir,
        FigureMeta(
            name="domain_separation_last_band_vs_archival",
            caption=(
                "Replication F4 last-band CIs beside the archival Stage 6 CSV "
                "(bge-m3 0.201 [0.065, 0.332], qwen3-embed-8b 0.390 [0.151, 0.593], "
                "gemini-embed-001 0.150 [0.029, 0.266]). Sign agreement means both "
                "CIs exclude 0. This table does not overwrite the archival files."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=f4_limitations,
            units={"gap": "cosine-distance contrast"},
        ),
    )
    save_table(
        matrices,
        out_dir,
        FigureMeta(
            name="last_band_seed_matrix",
            caption=(
                "Last-band mean cosine-distance matrix among the ten domain seeds, "
                "one row per embedding. Diagonal is D_within. Occupancy map, not a "
                "cluster count. Computed in the original high-dimensional space."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations=f4_limitations,
            units={"distance": "1 − cosine similarity"},
        ),
    )
    save_table(
        missing,
        out_dir,
        FigureMeta(
            name="missing_data",
            caption=(
                "Trajectories that did not yield 48 chunks. noise s2 FAILED at "
                "49151/49152 (WindowProtocolError). philosophy s1, programming s2 "
                "and war s2 COMPLETED with 47 chunks. Chunks are kept; last-band "
                "D_within for a 47-vs-48 pair can be empty. Do not impute."
            ),
            run_ids=run_ids,
            git_sha=git_sha,
            limitations="A FAILED or short trajectory is missing data, not a scientific exclusion.",
        ),
    )
    save_table(
        verdicts,
        out_dir,
        FigureMeta(
            name="degeneracy_verdicts",
            caption=(
                "Per-trajectory degeneracy on the occupancy replication generate. "
                "A looping trajectory occupies one point in representation space; "
                "read this before any confinement claim."
            ),
            run_ids=[args.gen, *run_ids],
            git_sha=git_sha,
            limitations="n=2 per seed is a count, not a CI.",
        ),
    )

    figure, tidy, meta = separation_figure(
        per_band, run_ids=run_ids, git_sha=git_sha, embeddings=list(OCCUPANCY_SPACE_ORDER)
    )
    save_matplotlib_figure(figure, out_dir, meta, data=tidy)
    plt.close(figure)

    # Touch-proof: archival headline CSVs must still exist and were not our --out.
    for path in (
        ARCHIVAL_STAGE6 / "domain_separation_last_band.csv",
        ARCHIVAL_STAGE5 / "domain_separation_last_band.csv",
    ):
        if not (root / path).is_file():
            raise SystemExit(f"archival CSV missing after assemble: {path}")

    tmlr_dest = _guard_out_dir(root / TMLR_REPL)
    if out_dir.resolve() != tmlr_dest.resolve():
        copy_headline_csvs(out_dir, tmlr_dest)

    print(f"wrote replication F4 tables under {out_dir}")
    print(f"copied headline CSVs to {tmlr_dest}")
    print(last_band.to_string(index=False))
    print(compare.to_string(index=False))


if __name__ == "__main__":
    main()
