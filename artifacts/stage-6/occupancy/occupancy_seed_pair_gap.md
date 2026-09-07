**occupancy_seed_pair_gap** — F4 last-band gap from the committed seed-pair matrix: unweighted mean of finite within-seed diagonals versus unordered between-seed pairs. Inferential target is ten fixed seed texts, not a domain population. Trajectory-bootstrap CIs are not recomputed here (embeddings absent).

| embedding        |   d_within |   d_between |    gap |   n_within_pairs |   n_between_pairs | method                   |
|:-----------------|-----------:|------------:|-------:|-----------------:|------------------:|:-------------------------|
| bge-m3           |     0.2881 |      0.4876 | 0.1995 |                9 |                45 | unique_finite_seed_pairs |
| qwen3-embed-8b   |     0.3466 |      0.7367 | 0.3901 |                9 |                45 | unique_finite_seed_pairs |
| gemini-embed-001 |     0.2002 |      0.3487 | 0.1485 |                9 |                45 | unique_finite_seed_pairs |
