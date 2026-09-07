**occupancy_within_pair_randomization** — Within-pair randomisation on unique finite seed pairs. Each permutation assigns the observed number of within-pairs at random. p = (1+n_extreme)/(1+n_perm), n_perm=9999, seed=0. One-sided on gap. Not a trajectory bootstrap.

| embedding        |   d_within |   d_between |    gap |   n_within_pairs |   n_between_pairs |   n_perm |   n_extreme |   p_value | method                    |   seed |
|:-----------------|-----------:|------------:|-------:|-----------------:|------------------:|---------:|------------:|----------:|:--------------------------|-------:|
| bge-m3           |     0.2881 |      0.4876 | 0.1995 |                9 |                45 |     9999 |           0 |    0.0001 | within_pair_randomization |      0 |
| qwen3-embed-8b   |     0.3466 |      0.7367 | 0.3901 |                9 |                45 |     9999 |           0 |    0.0001 | within_pair_randomization |      0 |
| gemini-embed-001 |     0.2002 |      0.3487 | 0.1485 |                9 |                45 |     9999 |           0 |    0.0001 | within_pair_randomization |      0 |
