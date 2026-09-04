"""Append-only spend ledger and budget enforcement.

Every request that could cost money passes through :meth:`Ledger.reserve`
*before* it is issued and :meth:`Ledger.record` after. Ceilings are checked on
reservation, so an overrun is prevented rather than discovered.

The ledger is a JSONL file rather than a database because it must survive being
read by a human mid-run, being appended to by several concurrent trajectories,
and being committed as evidence alongside a stage report.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import orjson

from .errors import BudgetExceededError


@dataclass(frozen=True, slots=True)
class Usage:
    """Token accounting and cost for one request."""

    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    cost_rub: float | None = None
    cached_tokens: int | None = None
    from_cache: bool = False

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def as_dict(self) -> dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": round(self.cost_usd, 8),
            "cost_rub": None if self.cost_rub is None else round(self.cost_rub, 6),
            "cached_tokens": self.cached_tokens,
            "from_cache": self.from_cache,
        }

    @staticmethod
    def zero() -> Usage:
        return Usage(prompt_tokens=0, completion_tokens=0, cost_usd=0.0, from_cache=True)


class Ledger:
    """Spend tracker with hard ceilings.

    ``per_run_ceiling`` guards a single invocation; ``total_ceiling`` guards the
    project. Both are read from settings and never raised in code.
    """

    def __init__(
        self,
        path: Path,
        *,
        run_id: str,
        per_run_ceiling_usd: float,
        total_ceiling_usd: float,
        stage_ceiling_usd: float | None = None,
    ) -> None:
        self.path = path
        self.run_id = run_id
        self.per_run_ceiling_usd = per_run_ceiling_usd
        self.total_ceiling_usd = total_ceiling_usd
        self.stage_ceiling_usd = stage_ceiling_usd
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        others, this_run = self._sum_ledger()
        # Charges already written for this run_id count toward the per-run
        # ceiling. A resume that started `_run_spend` at 0 would allow a
        # second full ceiling on top of a hung invocation.
        self._historical_spend = others
        self._run_spend = this_run

    def _sum_ledger(self) -> tuple[float, float]:
        if not self.path.is_file():
            return 0.0, 0.0
        others = 0.0
        this_run = 0.0
        with self.path.open("rb") as handle:
            for raw in handle:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    entry = orjson.loads(raw)
                    cost = float(entry.get("cost_usd", 0.0))
                except (orjson.JSONDecodeError, TypeError, ValueError):
                    continue
                if entry.get("run_id") == self.run_id:
                    this_run += cost
                else:
                    others += cost
        return others, this_run

    @property
    def run_spend_usd(self) -> float:
        return self._run_spend

    @property
    def project_spend_usd(self) -> float:
        return self._historical_spend + self._run_spend

    @property
    def remaining_project_usd(self) -> float:
        return self.total_ceiling_usd - self.project_spend_usd

    def reserve(self, estimated_usd: float, *, what: str) -> None:
        """Check ceilings before a request is issued.

        Raises :class:`BudgetExceededError`, which is never retried: the human
        decides whether to raise a ceiling.
        """
        with self._lock:
            prospective_run = self._run_spend + estimated_usd
            prospective_total = self.project_spend_usd + estimated_usd
        if prospective_run > self.per_run_ceiling_usd:
            raise BudgetExceededError(
                f"{what}: this run would reach ${prospective_run:.4f}, over the per-run ceiling "
                f"of ${self.per_run_ceiling_usd:.2f}. Raise AFTERLIFE_BUDGET_USD_PER_RUN only "
                "after checking with the human."
            )
        if prospective_total > self.total_ceiling_usd:
            raise BudgetExceededError(
                f"{what}: project spend would reach ${prospective_total:.4f}, over the total "
                f"ceiling of ${self.total_ceiling_usd:.2f}."
            )
        if self.stage_ceiling_usd is not None and prospective_run > self.stage_ceiling_usd:
            raise BudgetExceededError(
                f"{what}: this run would reach ${prospective_run:.4f}, over the stage budget of "
                f"${self.stage_ceiling_usd:.2f} declared in the stage plan."
            )

    def record(self, usage: Usage, *, kind: str, **fields: Any) -> None:
        """Append an actual charge. Cache hits are recorded with zero cost."""
        entry = {
            "ts": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "run_id": self.run_id,
            "kind": kind,
            **usage.as_dict(),
            **fields,
        }
        with self._lock:
            self._run_spend += usage.cost_usd
            with self.path.open("ab") as handle:
                handle.write(orjson.dumps(entry, option=orjson.OPT_APPEND_NEWLINE))

    def summary(self) -> dict[str, Any]:
        return {
            "run_spend_usd": round(self._run_spend, 6),
            "project_spend_usd": round(self.project_spend_usd, 6),
            "remaining_project_usd": round(self.remaining_project_usd, 6),
            "per_run_ceiling_usd": self.per_run_ceiling_usd,
            "total_ceiling_usd": self.total_ceiling_usd,
        }


def read_ledger(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    entries: list[dict[str, Any]] = []
    with path.open("rb") as handle:
        for raw in handle:
            raw = raw.strip()
            if raw:
                try:
                    entries.append(orjson.loads(raw))
                except orjson.JSONDecodeError:
                    continue
    return entries
