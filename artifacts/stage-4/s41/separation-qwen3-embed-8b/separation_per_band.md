**separation_per_band** — Seed-separation contrast per turnover band. `d_within` is the mean cosine distance between trajectories sharing a semantic seed and differing only in their stochastic seed; `d_between` is the same across different semantic seeds. `gap` is their difference, with a 95% bootstrap interval resampled over trajectories rather than over pairs.

|   band |   d_within |   d_between |    gap |   gap_ci_low |   gap_ci_high | separated   |   n_within_pairs |   n_between_pairs |   n_boot_valid |
|-------:|-----------:|------------:|-------:|-------------:|--------------:|:------------|-----------------:|------------------:|---------------:|
|      0 |     0.1748 |      0.8496 | 0.6748 |       0.6427 |        0.7062 | True        |               28 |                56 |           1883 |
|      2 |     0.2582 |      0.8407 | 0.5825 |       0.5131 |        0.6435 | True        |               32 |                64 |           1874 |
|      4 |     0.2803 |      0.8047 | 0.5244 |       0.3958 |        0.6261 | True        |               32 |                64 |           1869 |
|      6 |     0.2797 |      0.7986 | 0.5189 |       0.3898 |        0.6527 | True        |               32 |                64 |           1875 |
|      8 |     0.3066 |      0.7991 | 0.4925 |       0.355  |        0.6682 | True        |               32 |                64 |           1872 |
|     10 |     0.2983 |      0.7994 | 0.5011 |       0.3714 |        0.6978 | True        |               32 |                64 |           1868 |
