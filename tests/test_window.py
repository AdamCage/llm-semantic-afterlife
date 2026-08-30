"""Sliding-window and chunker invariants.

This is the most correctness-critical code in the project: if the window is not
where the manifest claims, every result that mentions ``W`` is void. The tests
below are therefore about invariants rather than examples.
"""

from __future__ import annotations

import itertools

import pytest

from semantic_afterlife.errors import WindowProtocolError
from semantic_afterlife.generation.window import SlidingWindow, TokenChunker
from semantic_afterlife.tokenization import WhitespaceTokenizer


def words(n: int, *, offset: int = 0) -> str:
    return " " + " ".join(f"w{offset + i}" for i in range(n))


class TestSlidingWindow:
    def test_window_never_exceeds_W(self, whitespace_tokenizer: WhitespaceTokenizer) -> None:
        window = SlidingWindow(whitespace_tokenizer, W=64, seed_text="seed text here")
        for step in range(40):
            window.append(words(8, offset=step * 8))
            assert window.prompt_tokens <= 64

    def test_prompt_is_exactly_the_tail(self, whitespace_tokenizer: WhitespaceTokenizer) -> None:
        """The prompt sent must *be* the detokenised last W tokens, not an approximation."""
        window = SlidingWindow(whitespace_tokenizer, W=32, seed_text="a b c d")
        for step in range(20):
            window.append(words(6, offset=step * 6))
        ids = whitespace_tokenizer.encode(window.prompt_text)
        assert len(ids) == window.prompt_tokens
        assert whitespace_tokenizer.decode(ids) == window.prompt_text

    def test_generated_tokens_accumulate(self, whitespace_tokenizer: WhitespaceTokenizer) -> None:
        window = SlidingWindow(whitespace_tokenizer, W=100, seed_text="s")
        before = 0
        for step in range(10):
            state = window.append(words(5, offset=step * 5))
            assert state.generated_tokens > before
            before = state.generated_tokens
        assert window.generated_tokens == before

    def test_horizon_matches_W_minus_seed(self, whitespace_tokenizer: WhitespaceTokenizer) -> None:
        seed = "alpha beta gamma delta"
        window = SlidingWindow(whitespace_tokenizer, W=50, seed_text=seed)
        assert window.horizon_tokens == 50 - window.seed_tokens

    def test_seed_leaves_the_window_exactly_at_the_horizon(
        self, whitespace_tokenizer: WhitespaceTokenizer
    ) -> None:
        window = SlidingWindow(whitespace_tokenizer, W=40, seed_text="one two three")
        horizon = window.horizon_tokens
        assert window.seed_tokens_in_window > 0
        while window.generated_tokens < horizon:
            window.append(words(4, offset=window.generated_tokens))
        assert window.past_horizon
        assert window.seed_tokens_in_window == 0

    def test_oversized_seed_is_truncated_and_flagged(
        self, whitespace_tokenizer: WhitespaceTokenizer
    ) -> None:
        window = SlidingWindow(whitespace_tokenizer, W=10, seed_text=words(100))
        assert window.seed_truncated
        assert window.seed_tokens == 10
        assert window.horizon_tokens == 0

    def test_empty_block_is_rejected(self, whitespace_tokenizer: WhitespaceTokenizer) -> None:
        window = SlidingWindow(whitespace_tokenizer, W=16, seed_text="x")
        with pytest.raises(WindowProtocolError):
            window.append("")

    def test_nonpositive_W_is_rejected(self, whitespace_tokenizer: WhitespaceTokenizer) -> None:
        with pytest.raises(WindowProtocolError):
            SlidingWindow(whitespace_tokenizer, W=0, seed_text="x")

    def test_turnovers_track_generated_tokens(
        self, whitespace_tokenizer: WhitespaceTokenizer
    ) -> None:
        window = SlidingWindow(whitespace_tokenizer, W=20, seed_text="x")
        for step in range(30):
            window.append(words(2, offset=step * 2))
        assert window.turnovers() == pytest.approx(window.generated_tokens / 20)


class TestTokenChunker:
    def test_chunks_are_exactly_chunk_size(self, whitespace_tokenizer: WhitespaceTokenizer) -> None:
        chunker = TokenChunker(whitespace_tokenizer, chunk_size=16)
        emitted = []
        for step in range(20):
            emitted.extend(chunker.feed(words(7, offset=step * 7)))
        assert emitted
        assert all(chunk.n_tokens == 16 for chunk in emitted)

    def test_chunks_are_contiguous_and_non_overlapping(
        self, whitespace_tokenizer: WhitespaceTokenizer
    ) -> None:
        chunker = TokenChunker(whitespace_tokenizer, chunk_size=8)
        emitted = []
        for step in range(30):
            emitted.extend(chunker.feed(words(5, offset=step * 5)))
        for previous, current in itertools.pairwise(emitted):
            assert current.token_start == previous.token_end
            assert current.index == previous.index + 1

    def test_token_accounting_reconciles(self, whitespace_tokenizer: WhitespaceTokenizer) -> None:
        """Emitted + pending must equal everything fed in, with nothing lost."""
        chunker = TokenChunker(whitespace_tokenizer, chunk_size=12)
        total_fed = 0
        emitted = []
        for step in range(25):
            text = words(6, offset=step * 6)
            total_fed += len(whitespace_tokenizer.encode(text))
            emitted.extend(chunker.feed(text))
        accounted = sum(c.n_tokens for c in emitted) + chunker.pending_tokens
        # Re-tokenising the concatenation can merge across boundaries, so allow a
        # small slack; a systematic gap would show up as a failure here.
        assert abs(accounted - total_fed) <= 2

    def test_flush_partial_reports_the_remainder(
        self, whitespace_tokenizer: WhitespaceTokenizer
    ) -> None:
        chunker = TokenChunker(whitespace_tokenizer, chunk_size=100)
        chunker.feed(words(20))
        partial = chunker.flush_partial()
        assert partial is not None
        assert 0 < partial.n_tokens < 100

    def test_no_partial_when_nothing_pending(
        self, whitespace_tokenizer: WhitespaceTokenizer
    ) -> None:
        chunker = TokenChunker(whitespace_tokenizer, chunk_size=4)
        chunker.feed(" a b c d")
        assert chunker.flush_partial() is None

    def test_nonpositive_chunk_size_is_rejected(
        self, whitespace_tokenizer: WhitespaceTokenizer
    ) -> None:
        with pytest.raises(WindowProtocolError):
            TokenChunker(whitespace_tokenizer, chunk_size=0)


class TestTokenizerRoundTrip:
    @pytest.mark.parametrize(
        "text",
        [
            "plain ascii text",
            "  leading and trailing  ",
            "tabs\tand\nnewlines\n\n",
            "unicode: \u00fcber \u6f22\u5b57 \u0442\u0435\u043a\u0441\u0442",
            "a" * 1000,
        ],
    )
    def test_whitespace_tokenizer_is_lossless(self, text: str) -> None:
        tokenizer = WhitespaceTokenizer()
        assert tokenizer.roundtrip_ok(text)

    def test_tail_returns_requested_token_count(self) -> None:
        tokenizer = WhitespaceTokenizer()
        text = words(500)
        tail, count = tokenizer.tail(text, 64)
        assert count == 64
        assert len(tokenizer.encode(tail)) == 64
        assert text.endswith(tail)

    def test_tail_of_short_text_is_the_whole_text(self) -> None:
        tokenizer = WhitespaceTokenizer()
        tail, count = tokenizer.tail("a b c", 100)
        assert tail == "a b c"
        assert count == len(tokenizer.encode("a b c"))
