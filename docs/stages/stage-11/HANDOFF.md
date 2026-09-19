# Stage 11 HANDOFF — opened

Opened 2026-09-19 on branch `stage-11` from `main` `bec8e0b`.
Scientific contract: [`PLAN.md`](PLAN.md). Freeze: ADR-0023…0026,
ADR-0029.

## Do

- One `afterlife generate` at a time. `scripts/s11_run_matrix.sh`.
- Resume with `--resume-run` only, same `run_id`.
- Keep empty-completion FAILED cells. Do not retune sampling.
- Gemma last. OOM → stop that family; no E4B / `B` cut.
- Degeneracy before any published \(G_t\).
- Hosted Qwen-embed after local BGE; cap $5 (ADR-0029).

## Do not

- Start S12.
- Pool Ministral or Gemma with S9 Qwen or S10 OLMo.
- Execute native-chat (`build_request` still raw).
- Load `mistralai/Ministral-3-8B-Instruct-2512` (FP8) or Reasoning-2512.
- Swap Gemma for E4B.
- Launch a second `afterlife generate` on this GPU.
- Write `paper/main.tex`.
- Edit `.cursor/plans/paper_b_local_matrix_5105e6af.plan.md`.
- Change F1 / `N_confirm=3`.
- Call a lock absorbing, or last-band \(G_t>0\) recovered memory.
- Soften “CI includes 0” to “true on the point.”

## Env

WSL Ubuntu. `UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife`,
`HF_HOME=/home/adam/hf-paperb`, `AFTERLIFE_BUDGET_USD_TOTAL=200`.

## Return contract

- `status: opened` (PLAN + YAML + estimate; generate next)
- `run_ids: none` yet
- `blockers: none` for Ministral generate; Gemma IT empty-completion
  at `W=4096` is a recorded risk, not a blocker
- `next_agent: S11 generate`
- `do_not: S12; dual GPU jobs; native-chat; E4B; pooling`
