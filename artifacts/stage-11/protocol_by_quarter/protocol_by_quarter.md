**protocol_by_quarter** — Block fill and stop rate by trajectory-quarter (four even step bins per trajectory, then mean across trajectories in the cell). Not a run-level mean.

| cell               | generate_run_id                                             |   quarter |   n_trajectories |   n_steps |   block_fill_mean |   block_fill_min |   stop_rate_mean |
|:-------------------|:------------------------------------------------------------|----------:|-----------------:|----------:|------------------:|-----------------:|-----------------:|
| gemma-base         | s11-paperb-gemma4-base-nf4-20260921T003925Z-6cae9981        |         1 |               40 |       492 |            0.9291 |           0.004  |         0.07324  |
| gemma-base         | s11-paperb-gemma4-base-nf4-20260921T003925Z-6cae9981        |         2 |               38 |       456 |            0.9978 |           0.9173 |         0.002193 |
| gemma-base         | s11-paperb-gemma4-base-nf4-20260921T003925Z-6cae9981        |         3 |               38 |       462 |            1      |           1      |         0        |
| gemma-base         | s11-paperb-gemma4-base-nf4-20260921T003925Z-6cae9981        |         4 |               38 |       456 |            0.9964 |           0.9237 |         0.004386 |
| gemma-it           | s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427          |         1 |               40 |       102 |            0.754  |           0.002  |         0.4159   |
| gemma-it           | s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427          |         2 |               20 |        72 |            0.868  |           0.026  |         0.186    |
| gemma-it           | s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427          |         3 |               31 |        89 |            0.5977 |           0.002  |         0.5063   |
| gemma-it           | s11-paperb-gemma4-it-nf4-20260922T160427Z-3b5b9427          |         4 |               19 |        68 |            0.5979 |           0.002  |         0.55     |
| ministral-base     | s11-paperb-ministral-base-nf4-20260919T130616Z-5896956b     |         1 |               40 |       481 |            1      |           1      |         0        |
| ministral-base     | s11-paperb-ministral-base-nf4-20260919T130616Z-5896956b     |         2 |               40 |       480 |            1      |           1      |         0        |
| ministral-base     | s11-paperb-ministral-base-nf4-20260919T130616Z-5896956b     |         3 |               40 |       480 |            1      |           1      |         0        |
| ministral-base     | s11-paperb-ministral-base-nf4-20260919T130616Z-5896956b     |         4 |               40 |       480 |            1      |           1      |         0        |
| ministral-instruct | s11-paperb-ministral-instruct-nf4-20260920T065557Z-a3093ea2 |         1 |               40 |       493 |            0.9345 |           0.2417 |         0.06662  |
| ministral-instruct | s11-paperb-ministral-instruct-nf4-20260920T065557Z-a3093ea2 |         2 |               40 |       491 |            0.9906 |           0.6912 |         0.009479 |
| ministral-instruct | s11-paperb-ministral-instruct-nf4-20260920T065557Z-a3093ea2 |         3 |               40 |       493 |            1      |           1      |         0        |
| ministral-instruct | s11-paperb-ministral-instruct-nf4-20260920T065557Z-a3093ea2 |         4 |               40 |       490 |            1      |           1      |         0        |
