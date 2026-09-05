**separation_per_band** — Seed-separation contrast per turnover band. `d_within` is the mean cosine distance between trajectories sharing a semantic seed and differing only in their stochastic seed; `d_between` is the same across different semantic seeds. `gap` is their difference, with a 95% bootstrap interval resampled over trajectories rather than over pairs.

|   band |   d_within |   d_between |    gap |   gap_ci_low |   gap_ci_high | separated   |   n_within_pairs |   n_between_pairs |   n_boot_valid |
|-------:|-----------:|------------:|-------:|-------------:|--------------:|:------------|-----------------:|------------------:|---------------:|
|      0 |     0.1943 |      0.4796 | 0.2853 |       0.2339 |        0.3177 | True        |              120 |               240 |           1993 |
|      2 |     0.2351 |      0.4862 | 0.251  |       0.1825 |        0.3095 | True        |              128 |               256 |           1997 |
|      4 |     0.2386 |      0.4846 | 0.246  |       0.1556 |        0.3139 | True        |              128 |               256 |           1993 |
|      6 |     0.2404 |      0.497  | 0.2567 |       0.1682 |        0.3299 | True        |              128 |               256 |           1994 |
|      8 |     0.2529 |      0.5103 | 0.2574 |       0.1319 |        0.3418 | True        |              128 |               256 |           1998 |
|     10 |     0.2669 |      0.5144 | 0.2474 |       0.1208 |        0.3455 | True        |              128 |               256 |           1993 |
|     12 |     0.2109 |      0.501  | 0.2902 |       0.1668 |        0.3903 | True        |                4 |                 9 |           1803 |
