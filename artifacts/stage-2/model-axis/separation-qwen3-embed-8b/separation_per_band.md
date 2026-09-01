**separation_per_band** — Seed-separation contrast per turnover band. `d_within` is the mean cosine distance between trajectories sharing a semantic seed and differing only in their stochastic seed; `d_between` is the same across different semantic seeds. `gap` is their difference, with a 95% bootstrap interval resampled over trajectories rather than over pairs.

|   band |   d_within |   d_between |    gap |   gap_ci_low |   gap_ci_high | separated   |   n_within_pairs |   n_between_pairs |   n_boot_valid |
|-------:|-----------:|------------:|-------:|-------------:|--------------:|:------------|-----------------:|------------------:|---------------:|
|      0 |     0.36   |      0.8044 | 0.4444 |      0.372   |        0.5121 | True        |             1758 |              1783 |           2000 |
|      2 |     0.4412 |      0.7648 | 0.3236 |      0.2509  |        0.3973 | True        |             1171 |              1217 |           2000 |
|      4 |     0.5214 |      0.7658 | 0.2444 |      0.1366  |        0.3484 | True        |              937 |              1000 |           2000 |
|      6 |     0.5534 |      0.7416 | 0.1882 |      0.08072 |        0.3054 | True        |              720 |               800 |           2000 |
|      8 |     0.544  |      0.7185 | 0.1745 |      0.06522 |        0.3038 | True        |              720 |               800 |           2000 |
|     10 |     0.5513 |      0.7141 | 0.1628 |      0.06291 |        0.2827 | True        |              675 |               750 |           2000 |
|     12 |     0.492  |      0.6661 | 0.1741 |      0.03874 |        0.3976 | True        |               25 |                30 |           1986 |
