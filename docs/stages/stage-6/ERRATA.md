# Errata (2026-09-06) — TMLR correctness pass (ADR-0019)

Closed `REPORT.md` numbers are not rewritten. Gemini embed `run_id`s
remain `s6-embed-third-space-20260906T082301Z-588eff8f` and
`s6-embed-third-space-20260906T082628Z-9077d587`.

## What changed

- F6 captions: `collapsed` $\to$ `no_detected_divergence`. A CI that
  includes $0$ is not occupancy of one lock and is not semantic collapse.
- Twin CI columns in
  [`twin_last_band.csv`](../../../artifacts/stage-6/occupancy/twin_last_band.csv)
  are not valid bootstrap intervals (ADR-0019 `set(chosen)`). Point
  $\Delta$ values are kept. CIs are not re-bootstrapped in this pass
  (embeddings absent from `state-latest`).
- Independent audit of F4 last-band *points* against the seed-pair
  matrix: signs agree; absolute difference $<0.002$
  ([`artifacts/tmlr-correctness/headline_audit.json`](../../../artifacts/tmlr-correctness/headline_audit.json)).
  Published gaps $0.201$ / $0.390$ / $0.150$ stand.

## ADR-0020 (2026-09-07)

Invalid F6 CI columns quarantined to `*.legacy_invalid.csv`. F4
leave-one-out and within-pair randomisation ($p=0.0001$ in each space,
$n_{\mathrm{perm}}=9999$) are tests on ten seed texts. Trajectory-bootstrap
CI recompute remains impossible: occupancy run directories are not
recoverable (ADR-0021).

## What did not change

- F4 trajectory-bootstrap CIs (multiplicity already correct).
- Sign agreement in three spaces; gemini lower bound $0.029$ is still
  an NHST pass, not architecture-independence.
- Hosted Stage 6 spend $\$0$.
