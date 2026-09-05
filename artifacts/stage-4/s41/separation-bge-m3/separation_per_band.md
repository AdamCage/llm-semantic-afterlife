**separation_per_band** — Seed-separation contrast per turnover band. `d_within` is the mean cosine distance between trajectories sharing a semantic seed and differing only in their stochastic seed; `d_between` is the same across different semantic seeds. `gap` is their difference, with a 95% bootstrap interval resampled over trajectories rather than over pairs.

|   band |   d_within |   d_between |    gap |   gap_ci_low |   gap_ci_high | separated   |   n_within_pairs |   n_between_pairs |   n_boot_valid |
|-------:|-----------:|------------:|-------:|-------------:|--------------:|:------------|-----------------:|------------------:|---------------:|
|      0 |     0.1861 |      0.4928 | 0.3067 |      0.2619  |        0.3584 | True        |               28 |                56 |           1883 |
|      2 |     0.2309 |      0.4911 | 0.2602 |      0.2122  |        0.3173 | True        |               32 |                64 |           1874 |
|      4 |     0.2356 |      0.4586 | 0.2229 |      0.1207  |        0.3264 | True        |               32 |                64 |           1869 |
|      6 |     0.2396 |      0.4546 | 0.2149 |      0.105   |        0.3574 | True        |               32 |                64 |           1875 |
|      8 |     0.264  |      0.4574 | 0.1934 |      0.07143 |        0.3966 | True        |               32 |                64 |           1872 |
|     10 |     0.2577 |      0.4668 | 0.2091 |      0.08315 |        0.3944 | True        |               32 |                64 |           1868 |
