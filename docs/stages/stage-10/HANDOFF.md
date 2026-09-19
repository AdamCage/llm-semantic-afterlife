# Stage 10 HANDOFF — scientific reviewer

## You are

Supervisor. Computations are **closed** (generate
`MATRIX DONE` 2026-09-18T15:04:04Z; analysis queue
`DONE` 2026-09-18T18:57:20Z). REPORT is written. Mechanical
gate **passed** (`afterlife review --stage s10`, exit 0; one
WARN on RLVR INT8 generate). Do not start S11. Do not merge
without scientific sign-off. Empty-completion FAILED trajs
stay in the sample.

## Headline

On this OLMo 3 7B line, post-training collapses **completion**
(NF4 empty deaths 13 → 21 → 37 → 36 / 40) and does not unlock
completers. Completers lock early; escape 0. Last-band \(G_t>0\)
where identified, both spaces; DPO last-band unidentified (not a
sign flip). Do not pool with S9 Qwen.

## Already on disk

- Branch `stage-10` from `main` (`72b7072`). Kickoff `f82e450`.
- ADR-0028: second space is hosted `qwen3-embed-8b`, $5 cap;
  realised **$0.00**.
- Generate: Base `…6d7b4be3` 27/13; SFT `…2b7b5b6e` 19/21;
  DPO `…64ad9f9f` 3/37; RLVR `…30b5b3fc` 4/36;
  Base INT8 `…2b2cdfd8` 5/5; RLVR INT8 `…7125ccca` 0/10 FAILED.
- Persistence (keep these): BGE `…183606`, `…183928`, `…184127`,
  `…184158`, `…184229`; Qwen `…184328`, `…185049`, `…185457`,
  `…185534`, `…185612`.
- SUPERSEDED: hung RLVR INT8 BGE; duplicate BGE persist from
  analysis-resume; RLVR INT8 persist both spaces (`min_chunks=8`).
- Artifacts: [`artifacts/stage-10/`](../../../artifacts/stage-10/).
- Report: [`REPORT.md`](REPORT.md).

## Gate

`AFTERLIFE_BUDGET_USD_TOTAL=200 afterlife review --stage s10`
(not `--stage 10` — that looks at `runs/10/`).

The only incomplete non-SUPERSEDED run is RLVR INT8 generate.
That is named empty-completion attrition (E2 PARTIAL), not a
dropped cell.

## Stop-and-ask (still)

Hosted $; INT8 OOM; thinking-storm; `T` above 12W; S11; F1
change; second GPU generate; Think-line ids; pooling with Qwen;
cutting `B`; native-chat generate; merge without scientific
sign-off.
