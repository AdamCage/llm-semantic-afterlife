**separation_per_band** — Seed-separation contrast per turnover band. `d_within` is the mean cosine distance between trajectories sharing a semantic seed and differing only in their stochastic seed; `d_between` is the same across different semantic seeds. `gap` is their difference, with a 95% bootstrap interval resampled over trajectories rather than over pairs.

|   band |   d_within |   d_between |     gap |   gap_ci_low |   gap_ci_high | separated   |   n_within_pairs |   n_between_pairs |   n_boot_valid |
|-------:|-----------:|------------:|--------:|-------------:|--------------:|:------------|-----------------:|------------------:|---------------:|
|      0 |     0.3261 |      0.5162 | 0.1901  |      0.1593  |        0.2218 | True        |             1758 |              1783 |           2000 |
|      2 |     0.3778 |      0.5092 | 0.1314  |      0.09499 |        0.1725 | True        |             1171 |              1217 |           2000 |
|      4 |     0.4079 |      0.518  | 0.11    |      0.06148 |        0.1645 | True        |              937 |              1000 |           2000 |
|      6 |     0.4268 |      0.5112 | 0.0844  |      0.03371 |        0.1472 | True        |              720 |               800 |           2000 |
|      8 |     0.4331 |      0.4998 | 0.06666 |      0.01786 |        0.1302 | True        |              720 |               800 |           2000 |
|     10 |     0.4357 |      0.498  | 0.06221 |      0.0172  |        0.1254 | True        |              675 |               750 |           2000 |
|     12 |     0.3993 |      0.4767 | 0.07743 |     -0.01413 |        0.2143 | False       |               25 |                30 |           1986 |
