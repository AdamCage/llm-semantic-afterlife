**separation_per_band** — Seed-separation contrast per turnover band. `d_within` is the mean cosine distance between trajectories sharing a semantic seed and differing only in their stochastic seed; `d_between` is the same across different semantic seeds. `gap` is their difference, with a 95% bootstrap interval resampled over trajectories rather than over pairs.

|   band |   d_within |   d_between |    gap |   gap_ci_low |   gap_ci_high | separated   |   n_within_pairs |   n_between_pairs |   n_boot_valid |
|-------:|-----------:|------------:|-------:|-------------:|--------------:|:------------|-----------------:|------------------:|---------------:|
|      0 |     0.1515 |      0.841  | 0.6896 |       0.6531 |        0.7253 | True        |              392 |               448 |           2000 |
|      2 |     0.2365 |      0.8347 | 0.5982 |       0.5209 |        0.6702 | True        |              448 |               512 |           1999 |
|      4 |     0.2934 |      0.8333 | 0.5399 |       0.4516 |        0.6322 | True        |              448 |               512 |           2000 |
|      6 |     0.3108 |      0.8259 | 0.5151 |       0.4231 |        0.6059 | True        |              448 |               512 |           2000 |
|      8 |     0.3237 |      0.8247 | 0.5009 |       0.4067 |        0.5944 | True        |              448 |               512 |           2000 |
|     10 |     0.3459 |      0.8207 | 0.4748 |       0.3582 |        0.5894 | True        |              448 |               512 |           2000 |
|     12 |     0.3592 |      0.8142 | 0.455  |       0.3301 |        0.5797 | True        |               43 |                48 |           2000 |
