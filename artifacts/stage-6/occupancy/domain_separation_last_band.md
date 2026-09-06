**domain_separation_last_band** — F4 last-band gap on the ten domain seeds in three spaces, with a 95% trajectory-bootstrap CI. Separated iff the CI excludes 0 from above. agrees_s5_sign compares each space to the S5 two-space sign (both S5 spaces were separated).

| embedding        | scope     |   n_trajectories |   last_band |   d_within |   d_between |    gap |   gap_ci_low |   gap_ci_high | separated   | s5_spaces_separated   | agrees_s5_sign   |
|:-----------------|:----------|-----------------:|------------:|-----------:|------------:|-------:|-------------:|--------------:|:------------|:----------------------|:-----------------|
| bge-m3           | domain_10 |               20 |          12 |     0.2881 |      0.489  | 0.2009 |      0.06524 |        0.3322 | True        | True                  | True             |
| qwen3-embed-8b   | domain_10 |               20 |          12 |     0.3466 |      0.7367 | 0.3902 |      0.1505  |        0.5934 | True        | True                  | True             |
| gemini-embed-001 | domain_10 |               20 |          12 |     0.2002 |      0.3502 | 0.15   |      0.02896 |        0.2659 | True        | True                  | True             |
