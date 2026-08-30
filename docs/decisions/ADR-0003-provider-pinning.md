# ADR-0003: RouterAI as primary provider, with hard endpoint pinning

Status: accepted
Date: 2026-08-30
Stage: S0

## Context

Generation runs through an aggregator. Aggregators load-balance across upstream
providers for the same model ID, and those providers can differ in quantization
(`fp8` vs. `bf16`), context limit, and supported parameters. For this project
that is not a latency detail: if the router silently switches endpoint
mid-experiment, **the generator we are studying changes**, and trajectories from
before and after are not samples of the same process.

RouterAI (`https://routerai.ru/api/v1`) is OpenAI-compatible and, per its
documentation, supports:

- `provider.order` / `only` / `ignore` — routing *preferences*, explicitly
  documented as **not** hard constraints: a fallback attempt after an upstream
  failure may be served outside the list.
- `provider.allow_fallbacks: false` — returns `404` instead of serving from
  outside the preference set. This is what converts a preference into a
  constraint.
- `provider.country` — documented as always enforced, including on retries.
- `GET /models/{author}/{slug}/endpoints` — per-endpoint `tag`, `quantization`,
  `context_length`, `max_completion_tokens`, `supported_parameters`,
  `supported_apis`, `status`, and rouble pricing.
- `seed`, `logprobs`/`top_logprobs`, and a cheaper `service_tier: flex`.

The user holds a RouterAI key; the OpenRouter key is not yet available.

## Decision

1. RouterAI is the primary provider. OpenRouter is implemented behind the same
   interface for Stage 6 cross-provider replication and is not required earlier.
2. Every generation request pins **both** `provider.only=[slug]` **and**
   `provider.allow_fallbacks=false`. A `404` is preferred over a silently
   substituted provider — failing loudly is the point.
3. The endpoint list is fetched and snapshotted per stage into the run manifest:
   provider tag, quantization, context length, supported parameters, and price.
   Prices are converted to USD with a per-stage pinned `usd_per_rub`, which is
   itself recorded.
4. The provider **actually served** is read back from every response and
   compared with the pinned value. A mismatch marks the trajectory `SUSPECT`
   and it is regenerated, never patched.
5. Determinism is measured rather than assumed: `afterlife audit determinism`
   repeats identical seeded requests and reports exact- and near-match rates per
   model and endpoint. The paper reports these rates.
6. `service_tier: flex` is used where the endpoint supports it (≈2× cheaper),
   recorded per run, and held constant within a comparison.

## Alternatives considered

- **Direct provider APIs** (Together, DeepInfra, Fireworks…). Strongest control
  and no router in the path, but multiple accounts, multiple billing
  relationships, and rouble payment friction. Kept as an escalation if pinning
  proves unreliable in S0.
- **No pinning.** Cheaper and simpler; makes the experiment unreproducible in
  the one way that matters most. Rejected.
- **Local inference for everything.** No GPU. Infeasible at the required scale.

## Consequences

- S0 must include a real capability audit; documented support is not evidence.
- A `404` from strict pinning is a *correct* outcome and must be surfaced clearly
  rather than retried into a fallback.
- Costs are natively in RUB; a single pinned conversion rate is recorded per run
  so that reported USD figures are reconstructible.
- If S0 shows pinning is not honoured in practice, this ADR is superseded and
  the escalation path is direct provider APIs for the headline models.

## Reversal cost

Low at the code level (providers sit behind one interface). High at the data
level: any change of served endpoint requires regenerating the affected
trajectories.
