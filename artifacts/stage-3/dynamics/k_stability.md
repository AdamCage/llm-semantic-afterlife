**k_stability** — n_macro at K=50 and K=100 on every F4 cell. No process keeps the same n_macro across K and both embedding spaces. F7 is instability, reported as the result.

| generator           | embedding      |   K |   n_macro |   its_flat |   ck_pass |   validated |
|:--------------------|:---------------|----:|----------:|-----------:|----------:|------------:|
| or-qwen3-8b         | bge-m3         |  50 |         2 |          1 |         0 |           0 |
| or-qwen3-8b         | bge-m3         | 100 |         4 |          0 |         0 |           0 |
| or-qwen3-8b-prefill | bge-m3         |  50 |         4 |          0 |         0 |           0 |
| or-qwen3-8b-prefill | bge-m3         | 100 |         2 |          1 |         0 |           0 |
| or-qwen3-8b         | qwen3-embed-8b |  50 |         1 |          0 |         0 |           0 |
| or-qwen3-8b         | qwen3-embed-8b | 100 |         4 |          1 |         0 |           0 |
| or-qwen3-8b-prefill | qwen3-embed-8b |  50 |         1 |          0 |         0 |           0 |
| or-qwen3-8b-prefill | qwen3-embed-8b | 100 |         2 |          1 |         0 |           0 |
| or-gpt-oss-120b     | bge-m3         |  50 |         2 |          1 |         0 |           0 |
| or-gpt-oss-120b     | bge-m3         | 100 |         4 |          0 |         0 |           0 |
| or-gpt-oss-120b     | qwen3-embed-8b |  50 |         2 |          0 |         0 |           0 |
| or-gpt-oss-120b     | qwen3-embed-8b | 100 |         1 |          1 |         0 |           0 |
