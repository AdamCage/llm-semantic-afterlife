**persistence_locks** — Prefix long-lived repetition lock (F1 + N_confirm=3) for gemma-it in local-bge-m3. Language: confirmed lock / no confirmed escape through T. Not an absorbing state.

| trajectory_id                              | seed_id   | confirmed_lock   | confirmed_escape   |   tau_lock |   tau_escape |
|:-------------------------------------------|:----------|:-----------------|:-------------------|-----------:|-------------:|
| pb-gemma4-12b-it__W4096__T0p3__biology__s1 | biology   | True             | False              |       2    |        nan   |
| pb-gemma4-12b-it__W4096__T0p3__biology__s2 | biology   | True             | True               |       0.75 |          2   |
| pb-gemma4-12b-it__W4096__T0p3__biology__s3 | biology   | True             | True               |       2.25 |          4   |
| pb-gemma4-12b-it__W4096__T0p3__noise__s2   | noise     | True             | True               |       1.75 |          2.5 |
| pb-gemma4-12b-it__W4096__T0p3__noise__s3   | noise     | True             | True               |       1.5  |          3   |
| pb-gemma4-12b-it__W4096__T0p3__physics__s3 | physics   | True             | False              |       2    |        nan   |
| pb-gemma4-12b-it__W4096__T0p3__recipe__s4  | recipe    | True             | False              |       0.75 |        nan   |
| pb-gemma4-12b-it__W4096__T0p3__war__s3     | war       | True             | False              |       0.75 |        nan   |
