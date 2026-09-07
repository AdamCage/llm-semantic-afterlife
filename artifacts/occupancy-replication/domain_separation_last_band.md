**domain_separation_last_band** — F4 last-band domain gap (D_between − D_within) with a 95% multiplicity-preserving trajectory bootstrap (n_boot=2000, seed=0) on the ADR-0022 replication generate. Ten domain seeds, two stochastic replicates. Twin pairs excluded. New run_ids.

| embedding        | scope     |   n_trajectories |   last_band |   d_within |   d_between |    gap |   gap_ci_low |   gap_ci_high | separated   |
|:-----------------|:----------|-----------------:|------------:|-----------:|------------:|-------:|-------------:|--------------:|:------------|
| bge-m3           | domain_10 |               20 |          12 |     0.2743 |      0.4823 | 0.208  |      0.09076 |        0.3145 | True        |
| qwen3-embed-8b   | domain_10 |               20 |          12 |     0.334  |      0.7343 | 0.4003 |      0.2208  |        0.5896 | True        |
| gemini-embed-001 | domain_10 |               20 |          12 |     0.1719 |      0.3241 | 0.1522 |      0.07306 |        0.2387 | True        |
