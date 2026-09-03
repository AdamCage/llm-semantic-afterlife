**separation_per_band** — Seed-separation contrast per turnover band. `d_within` is the mean cosine distance between trajectories sharing a semantic seed and differing only in their stochastic seed; `d_between` is the same across different semantic seeds. `gap` is their difference, with a 95% bootstrap interval resampled over trajectories rather than over pairs.

|   band |   d_within |   d_between |    gap |   gap_ci_low |   gap_ci_high | separated   |   n_within_pairs |   n_between_pairs |   n_boot_valid |
|-------:|-----------:|------------:|-------:|-------------:|--------------:|:------------|-----------------:|------------------:|---------------:|
|      0 |     0.2927 |      0.6152 | 0.3225 |      0.09306 |        0.5197 | True        |               12 |                16 |           1991 |
|      2 |     0.3638 |      0.5774 | 0.2136 |      0.01665 |        0.4174 | True        |               24 |                32 |           1987 |
|      4 |     0.3574 |      0.585  | 0.2276 |      0.04015 |        0.5001 | True        |               24 |                32 |           1981 |
|      6 |     0.3522 |      0.5839 | 0.2317 |      0.04514 |        0.4798 | True        |               24 |                32 |           1982 |
|      8 |     0.3882 |      0.5825 | 0.1943 |      0.03231 |        0.4186 | True        |               24 |                32 |           1983 |
|     10 |     0.4257 |      0.5758 | 0.1501 |      0.02855 |        0.3659 | True        |               24 |                32 |           1988 |
|     12 |     0.4432 |      0.5461 | 0.1029 |     -0.06596 |        0.3335 | False       |               12 |                16 |           1988 |
