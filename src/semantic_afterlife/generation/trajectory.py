"""The trajectory runner.

One trajectory = one initial condition advanced for ``T`` generated tokens under
protocol P1. Strictly sequential internally (step ``t+1`` consumes step ``t``);
parallelism happens across trajectories in :func:`run_experiment`.

Two properties matter more than speed here:

* **Resumability.** A run lasts hours on a laptop that may be closed. Every step
  is appended to ``*.steps.jsonl`` before the next one begins, and a restart
  replays that file to rebuild byte-identical state.
* **Failure isolation.** A dead trajectory is recorded as ``FAILED`` and the
  batch continues. Dropping it silently would bias every statistic computed over
  the ensemble.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

import orjson

from ..config import (
    EmbeddingConfig,
    ExperimentConfig,
    GeneratorConfig,
    SamplingConfig,
    SeedSpec,
    Settings,
    WindowConfig,
)
from ..costs import estimate_request_usd
from ..errors import ProviderError, TrajectoryFailure, WindowProtocolError
from ..hashing import sha256_text
from ..ledger import Ledger
from ..logging_utils import EventLogger, get_logger
from ..paths import RunPaths
from ..providers import CompletionRequest, InferenceClient
from ..tokenization import Tokenizer
from .window import ChunkRecord, SlidingWindow, TokenChunker, TrajectoryAccumulator

logger = get_logger("generation")

#: A model that returns nothing this many times in a row is not free-running.
MAX_CONSECUTIVE_EMPTY = 5


def trajectory_id(
    *,
    generator: str,
    W: int,
    temperature: float,
    semantic_seed: str,
    stochastic_seed: int,
) -> str:
    """Human-readable, collision-free identifier used in filenames and figures."""
    temp = f"{temperature:g}".replace(".", "p")
    return f"{generator}__W{W}__T{temp}__{semantic_seed}__s{stochastic_seed}"


def step_seed(stochastic_seed: int, step: int) -> int:
    """Per-step sampling seed, derived deterministically from the trajectory seed.

    A single fixed seed for the whole trajectory would make any revisited prompt
    produce a byte-identical continuation, turning a near-recurrence into an
    exact cycle — a harness artifact indistinguishable from a real fixed point.
    Varying the seed per step removes that artifact while keeping the whole
    trajectory reproducible from ``(stochastic_seed, step)``.
    """
    return (stochastic_seed * 1_000_003 + step * 31 + 17) % (2**31 - 1)


def build_request(
    generator: GeneratorConfig,
    sampling: SamplingConfig,
    *,
    prompt: str,
    max_tokens: int,
    seed: int,
) -> CompletionRequest:
    """Turn a window into a provider request according to the continuation mechanism.

    See methodology.md §1.3: the mechanism is a protocol fact, and
    ``chat_instructed`` is a *different experimental arm* from the other two
    because the instruction is a permanent external force.
    """
    common: dict[str, Any] = {
        "model_id": generator.model_id,
        "max_tokens": max_tokens,
        "temperature": sampling.temperature,
        "top_p": sampling.top_p,
        "top_k": sampling.top_k,
        "repetition_penalty": sampling.repetition_penalty,
        "seed": seed,
        "logprobs": sampling.logprobs,
        "top_logprobs": sampling.top_logprobs,
        "provider_slug": generator.provider_slug,
        "allow_fallbacks": generator.allow_fallbacks,
        "service_tier": generator.service_tier,
        "country": generator.country,
    }

    if generator.continuation == "raw_completion":
        return CompletionRequest(prompt=prompt, **common)

    messages: list[dict[str, str]] = []
    if generator.system_prompt:
        messages.append({"role": "system", "content": generator.system_prompt})

    if generator.continuation == "assistant_prefill":
        if generator.prefill_user_stub:
            messages.append({"role": "user", "content": generator.prefill_user_stub})
        messages.append({"role": "assistant", "content": prompt})
    else:  # chat_instructed
        instruction = generator.continuation_instruction or ""
        messages.append({"role": "user", "content": f"{instruction}\n\n{prompt}"})

    return CompletionRequest(messages=tuple(messages), **common)


@dataclass
class TrajectoryResult:
    trajectory_id: str
    status: str
    generated_tokens: int
    n_steps: int
    n_chunks: int
    stop_events: int
    empty_completions: int
    roundtrip_failures: int
    horizon_tokens: int
    seed_tokens: int
    cost_usd: float
    prompt_tokens_total: int
    completion_tokens_total: int
    served_providers: dict[str, int] = field(default_factory=dict)
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "trajectory_id": self.trajectory_id,
            "status": self.status,
            "generated_tokens": self.generated_tokens,
            "n_steps": self.n_steps,
            "n_chunks": self.n_chunks,
            "stop_events": self.stop_events,
            "stop_event_rate": round(self.stop_events / max(self.n_steps, 1), 4),
            "empty_completions": self.empty_completions,
            "roundtrip_failures": self.roundtrip_failures,
            "horizon_tokens": self.horizon_tokens,
            "seed_tokens": self.seed_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "prompt_tokens_total": self.prompt_tokens_total,
            "completion_tokens_total": self.completion_tokens_total,
            "served_providers": self.served_providers,
            "error": self.error,
        }


class TrajectoryRunner:
    """Advances one trajectory, checkpointing after every step."""

    def __init__(
        self,
        *,
        generator: GeneratorConfig,
        window_config: WindowConfig,
        sampling: SamplingConfig,
        seed_spec: SeedSpec,
        stochastic_seed: int,
        tokenizer: Tokenizer,
        client: InferenceClient,
        paths: RunPaths,
        events: EventLogger,
        ledger: Ledger,
        price_table: dict[str, dict[str, float]] | None = None,
        log_chunk_text: bool = False,
    ) -> None:
        self.generator = generator
        self.window_config = window_config
        self.sampling = sampling
        self.seed_spec = seed_spec
        self.stochastic_seed = stochastic_seed
        self.tokenizer = tokenizer
        self.client = client
        self.paths = paths
        self.events = events
        self.ledger = ledger
        self.price_table = price_table
        self.log_chunk_text = log_chunk_text

        self.id = trajectory_id(
            generator=generator.slug,
            W=window_config.W,
            temperature=sampling.temperature,
            semantic_seed=seed_spec.id,
            stochastic_seed=stochastic_seed,
        )
        self._steps_path = paths.trajectory_steps(self.id)
        self._requests_path = paths.trajectory_requests(self.id)
        self._served: dict[str, int] = {}
        self._cost = 0.0
        self._prompt_tokens_total = 0
        self._completion_tokens_total = 0

    # -- resume -------------------------------------------------------------

    def _replay(self, accumulator: TrajectoryAccumulator) -> int:
        """Rebuild state from the checkpoint file. Returns the number of steps replayed."""
        if not self._steps_path.is_file():
            return 0
        replayed = 0
        with self._steps_path.open("rb") as handle:
            for raw in handle:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    record = orjson.loads(raw)
                except orjson.JSONDecodeError:
                    # A truncated final line from a killed process: stop here and
                    # continue generating from this point rather than guessing.
                    break
                text = record.get("text") or ""
                if not text:
                    continue
                accumulator.ingest(text, finish_reason=record.get("finish_reason"))
                self._cost += float(record.get("cost_usd") or 0.0)
                self._prompt_tokens_total += int(record.get("prompt_tokens") or 0)
                self._completion_tokens_total += int(record.get("completion_tokens") or 0)
                if provider := record.get("served_provider"):
                    self._served[provider] = self._served.get(provider, 0) + 1
                replayed += 1
        if replayed:
            self.events.event(
                "generation.trajectory.resumed",
                trajectory_id=self.id,
                steps_replayed=replayed,
                generated_tokens=accumulator.window.generated_tokens,
                mirror=f"resuming {self.id} at step {replayed} "
                f"({accumulator.window.generated_tokens} tokens)",
            )
        return replayed

    # -- run ----------------------------------------------------------------

    async def run(self) -> TrajectoryResult:
        window = SlidingWindow(
            self.tokenizer, W=self.window_config.W, seed_text=self.seed_spec.text
        )
        chunker = TokenChunker(self.tokenizer, chunk_size=self.window_config.chunk_size)
        accumulator = TrajectoryAccumulator(window=window, chunker=chunker)

        self._steps_path.parent.mkdir(parents=True, exist_ok=True)
        self._requests_path.parent.mkdir(parents=True, exist_ok=True)
        self._replay(accumulator)

        target = self.window_config.target_tokens
        consecutive_empty = 0
        error: str | None = None
        status = "COMPLETED"

        self.events.event(
            "generation.trajectory.started",
            trajectory_id=self.id,
            generator=self.generator.slug,
            model_id=self.generator.model_id,
            continuation=self.generator.continuation,
            forcing=self.generator.forcing,
            W=self.window_config.W,
            block_size=self.window_config.block_size,
            target_tokens=target,
            chunk_size=self.window_config.chunk_size,
            temperature=self.sampling.temperature,
            semantic_seed=self.seed_spec.id,
            stochastic_seed=self.stochastic_seed,
            seed_tokens=window.seed_tokens,
            seed_truncated=window.seed_truncated,
            horizon_tokens=window.horizon_tokens,
            tokenizer=self.tokenizer.fingerprint,
            mirror=f"start {self.id}: W={self.window_config.W} T={target} "
            f"({target / self.window_config.W:.1f} turnovers)",
        )

        try:
            while window.generated_tokens < target:
                remaining = target - window.generated_tokens
                max_tokens = min(self.window_config.block_size, remaining)
                prompt = window.prompt_text
                seed = step_seed(self.stochastic_seed, window.step)

                request = build_request(
                    self.generator,
                    self.sampling,
                    prompt=prompt,
                    max_tokens=max_tokens,
                    seed=seed,
                )
                reserve = estimate_request_usd(
                    self.generator,
                    prompt_tokens=window.prompt_tokens,
                    max_tokens=max_tokens,
                    price_table=self.price_table,
                )
                self.ledger.reserve(reserve, what=f"{self.id} step {window.step}")

                response = await self.client.complete(request)

                self.ledger.record(
                    response.usage,
                    kind="completion",
                    trajectory_id=self.id,
                    model_id=self.generator.model_id,
                    step=window.step,
                    served_provider=response.served_provider,
                )
                self._cost += response.usage.cost_usd
                self._prompt_tokens_total += response.usage.prompt_tokens
                self._completion_tokens_total += response.usage.completion_tokens
                if response.served_provider:
                    self._served[response.served_provider] = (
                        self._served.get(response.served_provider, 0) + 1
                    )

                self._write_request_record(window.step, request, response, prompt_preview=prompt)

                if not response.text.strip():
                    consecutive_empty += 1
                    accumulator.empty_completions += 1
                    self.events.event(
                        "generation.step.empty",
                        level="WARNING",
                        trajectory_id=self.id,
                        step=window.step,
                        finish_reason=response.finish_reason,
                        consecutive_empty=consecutive_empty,
                    )
                    if consecutive_empty >= MAX_CONSECUTIVE_EMPTY:
                        raise TrajectoryFailure(
                            self.id,
                            f"{consecutive_empty} consecutive empty completions; the model is "
                            "not free-running under this continuation mechanism",
                        )
                    continue
                consecutive_empty = 0

                before_chunks = len(accumulator.chunks)
                state = accumulator.ingest(response.text, finish_reason=response.finish_reason)
                new_chunks = accumulator.chunks[before_chunks:]
                self._checkpoint(state.step, response, text=response.text)
                self._log_step(state, response, new_chunks)

            status = "COMPLETED"
        except TrajectoryFailure as exc:
            status, error = "FAILED", str(exc)
            self.events.event(
                "generation.trajectory.failed",
                level="ERROR",
                trajectory_id=self.id,
                error=error,
                generated_tokens=window.generated_tokens,
            )
        except (ProviderError, WindowProtocolError) as exc:
            status, error = "FAILED", f"{type(exc).__name__}: {exc}"
            self.events.event(
                "generation.trajectory.failed",
                level="ERROR",
                trajectory_id=self.id,
                error=error,
                generated_tokens=window.generated_tokens,
            )

        self._write_text()

        result = TrajectoryResult(
            trajectory_id=self.id,
            status=status,
            generated_tokens=window.generated_tokens,
            n_steps=window.step,
            n_chunks=len(accumulator.chunks),
            stop_events=accumulator.stop_events,
            empty_completions=accumulator.empty_completions,
            roundtrip_failures=accumulator.roundtrip_failures,
            horizon_tokens=window.horizon_tokens,
            seed_tokens=window.seed_tokens,
            cost_usd=self._cost,
            prompt_tokens_total=self._prompt_tokens_total,
            completion_tokens_total=self._completion_tokens_total,
            served_providers=dict(self._served),
            error=error,
        )
        self.events.event(
            "generation.trajectory.finished",
            **result.as_dict(),
            mirror=f"{status.lower()} {self.id}: {window.step} steps, "
            f"{window.generated_tokens} tokens, {len(accumulator.chunks)} chunks, "
            f"${self._cost:.4f}",
        )
        self.chunks = accumulator.chunks
        return result

    # -- persistence --------------------------------------------------------

    def _checkpoint(self, step: int, response: Any, *, text: str) -> None:
        record = {
            "step": step,
            "text": text,
            "finish_reason": response.finish_reason,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "cost_usd": response.usage.cost_usd,
            "served_provider": response.served_provider,
            "from_cache": response.from_cache,
        }
        with self._steps_path.open("ab") as handle:
            handle.write(orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE))

    def _write_request_record(
        self, step: int, request: CompletionRequest, response: Any, *, prompt_preview: str
    ) -> None:
        """Raw request/response, for audit and for reproducing a single step."""
        record = {
            "step": step,
            "request": {
                "model_id": request.model_id,
                "is_chat": request.is_chat,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "seed": request.seed,
                "provider_slug": request.provider_slug,
                "allow_fallbacks": request.allow_fallbacks,
                "service_tier": request.service_tier,
                # The full prompt is recoverable by replaying earlier steps, so we
                # store its hash plus both ends: enough to verify the window
                # without duplicating the whole trajectory on every line.
                "prompt_sha256": sha256_text(prompt_preview),
                "prompt_chars": len(prompt_preview),
                "prompt_head": prompt_preview[:400],
                "prompt_tail": prompt_preview[-400:],
            },
            "response": {
                "finish_reason": response.finish_reason,
                "served_provider": response.served_provider,
                "model_returned": response.model_returned,
                "latency_s": round(response.latency_s, 4),
                "attempts": response.attempts,
                "from_cache": response.from_cache,
                "usage": response.usage.as_dict(),
                "text": response.text,
                "logprobs": response.logprobs,
            },
        }
        with self._requests_path.open("ab") as handle:
            handle.write(orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE))

    def _write_text(self) -> None:
        """Full generated text, for reading and for re-chunking under other sizes.

        Reconstructed from the checkpoint file rather than held in memory, so a
        resumed run produces the same file as an uninterrupted one.
        """
        path = self.paths.trajectory_text(self.id)
        path.parent.mkdir(parents=True, exist_ok=True)
        pieces: list[str] = []
        if self._steps_path.is_file():
            with self._steps_path.open("rb") as handle:
                for raw in handle:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        pieces.append(orjson.loads(raw).get("text") or "")
                    except orjson.JSONDecodeError:
                        break
        path.write_text("".join(pieces), encoding="utf-8")

    def _log_step(self, state: Any, response: Any, new_chunks: list[ChunkRecord]) -> None:
        payload: dict[str, Any] = {
            "trajectory_id": self.id,
            "step": state.step,
            "generated_tokens": state.generated_tokens,
            "turnovers": round(state.turnovers, 4),
            "prompt_tokens_local": state.prompt_tokens,
            "prompt_tokens_api": response.usage.prompt_tokens,
            "completion_tokens_api": response.usage.completion_tokens,
            "finish_reason": response.finish_reason,
            "seed_in_window": state.seed_in_window,
            "seed_tokens_in_window": state.seed_tokens_in_window,
            "past_horizon": state.past_horizon,
            "tokenizer_roundtrip_ok": state.roundtrip_ok,
            "latency_s": round(response.latency_s, 3),
            "attempts": response.attempts,
            "from_cache": response.from_cache,
            "cost_usd": round(response.usage.cost_usd, 8),
            "cumulative_cost_usd": round(self._cost, 6),
            "served_provider": response.served_provider,
            "chunks_emitted": len(new_chunks),
        }
        if self.log_chunk_text and new_chunks:
            payload["chunk_texts"] = [c.text for c in new_chunks]
        self.events.event("generation.step.completed", **payload)


# ---------------------------------------------------------------------------
# Batch orchestration
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PlannedTrajectory:
    generator: GeneratorConfig
    window: WindowConfig
    sampling: SamplingConfig
    seed_spec: SeedSpec
    stochastic_seed: int


def plan_trajectories(config: ExperimentConfig, seed_bank: Any) -> list[PlannedTrajectory]:
    """Expand the experiment matrix into a concrete, ordered list of trajectories."""
    planned: list[PlannedTrajectory] = []
    for generator in config.generators:
        for window in config.windows:
            for sampling in config.sampling:
                for semantic_seed in config.semantic_seeds:
                    for stochastic_seed in config.stochastic_seeds:
                        planned.append(
                            PlannedTrajectory(
                                generator=generator,
                                window=window,
                                sampling=sampling,
                                seed_spec=seed_bank.by_id(semantic_seed),
                                stochastic_seed=stochastic_seed,
                            )
                        )
    return planned


async def run_trajectories(
    planned: list[PlannedTrajectory],
    *,
    settings: Settings,
    paths: RunPaths,
    events: EventLogger,
    ledger: Ledger,
    client_for: Any,
    tokenizer_for: Any,
    price_table: dict[str, dict[str, float]] | None = None,
    max_concurrent: int | None = None,
) -> tuple[list[TrajectoryResult], list[TrajectoryRunner]]:
    """Advance every planned trajectory, bounded by a semaphore.

    Concurrency is across trajectories only; a single trajectory is inherently
    sequential. Failures are collected rather than raised so that one dead cell
    does not discard the rest of a multi-hour batch.

    Returns the results and the runners, the latter because they carry the chunk
    records that the caller needs to persist.
    """
    limit = max_concurrent or settings.afterlife_max_concurrent_trajectories
    semaphore = asyncio.Semaphore(max(1, limit))
    results: list[TrajectoryResult] = []
    runners: list[TrajectoryRunner] = []

    async def one(item: PlannedTrajectory) -> TrajectoryResult:
        async with semaphore:
            runner = TrajectoryRunner(
                generator=item.generator,
                window_config=item.window,
                sampling=item.sampling,
                seed_spec=item.seed_spec,
                stochastic_seed=item.stochastic_seed,
                tokenizer=tokenizer_for(item.generator),
                client=client_for(item.generator),
                paths=paths,
                events=events,
                ledger=ledger,
                price_table=price_table,
                log_chunk_text=settings.afterlife_log_chunk_text,
            )
            runners.append(runner)
            return await runner.run()

    gathered = await asyncio.gather(*(one(item) for item in planned), return_exceptions=True)
    for item, outcome in zip(planned, gathered, strict=True):
        if isinstance(outcome, BaseException):
            tid = trajectory_id(
                generator=item.generator.slug,
                W=item.window.W,
                temperature=item.sampling.temperature,
                semantic_seed=item.seed_spec.id,
                stochastic_seed=item.stochastic_seed,
            )
            events.event(
                "generation.trajectory.crashed",
                level="ERROR",
                trajectory_id=tid,
                error_type=type(outcome).__name__,
                error=str(outcome),
            )
            results.append(
                TrajectoryResult(
                    trajectory_id=tid,
                    status="CRASHED",
                    generated_tokens=0,
                    n_steps=0,
                    n_chunks=0,
                    stop_events=0,
                    empty_completions=0,
                    roundtrip_failures=0,
                    horizon_tokens=0,
                    seed_tokens=0,
                    cost_usd=0.0,
                    prompt_tokens_total=0,
                    completion_tokens_total=0,
                    error=f"{type(outcome).__name__}: {outcome}",
                )
            )
        else:
            results.append(outcome)
    return results, runners


def collect_chunks(runners: list[TrajectoryRunner]) -> list[dict[str, Any]]:
    """Flatten per-trajectory chunk records into rows for a parquet table."""
    rows: list[dict[str, Any]] = []
    for runner in runners:
        for chunk in getattr(runner, "chunks", []):
            rows.append(
                {
                    "trajectory_id": runner.id,
                    "generator": runner.generator.slug,
                    "W": runner.window_config.W,
                    "block_size": runner.window_config.block_size,
                    "chunk_size": runner.window_config.chunk_size,
                    "temperature": runner.sampling.temperature,
                    "semantic_seed": runner.seed_spec.id,
                    "semantic_domain": runner.seed_spec.domain,
                    "stochastic_seed": runner.stochastic_seed,
                    "chunk_index": chunk.index,
                    "token_start": chunk.token_start,
                    "token_end": chunk.token_end,
                    "n_tokens": chunk.n_tokens,
                    "past_horizon": chunk.token_start >= runner.window_config.W,
                    "turnover": chunk.token_end / runner.window_config.W,
                    "text": chunk.text,
                }
            )
    return rows


def embedding_slug(embedding: EmbeddingConfig) -> str:
    return embedding.slug
