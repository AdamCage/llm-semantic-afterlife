# Figure shortlist (S7 notes; ADR-0019)

Include from `artifacts/`. Do not redraw. PCA/UMAP remain
illustrations only. F6 is not a headline figure.

## Headline (print)

| Figure | Path | What it shows | What it does not |
| --- | --- | --- | --- |
| S4 lock grid | `artifacts/stage-4/grid/looping_rate_vs_T.*` | T≤1.0 lock; Clopper–Pearson CI | a temperature phase transition |
| S4 clean α | `artifacts/stage-4/grid/clean_alpha_vs_T.*` | defined only at T=1.5 | H5 |
| S5 last-band domain gap | `artifacts/stage-5/occupancy/domain_separation_vs_turnover.*` | ten-domain gap CI excludes 0 in two spaces | recovered semantic memory |
| S6 three-space gap | `artifacts/stage-6/occupancy/domain_gap_three_spaces.*` | gemini 0.150 [0.029, 0.266] | architecture-independence |
| S6 last-band matrix | `artifacts/stage-6/occupancy/last_band_distance_matrix_gemini_embed_001.*` | pairwise distances | a cluster count |

## Support (not headline)

| Figure | Path | Note |
| --- | --- | --- |
| S5/S6 lock rate by seed | `*/occupancy/lock_rate_by_seed.*` | k/n; love 1/2 |
| Twin last-band points | `*/occupancy/twin_last_band.*` | n=2; CIs not bootstrap (ADR-0019) |
| Protocol by quarter | `*/occupancy/protocol_by_quarter.*` | fill/stop; forced continuation |
| Occupancy-repl F4 vs archival | `artifacts/occupancy-replication/domain_separation_last_band_vs_archival.*` | sign agreement; not a restore; n_within=6; do not swap in as the headline figure |
| S1 separation | `artifacts/stage-1/separation-bge-m3/` | 94% lock panel |
| S2 model-axis rates | `artifacts/stage-2/model-axis/rates/` | gemma 0/8; Clopper–Pearson |
| S3 k_stability | `artifacts/stage-3/dynamics/` | `validated=0` |

## Illustrations only (label as such)

Last-chunk PCA panels. No cluster count from 2-D.
