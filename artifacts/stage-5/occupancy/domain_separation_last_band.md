**domain_separation_last_band** — F4 last-band gap on the ten domain seeds, both spaces, with a 95% trajectory-bootstrap CI. Separated iff the CI excludes 0 from above.

| embedding      | scope     |   n_trajectories |   last_band |   d_within |   d_between |    gap |   gap_ci_low |   gap_ci_high | separated   |
|:---------------|:----------|-----------------:|------------:|-----------:|------------:|-------:|-------------:|--------------:|:------------|
| bge-m3         | domain_10 |               20 |          12 |     0.2881 |      0.489  | 0.2009 |      0.06524 |        0.3322 | True        |
| qwen3-embed-8b | domain_10 |               20 |          12 |     0.3466 |      0.7367 | 0.3902 |      0.1505  |        0.5934 | True        |
