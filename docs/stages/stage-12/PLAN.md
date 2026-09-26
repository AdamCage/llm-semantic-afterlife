# Stage 12 — Does a 12W lock escape by 5 million tokens?

**Status.** Opened 2026-09-26 after Stage 11 closed. Decisions:
[ADR-0023](../../decisions/ADR-0023-paper-b-local-four-family.md) F3,
[ADR-0025](../../decisions/ADR-0025-persistence-metrics-and-horizon-ladder.md).

If PLAN prose and YAML disagree, **YAML wins**. One local generator
at a time. L1 is not this stage. L2-persistence-to-lock is not this
stage. This stage does not pool families and does not call a lock
absorbing.

## 1. Question

For eight L0 trajectories that were still locked at 12W, does a
confirmed escape (`N_confirm=3` non-degenerate turnovers after the
lock) occur before the common token horizon near \(5\times 10^6\)
original generated tokens?

The confirmatory estimand is \(\tau_{\mathrm{escape}}\) only,
censored at the achieved \(T_{\min}\) inside the cohort. The
language of a finished cell with no escape is *no confirmed escape
through \(T\)*.

## 2. Entry state

From the closed S9–S11 lock tables (BGE rows; the classifier is
text-side). \(G_t\) was not used to choose checkpoints, seeds, or
descendants.

Checkpoint rule, applied after L0: rank checkpoints by the number
of trajectories that are confirmed-locked and not confirmed-escaped.
Take the top two. Ties break by stage order, then cell name.
That rank is Ministral Base NF4 (40 still locked) then Qwen
Instruct NF4 (38).

F3 on each of those checkpoints: order qualifying seeds by
median \(\tau_{\mathrm{lock}}\), ties by `seed_bank_v1` domain
order, then take the first seed and the seed at the median
position of that ordered list. Every locked descendant on both
checkpoints has median \(\tau_{\mathrm{lock}}=0.75\), so the order
is the domain order. Lowest is `physics`. The median position
among 10 seeds is `love`.

Per seed, two descendants: smallest \(\tau_{\mathrm{lock}}\), then
smaller stochastic id. All four on each seed tie at 0.75, so `s1`
and `s2`. All eight are still locked. Source runs:

- Ministral Base `s11-paperb-ministral-base-nf4-20260919T130616Z-5896956b`
- Qwen Instruct `s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6`

L2-persistence-to-lock stays closed: both checkpoints have locks
on every qualifying seed. L1 stays closed (supervisor-only).

## 3. Experiment matrix

Authoritative files under
[`configs/stages/stage12_horizon/`](../../../configs/stages/stage12_horizon/).
Continuation texts:
[`configs/seeds/seed_bank_s12_continuation.yaml`](../../../configs/seeds/seed_bank_s12_continuation.yaml).
`seed_bank_v1` texts are not edited. Each child YAML is one
trajectory. The prompt is the tail of the L0 trajectory; the
window keeps the last `W` tokens.

| Cell | Generator | Continuation id | L0 descendant |
| --- | --- | --- | --- |
| S12.1 | `pb-ministral-8b-base` | `mb-physics-s1` | physics s1 |
| S12.2 | same | `mb-physics-s2` | physics s2 |
| S12.3 | same | `mb-love-s1` | love s1 |
| S12.4 | same | `mb-love-s2` | love s2 |
| S12.5 | `pb-qwen3-8b-instruct` | `qi-physics-s1` | physics s1 |
| S12.6 | same | `qi-physics-s2` | physics s2 |
| S12.7 | same | `qi-love-s1` | love s1 |
| S12.8 | same | `qi-love-s2` | love s2 |

| knob | value |
| --- | --- |
| additional `T` | 4950016 (4834 blocks) |
| clock | L0 49152 + additional tokens, total ≤ 4999168 |
| `W` / `B` | 4096 / 1024 |
| temperature / `top_p` | 0.3 / 1.0 |
| protocol | `P1_reprompt`, `raw_bytes` |
| stochastic on the continuation | `{1}` (new draws; the L0 path is already in the tail) |
| `budget_usd` | 0 |

One cell expands to 1 trajectory
(`afterlife plan` on `mb-physics-s1.yaml`: 1 trajectory, 4,950,016
output tokens, $0). Eight cells: 39,600,128 additional output
tokens, $0.

Not in this opening: Gemma, OLMo, Qwen Base, Ministral Instruct,
INT8, native-chat, L1, fresh `seed_bank_v1` draws, hosted generate.

## 4. Computations

1. Round-robin generate (`scripts/s12_rotate.sh`). Each slice is
   48 completed steps on one trajectory, then the next. All eight
   stay within one slice of each other. Resume with `--resume-run`
   and the same id. One GPU process.
2. After the cohort stops (target reached, or a named stop at a
   common additional-token \(T_{\min}\)): degeneracy on each run.
3. \(\tau_{\mathrm{escape}}\) table. Clock origin is the L0 lock
   at 0.75W, not the first token of the continuation. A trajectory
   still locked at the stop is censored, not escaped.
4. Do not publish a 1220-turnover last-band \(G_t\) as if it were
   the L0 last band. Confirmatory output is the survival table.
5. Score this PLAN’s predictions. Do not start S13 from this folder
   before the report.

## 5. Exit criteria

| # | Criterion | Threshold |
| --- | --- | --- |
| E1 | Eight continuation runs | each id named; COMPLETED at the additional target, or stopped with the achieved token count named |
| E2 | Common horizon | within the cohort, reported \(\tau\) comparisons use \(T_{\min}\), not “whoever finished” |
| E3 | Round-robin | no trajectory is more than one 48-step slice ahead of the slowest at a planned stop |
| E4 | Estimand | table is \(\tau_{\mathrm{escape}}\) with a censoring flag; not a 1220-band \(G_t\) headline |
| E5 | Language | *no confirmed escape through \(T\)* where none was observed; the word absorbing is not used |
| E6 | Local | every generate step `served_provider=local` |
| E7 | Degeneracy | the escape label uses F1 + `N_confirm=3`, unchanged |
| E8 | Scope | L1 not run; L2-persistence-to-lock not run; families not pooled |
| E9 | Spend | generate $0 |

## 6. Pre-registered predictions

| # | Prediction | Confidence | Observed |
| --- | --- | ---: | --- |
| P1 | A majority of the eight still-locked continuations have no confirmed escape through the achieved \(T_{\min}\) | 0.55 | |
| P2 | Thinking tokens stay 0 on completed steps | 0.80 | |
| P3 | An empty-completion death of a continuation is kept and is not relabelled as escape | — | |
| P4 | L2-persistence-to-lock stays closed on these two checkpoints | 0.90 | |

P1 can be false. A mass of confirmed escapes is a finding, not a failed stage.

## 7. Budget and wall-clock

Generate forecast $0. Project ceiling $200; remaining about $189.
Hosted embed is not an exit criterion of this stage.

Additional tokens per trajectory: 4,950,016. At the S11 Ministral
step time of about 33 s, one trajectory is about 44 h and eight
round-robin trajectories are about **15 days** of exclusive GPU.
Qwen Instruct is re-timed on its first slice, not assumed equal.
A host stop is a censoring event at \(T_{\min}\), not a discarded
cohort.

Stop-and-ask: hosted spend, a second GPU generate, L1, changing
F1, swapping the F3 cohort after seeing the new text, calling the
lock absorbing.

## 8. Risks specific to this stage

| Risk | Mitigation |
| --- | --- |
| Sequential 5M censors the last trajectories | round-robin slices of 48 steps |
| Fresh seed instead of the locked window | continuation tails, not `seed_bank_v1` |
| Reading a new-run turnover 0 as the original lock time | clock adds the L0 49152 tokens; lock already at 0.75W |
| All \(\tau_{\mathrm{lock}}\) tied, so F3 looks arbitrary | positional median after the ADR tie-break, written here before generate |
| Cache of every W-prompt | prompts are hashed; full prompt text is not the scientific record |
| Two checkpoints on one GPU | the rotator runs one generate process |
