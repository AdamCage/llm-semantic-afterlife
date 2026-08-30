"""Structured logging.

Two sinks, one call site:

* ``events.jsonl`` — one JSON object per line, machine-readable, append-only.
  This is the audit trail a reviewer or a post-mortem reads.
* the console (and ``logs/run.log``) — human-readable, for watching a run.

The rule from ``.cursor/rules/10-reproducibility.mdc`` is that a long run must be
reconstructible from its event log alone. That is only true if events are emitted
at every step with typed payloads, so :meth:`EventLogger.event` takes a dotted
event name plus arbitrary keyword fields rather than a formatted string.
"""

from __future__ import annotations

import logging
import sys
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import orjson
from rich.console import Console
from rich.logging import RichHandler

_console: Console | None = None
_configured = False
_lock = threading.Lock()

# Keys whose values must never reach a log sink.
_REDACTED_KEYS = frozenset(
    {"api_key", "authorization", "token", "hf_token", "secret", "password", "bearer"}
)
_REDACTED = "<redacted>"


def get_console() -> Console:
    global _console
    if _console is None:
        # soft_wrap keeps long generated text from being re-flowed into noise.
        _console = Console(stderr=True, soft_wrap=True)
    return _console


def configure_logging(level: str = "INFO", *, log_file: Path | None = None) -> None:
    """Install the console handler (and optionally a file mirror). Idempotent."""
    global _configured
    with _lock:
        root = logging.getLogger("semantic_afterlife")
        root.setLevel(level.upper())
        if not _configured:
            handler = RichHandler(
                console=get_console(),
                rich_tracebacks=True,
                show_path=False,
                markup=False,
                log_time_format="%H:%M:%S",
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            root.addHandler(handler)
            root.propagate = False
            _configured = True
        if log_file is not None:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            existing = {
                Path(h.baseFilename).resolve()
                for h in root.handlers
                if isinstance(h, logging.FileHandler)
            }
            if log_file.resolve() not in existing:
                file_handler = logging.FileHandler(log_file, encoding="utf-8")
                file_handler.setFormatter(
                    logging.Formatter("%(asctime)s %(levelname)-8s %(name)s %(message)s")
                )
                root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Logger for human-readable messages. Structured events go via :class:`EventLogger`."""
    return logging.getLogger(f"semantic_afterlife.{name}")


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: (_REDACTED if key.lower() in _REDACTED_KEYS else _redact(val))
            for key, val in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    return value


class EventLogger:
    """Append-only JSONL event sink for one run.

    Thread-safe: trajectories run concurrently and all write to the same file.
    """

    def __init__(self, path: Path, run_id: str, *, mirror_level: int = logging.INFO) -> None:
        self.path = path
        self.run_id = run_id
        self._mirror_level = mirror_level
        self._lock = threading.Lock()
        self._logger = get_logger("events")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("ab", buffering=0)

    def event(
        self, name: str, *, level: str = "INFO", mirror: str | None = None, **fields: Any
    ) -> None:
        """Emit one structured event.

        ``name`` is a dotted identifier (``generation.step.completed``) so that
        events can be filtered mechanically. ``mirror`` is the optional
        human-readable line for the console; without it, events stay silent on
        the console and live only in the JSONL.
        """
        record = {
            "ts": datetime.now(UTC).isoformat(timespec="milliseconds"),
            "level": level,
            "event": name,
            "run_id": self.run_id,
            **_redact(fields),
        }
        line = orjson.dumps(record, option=orjson.OPT_APPEND_NEWLINE)
        with self._lock:
            self._handle.write(line)
        if mirror:
            self._logger.log(logging.getLevelName(level.upper()), mirror)

    @contextmanager
    def timed(self, name: str, **fields: Any) -> Iterator[dict[str, Any]]:
        """Emit ``<name>.started`` / ``.completed`` / ``.failed`` with a duration.

        The yielded dict can be mutated to attach outcome fields to the
        completion event, which keeps timing and outcome in one record.
        """
        extra: dict[str, Any] = {}
        self.event(f"{name}.started", **fields)
        start = perf_counter()
        try:
            yield extra
        except Exception as exc:
            self.event(
                f"{name}.failed",
                level="ERROR",
                duration_s=round(perf_counter() - start, 4),
                error_type=type(exc).__name__,
                error=str(exc),
                **fields,
                **extra,
            )
            raise
        else:
            self.event(
                f"{name}.completed",
                duration_s=round(perf_counter() - start, 4),
                **fields,
                **extra,
            )

    def close(self) -> None:
        with self._lock:
            if not self._handle.closed:
                self._handle.close()

    def __enter__(self) -> EventLogger:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def read_events(path: Path) -> list[dict[str, Any]]:
    """Load an event log. Tolerates a truncated final line from a killed run."""
    events: list[dict[str, Any]] = []
    with path.open("rb") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            try:
                events.append(orjson.loads(raw))
            except orjson.JSONDecodeError:
                print(f"warning: skipping malformed event line in {path}", file=sys.stderr)
    return events
