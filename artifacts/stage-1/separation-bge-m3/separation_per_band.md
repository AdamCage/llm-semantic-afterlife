**separation_per_band** — Seed-separation contrast per turnover band. `d_within` is the mean cosine distance between trajectories sharing a semantic seed and differing only in their stochastic seed; `d_between` is the same across different semantic seeds. `gap` is their difference, with a 95% bootstrap interval resampled over trajectories rather than over pairs.

|   band |   d_within |   d_between |     gap |   gap_ci_low |   gap_ci_high | separated   |   n_within_pairs |   n_between_pairs |   n_boot_valid |
|-------:|-----------:|------------:|--------:|-------------:|--------------:|:------------|-----------------:|------------------:|---------------:|
|      0 |     0.2031 |      0.345  | 0.1419  |     0.1176   |       0.1655  | True        |              315 |               756 |           2000 |
|      2 |     0.2536 |      0.334  | 0.08036 |     0.04812  |       0.1108  | True        |              360 |               864 |           2000 |
|      4 |     0.2756 |      0.3097 | 0.0341  |     0.001115 |       0.07398 | True        |              360 |               864 |           2000 |
|      6 |     0.2792 |      0.298  | 0.01878 |    -0.01729  |       0.06831 | False       |              360 |               864 |           2000 |
|      8 |     0.2749 |      0.2913 | 0.01641 |    -0.02312  |       0.06733 | False       |              360 |               864 |           2000 |
|     10 |     0.2685 |      0.2798 | 0.01132 |    -0.0289   |       0.06776 | False       |              360 |               864 |           2000 |
|     12 |     0.2689 |      0.285  | 0.01609 |    -0.03668  |       0.09129 | False       |               40 |                96 |           2000 |
