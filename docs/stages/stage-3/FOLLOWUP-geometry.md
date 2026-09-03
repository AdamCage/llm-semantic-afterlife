# S3.0 follow-up — geometry and seed-separation (2026-09-03)

Dated addendum on the RouterAI embed
`s3-embed-local-base-embed-20260902T051805Z-2ce86473`.
It does **not** rewrite the Stage 3 opening
([`REPORT.md`](REPORT.md), ADR-0012). It does **not** support H3 or H2.
`W = 256` still does not transfer to `W = 4096`.

Project ceiling is **$200** (ADR-0013). This pass spent **$0.00**.

## Runs

| pass | `run_id` | space |
| --- | --- | --- |
| geometry | `s3-geometry-bge-m3-20260903T102912Z-f0a1b50e` | bge-m3 |
| geometry | `s3-geometry-qwen3-embed-8b-20260903T102939Z-26a974ee` | qwen3-embed-8b |
| separation | `s3-separation-bge-m3-20260903T103004Z-9ce0ccd7` | bge-m3 |
| separation | `s3-separation-qwen3-embed-8b-20260903T103008Z-8a7a3e1f` | qwen3-embed-8b |

Degeneracy was recomputed from the source chunks
(`s3-local-base-20260901T184812Z-cc80633b`) and joined before any
exponent was written. Same verdict as
`s3-degeneracy-20260901T193542Z-f76d2086`: **8/8 degenerate**,
looping fraction 1.0.

Burn-in: 1.0 turnover. 11 post-horizon chunks per trajectory.
`chunk_size = W = 256`.

## Geometry

Ensemble MSD α (the number the figure prints) is **not** a confinement
result:

| space | ensemble α ± SD | range |
| --- | --- | --- |
| bge-m3 | 0.358 ± 0.513 | −0.10 … 1.20 |
| qwen3-embed-8b | 0.301 ± 0.367 | −0.09 … 0.81 |

Every row is a loop. A confined MSD of a loop is the Stage 1 trap.

T=0.3 physics s1 and s2 remain **bit-identical** on the surface metrics
and nearly identical on the geometry scalars (effective n = 1 at that
cell). T=0.3 surreal s1 is a frozen point (bge step displacement
2×10⁻⁷, plateau 2×10⁻⁶) whose α = 1.20, r² = 0.999 is a log–log fit
to near-zero MSD, not ballistic motion. T=1.0 sits farther from its
own origin (final distance 0.28–0.50) because it is a *different*
lock (`Deformation phase.`, `Is This`, `I I`, `/1/1`), still a loop.

Figures: [`artifacts/stage-3/geometry-bge-m3/`](../../../artifacts/stage-3/geometry-bge-m3/),
[`geometry-qwen3-embed-8b/`](../../../artifacts/stage-3/geometry-qwen3-embed-8b/).
PCA panels are illustrations only.

## Seed-separation

The CLI object pools all eight trajectories. `D_within` is defined as
same semantic seed, different stochastic seed — **temperature is not
a pairing key**. Of 144 within pair-rows, **120 are cross-T** (0.3 vs
1.0) and 24 are same-T.

| space | last-band gap | 95% CI | `separated_at_last_band` | post-horizon mean gap |
| --- | --- | --- | --- | --- |
| bge-m3 | 0.103 | [−0.066, 0.333] | **false** | 0.187 |
| qwen3-embed-8b | 0.106 | [−0.101, 0.388] | **false** | 0.238 |

Earlier bands mark `separated=true` because the published `D_within`
is a mixture of (a) the bit-identical T=0.3 physics pair and (b)
cross-T pairs of two different locks of the same seed. Cross-T within
mean distance is 0.44 (bge) / 0.50 (qwen); same-T within is 0.07 /
0.11. The decaying gap in the published table is partly that mix
inflating `D_within`, not seed information leaving the window.

A same-T-only contrast (diagnostic, **not** the CLI object; 2–4 within
rows per band) stays large (~0.55 / ~0.63). That is two different
repeated strings (physics seed-echo vs surreal lock), not H2.

Figures: [`artifacts/stage-3/separation-bge-m3/`](../../../artifacts/stage-3/separation-bge-m3/),
[`separation-qwen3-embed-8b/`](../../../artifacts/stage-3/separation-qwen3-embed-8b/).

## Spend

$0.00. Project ledger **$11.57 of $200**. OpenRouter not called.

## What this does not establish

- H3 (confinement) or H5 (temperature → diffusion). T=1.0 is a
  different lock, not a diffusion regime.
- H2 (seed half-life). Last-band CLI gap CI includes 0; a gap between
  loops is not recoverable seed identity.
- Transfer to `W = 4096` or to instruct models.
- A Stage 4 generate-yes. ADR-0013 raised the ceiling; it did not
  authorise the written $120 sweep.
