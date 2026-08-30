# S0.10–S0.11 — cross-provider endpoint selection

Run after Stage 0 closed, because the OpenRouter key became available and the
report required re-probing endpoints before Stage 1 locks its matrix.

**The question was not price.** Stage 0's finding F5 was that the cheapest healthy
endpoint throttles after ~4 consecutive steps, and F8 was that a single-call probe
cannot detect that. So every candidate below was measured with the *same*
multi-step trajectory (`W = 2048`, `B = 512`, `T = 8192`, physics seed,
`temperature = 0.7`, `raw_completion`), making the numbers directly comparable.

## Measured results

| Provider / endpoint | Model | Quant. | Median latency | Forecast h / full trajectory | Block fill (mean / min) | Stop rate | Prompt-token delta | USD/M in · out |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpenRouter `groq` | llama-3.1-8b-instruct | **unknown** | **0.87 s** | **0.06** | 0.932 / 0.607 | 0.278 | **35** | 0.050 · 0.080 |
| OpenRouter `deepinfra/fp8` | llama-3.1-8b-instruct | fp8 | 18.17 s | 1.29 | **1.000 / 1.000** | **0.000** | **0** | **0.020 · 0.040** |
| RouterAI `io-net` | mistral-nemo-12b | fp16 | 14.48 s | 1.03 | 0.877 / 0.045 | 0.263 | 3 | 0.061 · 0.223 |
| OpenRouter `io-net/fp16` | mistral-nemo-12b | fp16 | 33.56 s | 2.39 | 0.758 / 0.064 | 0.478 | 3 | 0.044 · 0.160 |
| OpenRouter `parasail/fp8` | mistral-nemo-12b | fp8 | — | — | 0.618 | — | 3 | 0.030 · 0.030 |
| RouterAI `parasail` | mistral-nemo-12b | fp8 | — | — | — | — | 3 | 0.042 · 0.042 |

Both Parasail endpoints failed to complete: 12 steps on OpenRouter (10 retries,
~8 min) and ~4 on RouterAI. The upstream shared pool throttles regardless of
which router fronts it, so **rate limits follow the upstream provider, not the
aggregator**.

Prices are consistently ~28–35% lower on OpenRouter for the same model family
once the currency conversion is applied correctly — see the note on that bug
below.

## Two findings that matter more than the ranking

### `deepinfra/fp8` removes the variable-stride limitation entirely

Block fill **1.000, minimum 1.000, stop rate 0.000, prompt-token delta 0**. That
combination means:

- **The stride is exactly `S = B`.** Stage 0's §0.1 caveat — that `S` is
  model-determined within `[0, B]` and only its distribution can be reported —
  does not apply to this endpoint. A constant stride restores the clean cost law,
  exact step/chunk alignment, and any claim that depends on a fixed `S`.
- **Nothing is added to the prompt.** A zero delta between our local token count
  and the provider's means the window we send is *exactly* the window, with no
  server-side template. For a paper whose subject is unforced continuation, that
  is a material provenance advantage, not a detail.
- Known fp8 quantization, and the cheapest endpoint on either provider.

### `groq` is 21× faster but reintroduces what DeepInfra removes

0.87 s per step against 18.17 s makes the difference between a 4-minute
trajectory and a 78-minute one — and therefore between a feasible and an
infeasible Stage 4 / Stage 5. But:

- **`prompt_token_delta = 35`**, constant. Thirty-five tokens of server-side
  scaffolding are prepended to what is nominally a raw completion. Constant, so
  the window stays well-defined and it is 0.4% of an 8192-token window — but we
  cannot see what those tokens say, and "unforced continuation" is the claim the
  paper rests on.
- **Quantization `unknown`**, so numerical precision is undocumented for a study
  about model-specific dynamics.
- Stop rate 0.278 and fill 0.932, so variable stride returns.

## A bug this audit exposed

The first cross-provider run reported OpenRouter prices **80× too low**, because
the audit applied the global rouble conversion rate to a provider that already
quotes USD. Currency is now a property of the client
(`InferenceClient.native_price_to_usd`), and audit artifacts are suffixed with
the provider name — previously the OpenRouter audit silently overwrote the
RouterAI table, which is how a stage report ends up citing numbers from a
provider it does not name.

## Cost implications for Stage 1

Recomputed with each endpoint's measured block fill, for the 48-trajectory core
arm at `W = 8192`, `T = 262144`:

| Endpoint | Forecast cost | Sequential wall clock | At concurrency 2 |
| --- | --- | --- | --- |
| `deepinfra/fp8` llama | **~$2.5** | ~62 h | ~31 h |
| `groq` llama | ~$6.3 | **~2.9 h** | ~1.5 h |
| RouterAI `io-net` mistral (the original plan) | $9.7 | ~49 h | ~25 h |

Both llama options are cheaper *and* better-behaved than the endpoint Stage 0
selected. The choice between them is speed against provenance, and it is a
decision for the human, not for the estimator.

## Recommendation

Use **`deepinfra/fp8` llama-3.1-8b-instruct as the primary generator** for
Stages 1–3, where per-trajectory cleanliness decides what the paper may claim: it
gives a constant stride, no hidden prompt scaffolding, documented quantization,
and the lowest price.

Keep **`groq` as a high-throughput arm** for Stages 4 and 5, where the number of
trajectories matters more than per-trajectory purity (a temperature × `W` sweep
and 200+ seeds per model are not otherwise reachable on this hardware), with an
explicit cross-endpoint consistency check on the overlapping configuration.

This also changes the model list: llama-3.1-8b-instruct enters as a third
architecture, which strengthens H1's model-specificity claim. Whether
mistral-nemo remains the wide arm or becomes a second family is part of the same
decision.
