**occupancy_leave_one_seed_out** — Leave-one-seed-out F4 gaps on the committed last-band seed-pair matrix. Each row drops one of the ten seed texts and recomputes mean(between) − mean(within) on the rest.

| embedding        | dropped_seed   |   d_within |   d_between |    gap |   n_within_pairs |   n_between_pairs |
|:-----------------|:---------------|-----------:|------------:|-------:|-----------------:|------------------:|
| bge-m3           | biology        |     0.2693 |      0.476  | 0.2067 |                8 |                36 |
| bge-m3           | finance        |     0.3006 |      0.4881 | 0.1875 |                8 |                36 |
| bge-m3           | love           |     0.2941 |      0.5033 | 0.2093 |                8 |                36 |
| bge-m3           | noise          |     0.2875 |      0.4913 | 0.2038 |                8 |                36 |
| bge-m3           | philosophy     |     0.3096 |      0.4878 | 0.1782 |                8 |                36 |
| bge-m3           | physics        |     0.2881 |      0.4907 | 0.2026 |                9 |                36 |
| bge-m3           | programming    |     0.2726 |      0.4791 | 0.2066 |                8 |                36 |
| bge-m3           | recipe         |     0.2978 |      0.4671 | 0.1692 |                8 |                36 |
| bge-m3           | surreal        |     0.2971 |      0.5007 | 0.2035 |                8 |                36 |
| bge-m3           | war            |     0.2645 |      0.4921 | 0.2276 |                8 |                36 |
| qwen3-embed-8b   | biology        |     0.3301 |      0.7362 | 0.406  |                8 |                36 |
| qwen3-embed-8b   | finance        |     0.372  |      0.7289 | 0.3568 |                8 |                36 |
| qwen3-embed-8b   | love           |     0.3335 |      0.7529 | 0.4194 |                8 |                36 |
| qwen3-embed-8b   | noise          |     0.3539 |      0.7436 | 0.3897 |                8 |                36 |
| qwen3-embed-8b   | philosophy     |     0.3778 |      0.734  | 0.3562 |                8 |                36 |
| qwen3-embed-8b   | physics        |     0.3466 |      0.7367 | 0.3902 |                9 |                36 |
| qwen3-embed-8b   | programming    |     0.3441 |      0.7273 | 0.3832 |                8 |                36 |
| qwen3-embed-8b   | recipe         |     0.3625 |      0.7225 | 0.36   |                8 |                36 |
| qwen3-embed-8b   | surreal        |     0.3452 |      0.7435 | 0.3983 |                8 |                36 |
| qwen3-embed-8b   | war            |     0.2997 |      0.7414 | 0.4417 |                8 |                36 |
| gemini-embed-001 | biology        |     0.1857 |      0.3414 | 0.1557 |                8 |                36 |
| gemini-embed-001 | finance        |     0.2094 |      0.3471 | 0.1378 |                8 |                36 |
| gemini-embed-001 | love           |     0.196  |      0.3591 | 0.1631 |                8 |                36 |
| gemini-embed-001 | noise          |     0.2018 |      0.3497 | 0.1479 |                8 |                36 |
| gemini-embed-001 | philosophy     |     0.2194 |      0.3474 | 0.128  |                8 |                36 |
| gemini-embed-001 | physics        |     0.2002 |      0.3521 | 0.1519 |                9 |                36 |
| gemini-embed-001 | programming    |     0.1963 |      0.3409 | 0.1446 |                8 |                36 |
| gemini-embed-001 | recipe         |     0.2128 |      0.3447 | 0.1319 |                8 |                36 |
| gemini-embed-001 | surreal        |     0.2033 |      0.355  | 0.1517 |                8 |                36 |
| gemini-embed-001 | war            |     0.1773 |      0.3497 | 0.1724 |                8 |                36 |
