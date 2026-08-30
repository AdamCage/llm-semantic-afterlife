"""Cost forecasting.

The whole budget structure of the project follows from one relation
(ADR-0004): under the re-prompt protocol the entire window is re-sent every
``S`` tokens, so

    input_tokens ≈ T · W / S        output_tokens ≈ T

which means input dominates by a factor of ``W/S``. Estimates here are used both
to warn a human before a launch and to enforce the ledger's ceilings, so they
must be conservative rather than optimistic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import ExperimentConfig, GeneratorConfig, WindowConfig


@dataclass(frozen=True, slots=True)
class CellEstimate:
    generator: str
    W: int
    block_size: int
    target_tokens: int
    n_trajectories: int
    input_tokens: int
    output_tokens: int
    input_usd: float
    output_usd: float

    @property
    def total_usd(self) -> float:
        return self.input_usd + self.output_usd

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def turnovers(self) -> float:
        return self.target_tokens / self.W

    def as_dict(self) -> dict[str, Any]:
        return {
            "generator": self.generator,
            "W": self.W,
            "block_size": self.block_size,
            "target_tokens": self.target_tokens,
            "turnovers": round(self.turnovers, 2),
            "n_trajectories": self.n_trajectories,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "input_amplification": round(self.input_tokens / max(self.output_tokens, 1), 2),
            "input_usd": round(self.input_usd, 4),
            "output_usd": round(self.output_usd, 4),
            "total_usd": round(self.total_usd, 4),
        }


def trajectory_tokens(window: WindowConfig, *, block_fill: float = 1.0) -> tuple[int, int]:
    """``(input_tokens, output_tokens)`` for one trajectory.

    The input side ramps while the window is still filling, so it is summed step
    by step rather than approximated by ``T·W/S`` -- at low turnover counts the
    difference is material.

    ``block_fill`` is the measured mean ratio of returned tokens to ``max_tokens``.
    A model that stops early needs ``1/block_fill`` times as many steps to reach
    ``T``, and each extra step re-sends the entire window, so input scales
    accordingly. Output does not: it is bounded by ``T`` either way.
    """
    fill = min(max(block_fill, 1e-3), 1.0)
    effective_block = max(1, int(window.block_size * fill))
    n_steps = -(-window.target_tokens // effective_block)
    total_input = 0
    produced = 0
    for _ in range(n_steps):
        total_input += min(produced, window.W)
        produced += effective_block
    return total_input, window.target_tokens


def prices(
    generator: GeneratorConfig, price_table: dict[str, dict[str, float]] | None
) -> tuple[float, float]:
    """Per-token USD ``(input, output)``.

    Config-declared prices win over a fetched table: they are what the stage plan
    was approved against, and a silent provider price change should show up as a
    discrepancy in the report rather than as a quietly different bill.
    """
    if generator.price_usd_per_m_input is not None or generator.price_usd_per_m_output is not None:
        return (
            (generator.price_usd_per_m_input or 0.0) / 1e6,
            (generator.price_usd_per_m_output or 0.0) / 1e6,
        )
    entry = (price_table or {}).get(generator.model_id, {})
    return entry.get("input_usd_per_token", 0.0), entry.get("output_usd_per_token", 0.0)


def estimate_experiment(
    config: ExperimentConfig,
    *,
    price_table: dict[str, dict[str, float]] | None = None,
) -> list[CellEstimate]:
    """Per-(generator, window) forecast for a whole experiment matrix."""
    counts: dict[tuple[str, int, int], int] = {}
    for cell in config.cells:
        key = (cell["generator"], cell["W"], cell["block_size"])
        counts[key] = counts.get(key, 0) + 1

    out: list[CellEstimate] = []
    for (generator_slug, W, block_size), n in sorted(counts.items()):
        generator = config.generator(generator_slug)
        window = config.window(W, block_size)
        input_tokens, output_tokens = trajectory_tokens(
            window, block_fill=generator.expected_block_fill
        )
        input_price, output_price = prices(generator, price_table)
        out.append(
            CellEstimate(
                generator=generator_slug,
                W=W,
                block_size=block_size,
                target_tokens=window.target_tokens,
                n_trajectories=n,
                input_tokens=input_tokens * n,
                output_tokens=output_tokens * n,
                input_usd=input_tokens * n * input_price,
                output_usd=output_tokens * n * output_price,
            )
        )
    return out


def estimate_request_usd(
    generator: GeneratorConfig,
    *,
    prompt_tokens: int,
    max_tokens: int,
    price_table: dict[str, dict[str, float]] | None = None,
) -> float:
    """Upper bound for one request, used by :meth:`Ledger.reserve`.

    Assumes the model returns the full ``max_tokens``, which is the worst case.
    """
    input_price, output_price = prices(generator, price_table)
    return prompt_tokens * input_price + max_tokens * output_price


def estimate_embedding_usd(price_usd_per_m_input: float | None, *, n_tokens: int) -> float:
    return (price_usd_per_m_input or 0.0) / 1e6 * n_tokens


def summarise(estimates: list[CellEstimate]) -> dict[str, Any]:
    return {
        "n_trajectories": sum(e.n_trajectories for e in estimates),
        "input_tokens": sum(e.input_tokens for e in estimates),
        "output_tokens": sum(e.output_tokens for e in estimates),
        "total_usd": round(sum(e.total_usd for e in estimates), 4),
        "input_share": round(
            sum(e.input_usd for e in estimates) / max(sum(e.total_usd for e in estimates), 1e-12), 3
        ),
    }
