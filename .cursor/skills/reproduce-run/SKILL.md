---
name: reproduce-run
description: Re-derive an existing run and diff it against the original to verify reproducibility, or diagnose why a run cannot be reproduced. Use when auditing a result, before publishing a stage, when a number looks suspicious, or when preparing the artifact release for reviewers.
---

# Reproducing a run

Reproducibility here is a measured property, not an assumption. LLM APIs are
only approximately deterministic, so we distinguish three levels and report
which one a given result achieves.

| Level | Meaning | How to verify |
| --- | --- | --- |
| **L3 — bit-exact replay** | same inputs, responses served from cache | `AFTERLIFE_EXECUTION_MODE=replay` |
| **L2 — analysis-exact** | analysis re-run on stored trajectories yields identical numbers | re-run the analysis pass |
| **L1 — statistically equivalent** | fresh generation reproduces the *conclusion* within CI | fresh run, compare distributions |

Every published claim must reach at least **L2**, and the paper reports
measured **L1** agreement for the headline results.

## Procedure

```bash
afterlife reproduce <run_id> --level replay     # L3
afterlife reproduce <run_id> --level analysis   # L2
afterlife reproduce <run_id> --level fresh      # L1 — costs money, estimate first
```

`reproduce` re-resolves the original config from the manifest, checks out
nothing (it uses the *current* code deliberately), re-executes, and writes a
diff report to `runs/<new_run_id>/REPRODUCTION.md` containing: config diff,
per-file hash comparison, and for numeric outputs the max absolute and relative
deviation per column.

## Interpreting failures

Work down this list; the causes are ordered by how often they are the culprit.

1. **Code changed since the original run.** Compare `git_sha` in both
   manifests. If analysis code changed, that is expected — decide whether the
   original number should be superseded, and if so re-run the whole stage pass,
   not just the failing cell.
2. **Provider drift.** Compare `provider` and `quantization` in the manifests.
   A router silently moving to a different endpoint or a different quantization
   changes outputs even with a fixed `seed`. This is why we pin
   `provider.only` + `allow_fallbacks=false`; if the recorded provider differs,
   the run is not comparable and must be re-generated, not patched.
3. **Sampling non-determinism.** Expected for LLM APIs. Quantify with
   `afterlife audit determinism` and report the rate; do not present a
   non-deterministic pipeline as deterministic.
4. **Tokenizer round-trip.** Check `tokenizer_roundtrip_ok` in the events log.
   A failure means the window boundary was not where the manifest claims, which
   invalidates the `W` semantics for that trajectory.
5. **Non-seeded randomness in analysis.** A bare `np.random` call, a
   set-iteration order, or a dict ordering leak. Fix the code, add a test, and
   note it in the stage report — a past result computed with unseeded
   randomness is not trustworthy and must be recomputed.

## After a successful audit

Record the achieved level in the stage report, and add the reproduction
`run_id` to `artifacts/stage-N/INDEX.md`. For the artifact release, include the
`.data.parquet` sidecars and the response cache for at least the headline
figures, so reviewers can reach L3 without an API key.
