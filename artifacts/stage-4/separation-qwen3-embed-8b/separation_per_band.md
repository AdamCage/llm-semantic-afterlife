**separation_per_band** — Seed-separation contrast per turnover band. `d_within` is the mean cosine distance between trajectories sharing a semantic seed and differing only in their stochastic seed; `d_between` is the same across different semantic seeds. `gap` is their difference, with a 95% bootstrap interval resampled over trajectories rather than over pairs.

|   band |   d_within |   d_between |    gap |   gap_ci_low |   gap_ci_high | separated   |   n_within_pairs |   n_between_pairs |   n_boot_valid |
|-------:|-----------:|------------:|-------:|-------------:|--------------:|:------------|-----------------:|------------------:|---------------:|
|      0 |     0.1867 |      0.8295 | 0.6428 |       0.5822 |        0.679  | True        |              120 |               240 |           1993 |
|      2 |     0.252  |      0.8264 | 0.5744 |       0.4601 |        0.6667 | True        |              128 |               256 |           1997 |
|      4 |     0.2719 |      0.8285 | 0.5567 |       0.4276 |        0.6617 | True        |              128 |               256 |           1993 |
|      6 |     0.2913 |      0.827  | 0.5357 |       0.3759 |        0.6559 | True        |              128 |               256 |           1994 |
|      8 |     0.3075 |      0.8302 | 0.5226 |       0.335  |        0.6541 | True        |              128 |               256 |           1998 |
|     10 |     0.3208 |      0.8297 | 0.5088 |       0.3155 |        0.6632 | True        |              128 |               256 |           1993 |
|     12 |     0.2593 |      0.8427 | 0.5835 |       0.4257 |        0.7225 | True        |                4 |                 9 |           1803 |
