# Stage 10 HANDOFF — next executor

## You are

Executor. Kickoff is on `stage-10`. Generate is **blocked** until
the human sees the estimate and says «да». Do not start S11. Do
not request review while `afterlife review --stage s10` fails.

## Already on disk

- Branch `stage-10` from `main` (`72b7072`).
- ADR-0028: second space is hosted `qwen3-embed-8b` (RouterAI /
  OpenRouter), $5 cap.
- YAML: `configs/stages/stage10_olmo/` (four NF4 rungs + Base/RLVR
  INT8 + `embed_bge.yaml` / `embed_qwen.yaml`).
- INT8 slugs: `pb-olmo3-7b-base-int8`, `pb-olmo3-7b-rlvr-int8` in
  `configs/models/generators_local_paperb.yaml`.
- PLAN / README / this file / `artifacts/stage-10/README.md`.

## Estimate (registered before generate)

Six generate YAMLs, fill=1: **180 traj**, 33.5M input / 8.85M
output tokens, **$0.00**. Hosted Qwen-embed cap $5, not in that
forecast. Wall-clock ~93 h exclusive (0.517 h/traj from
`s8-paperb-micro-olmo3-7b-base-20260910T232755Z-e3cc4b7f`).
Project remaining $189.46 / $200. CLI prints `stage budget not
declared` because `budget_usd: 0.0` is falsy; the ceiling is $0.

## After the human says «да»

1. WSL Ubuntu (`wsl -d Ubuntu`). Default distro is docker-desktop —
   do not use it.
2. Env:
   `UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife`
   `HF_HOME=/home/adam/hf-paperb`
   `AFTERLIFE_BUDGET_USD_TOTAL=200`
   Logs: `/home/adam/s10` (INT8 stdout flood).
3. One CUDA generate. `nvidia-smi` before each pass.
4. Order: Base NF4 → SFT → DPO → RLVR → Base INT8 → RLVR INT8
   (`scripts/s10_run_matrix.sh` or `s10_run_one.sh <yaml>`).
5. Resume only with `--resume-run`. Empty-completion FAILED trajs
   stay in the sample.
6. After each generate: `summarise_run.py`, then `embed` BGE, then
   hosted Qwen-embed (ADR-0028). Degeneracy before \(G_t\).
7. Confirmatory: \(G_t\) → \(\tau_{\mathrm{lock}}\). Last-band
   \(G_t>0\) is registers / loop families, not recovered semantics.
   Lock language: early-onset long-lived repetition lock — not
   “late lock”, not absorbing.
8. Two estimands in every lede: completer persistence **and**
   completion. Do not pool with Qwen.

## Stop-and-ask

Hosted $; INT8 OOM; thinking-storm; `T` above 12W; S11; F1 change;
second GPU generate; Think-line ids; pooling with Qwen; cutting `B`;
native-chat generate.

## Gate

`AFTERLIFE_BUDGET_USD_TOTAL=200 afterlife review --stage s10`
(not `--stage 10` — that looks at `runs/10/`).
