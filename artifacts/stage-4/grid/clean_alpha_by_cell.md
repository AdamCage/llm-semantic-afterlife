**clean_alpha_by_cell** — MSD α on the non-degenerate subset of each (W, T, embedding) cell. alpha_defined is false when n_clean < 2; those rows are not estimates.

| embedding      |    W |   temperature |   n_traj |   n_clean | alpha_defined   |   msd_alpha |   ci_low |   ci_high |
|:---------------|-----:|--------------:|---------:|----------:|:----------------|------------:|---------:|----------:|
| bge-m3         | 4096 |           0.3 |        4 |         0 | False           |    nan      | nan      |  nan      |
| bge-m3         | 4096 |           0.7 |        4 |         0 | False           |    nan      | nan      |  nan      |
| bge-m3         | 4096 |           1   |        4 |         0 | False           |    nan      | nan      |  nan      |
| bge-m3         | 4096 |           1.5 |        4 |         4 | True            |      0.1485 |   0.1396 |    0.1582 |
| bge-m3         | 8192 |           0.3 |        4 |         0 | False           |    nan      | nan      |  nan      |
| bge-m3         | 8192 |           0.7 |        4 |         0 | False           |    nan      | nan      |  nan      |
| bge-m3         | 8192 |           1   |        4 |         0 | False           |    nan      | nan      |  nan      |
| bge-m3         | 8192 |           1.5 |        4 |         2 | True            |      0.1463 |   0.0859 |    0.2067 |
| qwen3-embed-8b | 4096 |           0.3 |        4 |         0 | False           |    nan      | nan      |  nan      |
| qwen3-embed-8b | 4096 |           0.7 |        4 |         0 | False           |    nan      | nan      |  nan      |
| qwen3-embed-8b | 4096 |           1   |        4 |         0 | False           |    nan      | nan      |  nan      |
| qwen3-embed-8b | 4096 |           1.5 |        4 |         4 | True            |      0.2772 |   0.2406 |    0.3182 |
| qwen3-embed-8b | 8192 |           0.3 |        4 |         0 | False           |    nan      | nan      |  nan      |
| qwen3-embed-8b | 8192 |           0.7 |        4 |         0 | False           |    nan      | nan      |  nan      |
| qwen3-embed-8b | 8192 |           1   |        4 |         0 | False           |    nan      | nan      |  nan      |
| qwen3-embed-8b | 8192 |           1.5 |        4 |         2 | True            |      0.247  |   0.1722 |    0.3219 |
