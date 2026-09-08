**domain_separation_last_band_vs_archival** — Replication F4 last-band CIs beside the archival Stage 6 CSV (bge-m3 0.201 [0.065, 0.332], qwen3-embed-8b 0.390 [0.151, 0.593], gemini-embed-001 0.150 [0.029, 0.266]). Sign agreement means both CIs exclude 0. This table does not overwrite the archival files.

| embedding        |   archival_gap |   archival_gap_ci_low |   archival_gap_ci_high |   replication_gap |   replication_gap_ci_low |   replication_gap_ci_high | replication_separated   | sign_agrees   |
|:-----------------|---------------:|----------------------:|-----------------------:|------------------:|-------------------------:|--------------------------:|:------------------------|:--------------|
| bge-m3           |         0.2009 |               0.06524 |                 0.3322 |            0.208  |                  0.09076 |                    0.3145 | True                    | True          |
| qwen3-embed-8b   |         0.3902 |               0.1505  |                 0.5934 |            0.4003 |                  0.2208  |                    0.5896 | True                    | True          |
| gemini-embed-001 |         0.15   |               0.02896 |                 0.2659 |            0.1522 |                  0.07306 |                    0.2387 | True                    | True          |
