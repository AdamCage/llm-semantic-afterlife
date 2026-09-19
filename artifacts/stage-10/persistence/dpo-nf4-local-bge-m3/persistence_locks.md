**persistence_locks** — Prefix long-lived repetition lock (F1 + N_confirm=3) for dpo-nf4 in local-bge-m3. Language: confirmed lock / no confirmed escape through T. Not an absorbing state.

| trajectory_id                             | seed_id   | confirmed_lock   | confirmed_escape   |   tau_lock | tau_escape   |
|:------------------------------------------|:----------|:-----------------|:-------------------|-----------:|:-------------|
| pb-olmo3-7b-dpo__W4096__T0p3__finance__s1 | finance   | True             | False              |       0.75 |              |
| pb-olmo3-7b-dpo__W4096__T0p3__love__s3    | love      | True             | False              |       0.75 |              |
| pb-olmo3-7b-dpo__W4096__T0p3__noise__s2   | noise     | True             | False              |       0.75 |              |
| pb-olmo3-7b-dpo__W4096__T0p3__noise__s3   | noise     | True             | False              |       0.75 |              |
| pb-olmo3-7b-dpo__W4096__T0p3__noise__s4   | noise     | True             | False              |       0.75 |              |
