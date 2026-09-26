**persistence_gt_bands** — G_t = d_between − d_within per integer turnover band in qwen3-embed-8b, cell gemma-it. CI is seed-cluster bootstrap (ADR-0025), not Greenwood on 40 iid traj.

|   band_left |   band_right |   band_mid |   d_within |   d_between |          G |   n_within_pairs |   n_between_pairs |      G_lo |       G_hi |
|------------:|-------------:|-----------:|-----------:|------------:|-----------:|-----------------:|------------------:|----------:|-----------:|
|           1 |            2 |      1.414 |     0.3483 |      0.3889 |   0.04058  |                4 |                24 |  -0.03877 |   0.04058  |
|           2 |            3 |      2.449 |     0.3993 |      0.391  |  -0.008269 |                4 |                24 |  -0.09769 |   0.009654 |
|           3 |            4 |      3.464 |     0.3064 |      0.4206 |   0.1142   |                2 |                13 |  -0.08627 |   0.2615   |
|           4 |            5 |      4.472 |   nan      |      0.3748 | nan        |                0 |                 3 | nan       | nan        |
|           5 |            6 |      5.477 |   nan      |    nan      | nan        |                0 |                 0 | nan       | nan        |
|           6 |            7 |      6.481 |   nan      |    nan      | nan        |                0 |                 0 | nan       | nan        |
|           7 |            8 |      7.483 |   nan      |    nan      | nan        |                0 |                 0 | nan       | nan        |
|           8 |            9 |      8.485 |   nan      |    nan      | nan        |                0 |                 0 | nan       | nan        |
