"""The sliding window and the analysis chunker.

This is the most correctness-critical module in the project: if the window is not
where the manifest claims, every result that mentions ``W`` is void. It is
therefore small, side-effect free, and exhaustively tested.

Design notes
------------
*Text is authoritative, not token ids.* The API consumes and produces text, so
the state we carry is text, and the window is defined as "the detokenisation of
the last ``W`` tokens of that text under the generator's tokenizer". This is
self-consistent — the prompt we send *is* the window — and it makes the whole
protocol expressible without ever assuming that re-tokenising the model's own
output reproduces the model's internal token sequence (it need not, at block
boundaries).

*Cost is ``O(W)`` per step, not ``O(T)``.* Only a bounded tail is ever
re-encoded, so a million-token trajectory does not degrade quadratically.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..errors import WindowProtocolError
from ..tokenization import Tokenizer


@dataclass(frozen=True, slots=True)
class WindowState:
    """Observable state after a step; every field is logged."""

    step: int
    generated_tokens: int
    prompt_tokens: int
    seed_tokens_in_window: int
    seed_in_window: bool
    past_horizon: bool
    roundtrip_ok: bool
    turnovers: float


@dataclass(frozen=True, slots=True)
class ChunkRecord:
    """One analysis unit: exactly ``chunk_size`` generator tokens."""

    index: int
    token_start: int
    token_end: int
    n_tokens: int
    text: str


class SlidingWindow:
    """Maintains ``X_{t+1} = Tail_W(X_t ⊕ Y_t)``.

    ``seed_text`` is the initial condition. If it exceeds ``W`` it is truncated
    to its own tail, and the truncation is reported so the manifest records that
    the trajectory started with a partially visible seed.
    """

    def __init__(self, tokenizer: Tokenizer, *, W: int, seed_text: str) -> None:
        if W <= 0:
            raise WindowProtocolError(f"W must be positive, got {W}")
        self.tokenizer = tokenizer
        self.W = W

        seed_ids = tokenizer.encode(seed_text)
        self.seed_truncated = len(seed_ids) > W
        if self.seed_truncated:
            seed_ids = seed_ids[-W:]
            seed_text = tokenizer.decode(seed_ids)
        self.seed_text = seed_text
        self.seed_tokens = len(seed_ids)

        self._buffer = seed_text
        self._buffer_tokens = self.seed_tokens
        self.generated_tokens = 0
        self.step = 0
        self._last_roundtrip_ok = True

    # -- derived quantities --------------------------------------------------

    @property
    def horizon_tokens(self) -> int:
        """``t_h = W − L_0``: generated tokens after which no seed token remains."""
        return max(0, self.W - self.seed_tokens)

    @property
    def seed_tokens_in_window(self) -> int:
        return max(0, min(self.seed_tokens, self.W - self.generated_tokens))

    @property
    def past_horizon(self) -> bool:
        return self.seed_tokens_in_window == 0

    @property
    def prompt_text(self) -> str:
        """The current window, as the exact text that will be sent."""
        return self._buffer

    @property
    def prompt_tokens(self) -> int:
        return self._buffer_tokens

    def turnovers(self) -> float:
        return self.generated_tokens / self.W

    # -- advance ------------------------------------------------------------

    def append(self, new_text: str) -> WindowState:
        """Append a generated block and slide the window.

        Raises :class:`WindowProtocolError` if the window ends up longer than
        ``W``, which would mean the model was shown more memory than the
        experiment claims.
        """
        if not new_text:
            raise WindowProtocolError("cannot append an empty block; the caller must handle this")

        combined = self._buffer + new_text
        ids = self.tokenizer.encode(combined)
        new_tokens = len(ids) - self._buffer_tokens
        if new_tokens <= 0:
            # Re-tokenisation merged the whole block into existing tokens: the
            # trajectory would stall silently, so refuse instead.
            raise WindowProtocolError(
                f"appending {len(new_text)} characters produced {new_tokens} new tokens; "
                "re-tokenisation collapsed the block"
            )

        if len(ids) > self.W:
            kept = ids[-self.W :]
            self._buffer = self.tokenizer.decode(kept)
            self._buffer_tokens = len(kept)
            # decode/encode must be stable, otherwise the boundary drifts.
            self._last_roundtrip_ok = (
                len(self.tokenizer.encode(self._buffer)) == self._buffer_tokens
            )
        else:
            self._buffer = combined
            self._buffer_tokens = len(ids)
            self._last_roundtrip_ok = True

        if self._buffer_tokens > self.W:
            raise WindowProtocolError(
                f"window holds {self._buffer_tokens} tokens, above W={self.W}"
            )

        self.generated_tokens += new_tokens
        self.step += 1
        return WindowState(
            step=self.step,
            generated_tokens=self.generated_tokens,
            prompt_tokens=self._buffer_tokens,
            seed_tokens_in_window=self.seed_tokens_in_window,
            seed_in_window=self.seed_tokens_in_window > 0,
            past_horizon=self.past_horizon,
            roundtrip_ok=self._last_roundtrip_ok,
            turnovers=self.turnovers(),
        )


class TokenChunker:
    """Cuts the generated stream into non-overlapping ``chunk_size`` chunks.

    Overlap is not offered as an option. It inflates autocorrelation and thereby
    manufactures apparent metastability (risks.md R3, methodology.md §1.6).
    """

    def __init__(self, tokenizer: Tokenizer, *, chunk_size: int) -> None:
        if chunk_size <= 0:
            raise WindowProtocolError(f"chunk_size must be positive, got {chunk_size}")
        self.tokenizer = tokenizer
        self.chunk_size = chunk_size
        self._pending = ""
        self._pending_tokens = 0
        self._emitted_tokens = 0
        self._index = 0

    @property
    def n_emitted(self) -> int:
        return self._index

    @property
    def pending_tokens(self) -> int:
        return self._pending_tokens

    def feed(self, text: str) -> list[ChunkRecord]:
        """Add generated text; return every complete chunk it made available."""
        if not text:
            return []
        self._pending += text
        ids = self.tokenizer.encode(self._pending)
        out: list[ChunkRecord] = []
        cursor = 0
        while len(ids) - cursor >= self.chunk_size:
            piece = ids[cursor : cursor + self.chunk_size]
            chunk_text = self.tokenizer.decode(piece)
            out.append(
                ChunkRecord(
                    index=self._index,
                    token_start=self._emitted_tokens,
                    token_end=self._emitted_tokens + self.chunk_size,
                    n_tokens=self.chunk_size,
                    text=chunk_text,
                )
            )
            self._index += 1
            self._emitted_tokens += self.chunk_size
            cursor += self.chunk_size
        if cursor:
            self._pending = self.tokenizer.decode(ids[cursor:])
        self._pending_tokens = len(ids) - cursor
        return out

    def flush_partial(self) -> ChunkRecord | None:
        """Return the trailing partial chunk, if any.

        Never used in analysis — a short chunk is not comparable to a full one —
        but recorded so that token accounting reconciles exactly.
        """
        if self._pending_tokens == 0:
            return None
        return ChunkRecord(
            index=self._index,
            token_start=self._emitted_tokens,
            token_end=self._emitted_tokens + self._pending_tokens,
            n_tokens=self._pending_tokens,
            text=self._pending,
        )


@dataclass
class TrajectoryAccumulator:
    """Bookkeeping shared by the runner and by resume logic."""

    window: SlidingWindow
    chunker: TokenChunker
    chunks: list[ChunkRecord] = field(default_factory=list)
    stop_events: int = 0
    empty_completions: int = 0
    roundtrip_failures: int = 0

    def ingest(self, text: str, *, finish_reason: str | None) -> WindowState:
        state = self.window.append(text)
        self.chunks.extend(self.chunker.feed(text))
        if finish_reason not in (None, "length"):
            self.stop_events += 1
        if not state.roundtrip_ok:
            self.roundtrip_failures += 1
        return state
