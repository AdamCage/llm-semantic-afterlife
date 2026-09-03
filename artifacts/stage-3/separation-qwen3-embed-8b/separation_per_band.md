**separation_per_band** — Seed-separation contrast per turnover band. `d_within` is the mean cosine distance between trajectories sharing a semantic seed and differing only in their stochastic seed; `d_between` is the same across different semantic seeds. `gap` is their difference, with a 95% bootstrap interval resampled over trajectories rather than over pairs.

|   band |   d_within |   d_between |    gap |   gap_ci_low |   gap_ci_high | separated   |   n_within_pairs |   n_between_pairs |   n_boot_valid |
|-------:|-----------:|------------:|-------:|-------------:|--------------:|:------------|-----------------:|------------------:|---------------:|
|      0 |     0.3093 |      0.7375 | 0.4282 |      0.1921  |        0.6413 | True        |               12 |                16 |           1991 |
|      2 |     0.4049 |      0.7271 | 0.3221 |      0.1312  |        0.5391 | True        |               24 |                32 |           1987 |
|      4 |     0.4263 |      0.7176 | 0.2913 |      0.063   |        0.5872 | True        |               24 |                32 |           1981 |
|      6 |     0.4303 |      0.7128 | 0.2825 |      0.04186 |        0.5798 | True        |               24 |                32 |           1982 |
|      8 |     0.4621 |      0.7085 | 0.2464 |      0.03006 |        0.517  | True        |               24 |                32 |           1983 |
|     10 |     0.4924 |      0.675  | 0.1826 |      0.02528 |        0.4068 | True        |               24 |                32 |           1988 |
|     12 |     0.5302 |      0.6358 | 0.1056 |     -0.1009  |        0.3876 | False       |               12 |                16 |           1988 |
