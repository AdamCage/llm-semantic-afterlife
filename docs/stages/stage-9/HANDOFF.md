# Stage 9 — HANDOFF

Scientific contract: [`PLAN.md`](PLAN.md). Executor record:
[`REPORT.md`](REPORT.md). S8 close:
[`../stage-8/REPORT.md`](../stage-8/REPORT.md).

WSL: `UV_PROJECT_ENVIRONMENT=/home/adam/.venvs/llm-semantic-afterlife`,
`HF_HOME=/home/adam/hf-paperb`.

## Live generate

| Pass | Config | `run_id` | STATUS |
| --- | --- | --- | --- |
| S9.1 | `configs/stages/stage9_qwen/pb-qwen3-8b-instruct.yaml` | `s9-paperb-qwen-instruct-nf4-20260911T054758Z-c54e2ab6` | COMPLETED 38/40 |
| S9.2 | `configs/stages/stage9_qwen/pb-qwen3-8b-base.yaml` | `s9-paperb-qwen-base-nf4-20260912T014645Z-f55767bc` | COMPLETED 31/40 |
| S9.3 | `configs/stages/stage9_qwen/pb-qwen3-8b-instruct-int8.yaml` | `s9-paperb-qwen-instruct-int8-20260912T180435Z-e9c7d498` | COMPLETED 9/10 |
| S9.4 | `configs/stages/stage9_qwen/pb-qwen3-8b-base-int8.yaml` | `s9-paperb-qwen-base-int8-20260914T091655Z-11069a87` | COMPLETED 8/10 |

14 empty-completion FAILED cells kept. Native-chat not executed.

## Return contract

- `status:` closed 2026-09-16. Human authorised `--no-ff`. S10 is a new branch from `main`.
- `run_ids:` generate table + 8 embed + 4 degeneracy + 8 persistence (see REPORT)
- `blockers:` native-chat serialization (`build_request` still raw)
- `next_agent:` scientific supervisor after a green mechanical gate
- `do_not: S10; native-chat; dual GPU; OpenRouter Instruct; paper/main.tex`

## Do not

- Start S10
- Edit `.cursor/plans/paper_b_local_matrix_5105e6af.plan.md`
- Generate native-chat YAMLs until `build_request` is fixed
- Use `or-qwen3-8b` as Instruct
- Change F1 thresholds
- Launch a second generate
- Cut `B` / swap checkpoint
- Write `paper/main.tex`
- Commit unless the human asks
