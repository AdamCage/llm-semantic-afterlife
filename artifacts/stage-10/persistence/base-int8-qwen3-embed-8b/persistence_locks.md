**persistence_locks** — Prefix long-lived repetition lock (F1 + N_confirm=3) for base-int8 in qwen3-embed-8b. Language: confirmed lock / no confirmed escape through T. Not an absorbing state.

| trajectory_id                                   | seed_id   | confirmed_lock   | confirmed_escape   |   tau_lock | tau_escape   |
|:------------------------------------------------|:----------|:-----------------|:-------------------|-----------:|:-------------|
| pb-olmo3-7b-base-int8__W4096__T0p3__biology__s2 | biology   | True             | False              |       0.75 |              |
| pb-olmo3-7b-base-int8__W4096__T0p3__love__s1    | love      | True             | False              |       0.75 |              |
| pb-olmo3-7b-base-int8__W4096__T0p3__love__s2    | love      | True             | False              |       0.75 |              |
| pb-olmo3-7b-base-int8__W4096__T0p3__physics__s1 | physics   | True             | False              |       0.75 |              |
| pb-olmo3-7b-base-int8__W4096__T0p3__surreal__s1 | surreal   | True             | False              |       0.75 |              |
| pb-olmo3-7b-base-int8__W4096__T0p3__surreal__s2 | surreal   | True             | False              |       0.75 |              |
