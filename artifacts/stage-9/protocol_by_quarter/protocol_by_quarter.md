**protocol_by_quarter** — Block fill and stop rate by trajectory-quarter (four even step bins per trajectory, then mean across trajectories in the cell). Not a run-level mean.

| cell          | generate_run_id                                        |   quarter |   n_trajectories |   n_steps |   block_fill_mean |   block_fill_min |   stop_rate_mean |
|:--------------|:-------------------------------------------------------|----------:|-----------------:|----------:|------------------:|-----------------:|-----------------:|
| base-int8     | s9-paperb-qwen-base-int8-20260914T091655Z-11069a87     |         1 |               10 |        98 |            0.8395 |           0.006  |          0.2     |
| base-int8     | s9-paperb-qwen-base-int8-20260914T091655Z-11069a87     |         2 |                8 |        96 |            1      |           1      |          0       |
| base-int8     | s9-paperb-qwen-base-int8-20260914T091655Z-11069a87     |         3 |                8 |        96 |            1      |           1      |          0       |
| base-int8     | s9-paperb-qwen-base-int8-20260914T091655Z-11069a87     |         4 |                8 |        96 |            1      |           1      |          0       |
| base-nf4      | s9-paperb-qwen-base-nf4-20260912T014645Z-f55767bc      |         1 |               40 |       400 |            0.7731 |           0.004  |          0.2656  |
| base-nf4      | s9-paperb-qwen-base-nf4-20260912T014645Z-f55767bc      |         2 |               31 |       384 |            0.9766 |           0.8133 |          0.05442 |
| base-nf4      | s9-paperb-qwen-base-nf4-20260912T014645Z-f55767bc      |         3 |               33 |       387 |            0.9158 |           0.004  |          0.1201  |
| base-nf4      | s9-paperb-qwen-base-nf4-20260912T014645Z-f55767bc      |         4 |               31 |       382 |            0.9755 |           0.8223 |          0.05244 |
| instruct-int8 | s9-paperb-qwen-instruct-int8-20260912T180435Z-e9c7d498 |         1 |               10 |       109 |            1      |           1      |          0       |
| instruct-int8 | s9-paperb-qwen-instruct-int8-20260912T180435Z-e9c7d498 |         2 |               10 |       109 |            0.9869 |           0.869  |          0.1     |
| instruct-int8 | s9-paperb-qwen-instruct-int8-20260912T180435Z-e9c7d498 |         3 |               10 |       109 |            0.9058 |           0.058  |          0.1     |
| instruct-int8 | s9-paperb-qwen-instruct-int8-20260912T180435Z-e9c7d498 |         4 |                9 |       108 |            1      |           1      |          0       |
| instruct-nf4  | s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6  |         1 |               40 |       459 |            1      |           1      |          0       |
| instruct-nf4  | s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6  |         2 |               40 |       458 |            0.9794 |           0.176  |          0.025   |
| instruct-nf4  | s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6  |         3 |               40 |       458 |            0.9605 |           0.021  |          0.05    |
| instruct-nf4  | s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6  |         4 |               38 |       456 |            1      |           1      |          0       |
