"""Domain exceptions.

Never raise bare ``Exception``; a typed error is what lets a long generation run
distinguish "this trajectory is lost" from "stop the whole batch".
"""

from __future__ import annotations


class AfterlifeError(Exception):
    """Base class for every error raised by this package."""


class ConfigError(AfterlifeError):
    """Malformed, missing, or internally inconsistent configuration."""


class MissingCredentialsError(ConfigError):
    """A required API key is absent from the environment."""


class BudgetExceededError(AfterlifeError):
    """A request would push spend past a configured ceiling.

    Raised *before* the request is issued. Never caught and retried; the human
    decides whether to raise the ceiling.
    """


class ProviderError(AfterlifeError):
    """The inference provider returned an error or an unusable response."""

    def __init__(self, message: str, *, status_code: int | None = None, body: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class ProviderPinningError(ProviderError):
    """The provider that served a request differs from the pinned one.

    This invalidates the trajectory: the generator changed mid-experiment.
    See ADR-0003.
    """


class CacheMissError(AfterlifeError):
    """``replay`` execution mode required a cached response that is absent."""


class TokenizerError(AfterlifeError):
    """A generator tokenizer could not be loaded or failed its round-trip check."""


class WindowProtocolError(AfterlifeError):
    """The sliding-window invariants were violated.

    Correctness-critical: a window that is not where the manifest claims makes
    ``W`` meaningless for that trajectory.
    """


class TrajectoryFailure(AfterlifeError):
    """A single trajectory failed; the batch continues with the failure recorded."""

    def __init__(self, trajectory_id: str, message: str):
        super().__init__(f"trajectory {trajectory_id}: {message}")
        self.trajectory_id = trajectory_id


class AnalysisError(AfterlifeError):
    """An analysis pass received data it cannot legitimately process."""
