# ADR-0023: Open Paper B / S8+ (local four-family programme)

Status: accepted
Date: 2026-09-09
Stage: S8+
Amends: the research-plan sentence “there is no S8”
Does not rewrite: closed S0–S7 reports, [ADR-0018](ADR-0018-s7-manuscript-from-closed-stages.md),
[ADR-0019](ADR-0019-tmlr-correctness-pass.md) (those records stay Paper A)

## Context

Paper A (S0–S7) is a closed existence case: on `or-qwen3-8b` under P1
`raw_completion`, `W=4096`, `B=1024`, `T=0.3`, 12 turnovers, late-window
chunks of ten `seed_bank_v1` domain seeds are ensemble-distinguishable in
three representation spaces. H1 is unsupported. A lock is not a validated
metastable semantic state. The hosted Qwen3-8B OpenRouter run is **not** a
matched Instruct half of a Base/Instruct contrast.

The research plan and ADR-0019 said there is no S8. That sentence was
correct for the Paper A writing pass. It is no longer the project state.

Paper B asks a different question, from [docs/backlog.md](../backlog.md):
*what determines the long-run dynamical regime of a self-conditioned LM
after complete prompt eviction*. The claim stays narrow. Not “semantic
attractors”, not “generic semantic memory”, not a property of all LLMs.

> In a fixed blockwise self-conditioning regime (P1), a finite-context
> LLM can retain a measurable dependence of late dynamics on the initial
> text many full window turnovers after physical eviction of the seed
> tokens. That dependence is realised mainly as a seed-conditioned choice
> of a late repeating regime. Paper B asks **how that regime changes
> with post-training and attention architecture**, and does not prove
> universality.

S9–S11 is a complete scientific story (anchor / post-training ladder /
replication+generalization). S12 is strengthening or a separate
*no confirmed escape through T*. S13 is synthesis. Do not wait on S12
to decide whether Paper B has a result.

## Decision

1. **Open S8+.** Paper A remains the closed S0–S7 record. Paper B is
   stages **S8–S13**. Closed reports are not rewritten. Old occupancy
   `run_id`s are not restored by regenerating under the same ids
   ([ADR-0021](ADR-0021-occupancy-record-not-recoverable.md)).
2. **Frozen stage order (do not reorder in a HANDOFF):**
   **S9 Qwen → S10 OLMo → S11 Ministral+Gemma → S12 horizon → S13.**
   S8 is harness and foundations only (no scientific claims, no 12W
   matrix). Do not start 5M / L2 before S9–S11 are closed.
3. **Ten local checkpoints, four families**, official BF16 (or
   BF16-equivalent) weights, one bitsandbytes NF4 recipe
   ([ADR-0024](ADR-0024-local-nf4-lifecycle.md)):
   - **Qwen3-8B** (`Qwen/Qwen3-8B-Base`, `Qwen/Qwen3-8B`) — causal
     anchor / post-training. Thinking off; think-arm parked.
   - **OLMo 3 7B Instruct line** (`allenai/Olmo-3-1025-7B`,
     `allenai/Olmo-3-7B-Instruct-SFT`, `allenai/Olmo-3-7B-Instruct-DPO`,
     `allenai/Olmo-3-7B-Instruct` as RLVR) — mechanistic ladder. Wave 0
     census confirms Hub ids. Think line parked. Not an architecture
     experiment at imposed `W=4096`.
   - **Ministral 3 8B** (`mistralai/Ministral-3-8B-Base-2512`,
     `mistralai/Ministral-3-8B-Instruct-2512-BF16`) — matched
     replication. Not FP8 Instruct. Not Reasoning-2512.
   - **Gemma 4 12B** (`google/gemma-4-12B`, `google/gemma-4-12B-it`) —
     architectural **generalization**, not a causal attention ablation.
     Gemma OOM → stop and ask; no silent substitute.
4. **Held constant on L0 (S9–S11):** P1 `raw_completion`, `unforced`,
   no system prompt; `W=4096`, `B_max=1024`, temperature `0.3`,
   `top_p=1.0`; ten domain seeds from `seed_bank_v1` (twins out of the
   F4-style domain gap); `stochastic_seeds: [1,2,3,4]`; primary
   serialization `raw_bytes` (same seed-token bytes for Base and
   Instruct). Native-chat is a reduced secondary arm, not pooled with
   `raw_bytes`. Protocol field in YAML is `P1_reprompt` only. P2 stays
   parked ([ADR-0017](ADR-0017-s6-third-space-occupancy-robustness.md)).
5. **Local embeddings** are the two primary Paper B spaces: BGE-M3 and
   Qwen3-Embedding-8B, both `api: local`. Gemini is optional hosted,
   estimate + human yes, not an S9–S11 exit criterion.
6. **Hosted OpenRouter Qwen is not the Instruct half** of any Paper B
   Δ. Discovery stays Paper A; local Qwen Instruct is a controlled
   replication, not a restore.
7. **Money.** Local generate is $0 ledger USD. Project ceiling $200
   ([ADR-0013](ADR-0013-project-ceiling-200.md)) still binds any hosted
   call. Do not raise it. HF weight download is disk, not ledger.
8. **Freeze block F1–F4** below is locked before any Paper B generate.
   Changing any item after seeing S9–S12 data requires a new ADR and
   reclassifies the affected analysis as exploratory, not confirmatory.

### Freeze block (locked)

#### F1. Degeneracy construct + `N_confirm = 3`

Copy of the current calibrated defaults in
[`degeneracy.py`](../../src/semantic_afterlife/analysis/degeneracy.py)
`DegeneracyParams` (chunk=1024, same tokenizer-independent text
measures):

- `ngram = 3`
- `loop_repetition_threshold = 0.083`
- `loop_chunk_fraction = 0.5`
- `shingle_n = 5`
- `fixed_point_threshold = 0.0122`
- `novelty_threshold = 0.872`
- `self_similarity_threshold = 0.98` (only if embeddings are supplied;
  not the sole lock criterion)
- Trajectory `degenerate` := looping **or** late-window fixed-point, as
  in the code now
- **`N_confirm = 3`:** lock := ≥3 consecutive turnovers
  `degenerate=true`; escape := ≥3 consecutive turnovers
  `degenerate=false` after a confirmed lock
- Exact-cycle hash is **not** part of the lock/escape verdict

**Forbidden:** changing thresholds, `N_confirm`, `chunk_size`, or the
definition of `degenerate` after seeing S9–S12 results. Re-calibrate
(`scripts/calibrate_degeneracy.py`) only if chunk or tokenizer is
changed first — that is a new ADR **before** generate, not mid-stage.

#### F2. Five INT8 seeds — chosen now, before NF4 Paper B

Mechanical rule, not an S5 lock-rate pick: **even indices 0,2,4,6,8**
among the ten domain ids in
[`seed_bank_v1.yaml`](../../configs/seeds/seed_bank_v1.yaml) order,
twins excluded.

Frozen list:

- `physics`
- `biology`
- `love`
- `programming`
- `surreal`

INT8 descendants: **`s1`, `s2`** (the first two of `{1,2,3,4}`).
Total 5×2×2 = 20 trajectories (Base and Instruct). Do not substitute a
seed after seeing NF4 \(G_t\) or lock.

Native-chat reduced (Qwen and Ministral): the first two INT8 seeds ×
the same `s1,s2` = **`physics`, `biology`**. Nested in the INT8 list
so a third arbitrary set is not invented.

#### F3. L2 locked-seed rule — no hand selection

On each checkpoint, **after** L0, among seeds with ≥1 descendant that
reached confirmed lock (`N_confirm=3`):

1. Seed-level \(\tau_{\mathrm{lock}}\) := **median** time-to-confirmed-lock
   over that seed’s locked descendants (unlocked descendants are not in
   the median).
2. Take the seed with the **lowest** \(\tau_{\mathrm{lock}}\) and the
   seed with the **median** \(\tau_{\mathrm{lock}}\) in this qualifying
   set.
3. Ties: earlier in `seed_bank_v1.yaml` domain order.
4. If exactly 2 qualifying seeds — both. If 1 — L2-escape is PARTIAL
   on that one seed; do not substitute an unlocked seed. If 0 — **no**
   L2-escape on that checkpoint; only optional L2-persistence-to-lock
   may be considered.
5. Per chosen seed — 2 descendants: prefer already locked (`s` with
   smaller \(\tau_{\mathrm{lock}}\); tie → smaller stochastic id). Do
   not pick the “prettiest” late text.

Forbidden to look at UMAP / fingerprint labels / \(G_t\) when selecting.

#### F4. Primary estimands (confirmatory vs exploratory)

**L0 / S9–S11 (importance order, confirmatory):**

1. \(G_t\) — seed-conditioned representation gap vs turnover (two local
   spaces, seed-cluster bootstrap, LOO).
2. \(\tau_{\mathrm{lock}}\) / prefix lock dynamics — time-to-confirmed-lock,
   counts by seed.
3. Fingerprint agreement — within-seed vs between-seed agreement and
   counts of recurrent fingerprints.

**L2 (separate confirmatory, S12 only):**

1. \(\tau_{\mathrm{escape}}\) — time from confirmed lock to confirmed
   escape, censored at the common \(T_{\min}\).

Everything else is exploratory until a separate ADR **before** analysis
promotes it: native-chat Δ, INT8 concordance (limitations, not a third
L0 headline), period-hash mutations, MI, MSM, MSD α, L1 48W,
L2-persistence-to-lock, Gemma sliding-window storytelling beyond
“did not replicate / full attention on every layer is not necessary”.

If thirty figures appear, confirmatory are only these 2–3 (L0) plus
\(\tau_{\mathrm{escape}}\) (L2). Estimator definitions:
[ADR-0025](ADR-0025-persistence-metrics-and-horizon-ladder.md).

## Alternatives considered

- **Keep “there is no S8” and treat Paper B as backlog only.**
  Rejected: the human opened a local four-family programme. The plan
  sentence would be false.
- **One mega-ADR for models + quant + estimators + seed-bank prose.**
  Rejected: four separable decisions (this file, 0024, 0025, 0026).
- **Start at S12 / 5M.** Rejected: 12W is the comparable primary
  horizon; 5M is a rare-event / waiting-time arm after L0.
- **Use hosted OpenRouter Qwen as the Instruct cell.** Rejected:
  different serving stack, lost F4 vectors, not a matched Base pair.
- **Pool families into one “instruct effect”.** Rejected: Qwen and
  Ministral signs are compared, not averaged. OLMo is not pooled with
  Qwen.
- **Call Gemma a causal attention ablation.** Rejected: family,
  training, and size differ at once. Generalization only.

## Consequences

- [`docs/research-plan.md`](../research-plan.md) now has S8+.
- S8 YAML is smoke-scale only
  ([`configs/stages/stage8_paperb_foundations.yaml`](../../configs/stages/stage8_paperb_foundations.yaml)).
  The 12W matrix lives in later stage configs, not this one.
- Seed-bank *texts* are unchanged. Constraint #2 rationale is corrected
  in [ADR-0026](ADR-0026-seed-bank-v1-rationale-not-identification.md).
- Degeneracy thresholds in this ADR match code at freeze time. Code
  must not drift without a new ADR.
- Wave 0 census may correct Hub ids / revisions; a pin change before
  first generate is an amendment note, not a silent swap after data.

## Reversal cost

High after S9 generate starts: the confirmatory object is this matrix
and these estimands. Before S9, revert by a superseding ADR and leave
S8 harness code in place if it is still useful. Do not delete closed
S0–S7 artifacts.
