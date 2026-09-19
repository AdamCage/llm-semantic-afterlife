# Stage 10 HANDOFF — after phrase blockers

## You are

Waiting on the human. Scientific review **APPROVED WITH CHANGES**
([`REVIEW.md`](REVIEW.md)). Two phrase blockers applied in
[`REPORT.md`](REPORT.md) (2026-09-19): last-band intervals spelled
out; P3 scored **not established**; DPO quote is last-band `noise`
s2, not FAILED `finance` s1. Do not start S11. Do not merge until
the human authorises `--no-ff`. Empty-completion FAILED trajs stay
in the sample.

## Headline

On this OLMo 3 7B line, **two estimands**. Completion collapses
from Base through DPO and **floors** at DPO ≈ RLVR (NF4 empty
deaths 13 → 21 → 37 → 36 / 40). Lock-table trajectories lock
early; escape 0. Last-band \(G_t\): Base NF4 CIs exclude 0 in both
spaces; SFT BGE includes 0, SFT Qwen excludes 0; RLVR point `+`,
both CIs include 0, LOO skipped (P3 **not established**);
DPO last-band unidentified (not a sign flip). Do not pool with
S9 Qwen.

## Already on disk

- Branch `stage-10`. Close-out `4bc4695`; phrase-blocker edits
  uncommitted until the human asks.
- ADR-0028: hosted `qwen3-embed-8b`, realised **$0.00**.
- Generate: Base `…6d7b4be3` 27/13; SFT `…2b7b5b6e` 19/21;
  DPO `…64ad9f9f` 3/37; RLVR `…30b5b3fc` 4/36;
  Base INT8 `…2b2cdfd8` 5/5; RLVR INT8 `…7125ccca` 0/10 FAILED.
- Persistence (keep these): BGE `…183606`, `…183928`, `…184127`,
  `…184158`, `…184229`; Qwen `…184328`, `…185049`, `…185457`,
  `…185534`, `…185612`.
- Artifacts: [`artifacts/stage-10/`](../../../artifacts/stage-10/).
- Report: [`REPORT.md`](REPORT.md). Review: [`REVIEW.md`](REVIEW.md).

## Gate

Already green. Do not re-run unless a later edit breaks a check.

## Stop-and-ask (still)

Hosted $; INT8 OOM; thinking-storm; `T` above 12W; S11; F1
change; second GPU generate; Think-line ids; pooling with Qwen;
cutting `B`; native-chat generate; merge without the human’s
`--no-ff`.
