**separation_per_band** — Seed-separation contrast per turnover band. `d_within` is the mean cosine distance between trajectories sharing a semantic seed and differing only in their stochastic seed; `d_between` is the same across different semantic seeds. `gap` is their difference, with a 95% bootstrap interval resampled over trajectories rather than over pairs.

|   band |   d_within |   d_between |    gap |   gap_ci_low |   gap_ci_high | separated   |   n_within_pairs |   n_between_pairs |   n_boot_valid |
|-------:|-----------:|------------:|-------:|-------------:|--------------:|:------------|-----------------:|------------------:|---------------:|
|      0 |     0.1632 |      0.4804 | 0.3172 |       0.2916 |        0.3465 | True        |              392 |               448 |           2000 |
|      2 |     0.2234 |      0.4857 | 0.2624 |       0.2029 |        0.3223 | True        |              448 |               512 |           1999 |
|      4 |     0.2433 |      0.5016 | 0.2583 |       0.1921 |        0.3267 | True        |              448 |               512 |           2000 |
|      6 |     0.2452 |      0.5006 | 0.2553 |       0.2009 |        0.313  | True        |              448 |               512 |           2000 |
|      8 |     0.2549 |      0.5001 | 0.2452 |       0.1869 |        0.3053 | True        |              448 |               512 |           2000 |
|     10 |     0.269  |      0.5109 | 0.2419 |       0.1737 |        0.3117 | True        |              448 |               512 |           2000 |
|     12 |     0.279  |      0.5109 | 0.2319 |       0.1573 |        0.3117 | True        |               43 |                48 |           2000 |
