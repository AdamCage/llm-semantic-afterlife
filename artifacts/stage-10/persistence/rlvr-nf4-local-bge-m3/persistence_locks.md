**persistence_locks** — Prefix long-lived repetition lock (F1 + N_confirm=3) for rlvr-nf4 in local-bge-m3. Language: confirmed lock / no confirmed escape through T. Not an absorbing state.

| trajectory_id                             | seed_id   | confirmed_lock   | confirmed_escape   |   tau_lock | tau_escape   |
|:------------------------------------------|:----------|:-----------------|:-------------------|-----------:|:-------------|
| pb-olmo3-7b-rlvr__W4096__T0p3__noise__s1  | noise     | True             | False              |       0.75 |              |
| pb-olmo3-7b-rlvr__W4096__T0p3__noise__s2  | noise     | True             | False              |       0.75 |              |
| pb-olmo3-7b-rlvr__W4096__T0p3__noise__s3  | noise     | True             | False              |       0.75 |              |
| pb-olmo3-7b-rlvr__W4096__T0p3__noise__s4  | noise     | True             | False              |       0.75 |              |
| pb-olmo3-7b-rlvr__W4096__T0p3__recipe__s3 | recipe    | True             | False              |       1.5  |              |
