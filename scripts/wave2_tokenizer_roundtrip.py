"""E8: seed_bank_v1 encode/decode on the ten Paper B tokenizers."""

from __future__ import annotations

from semantic_afterlife.config import load_experiment_config, load_seed_bank
from semantic_afterlife.tokenization import load_tokenizer

CFG = "configs/stages/stage8_paperb_foundations.yaml"
CACHE = "cache/tokenizers"


def main() -> None:
    experiment, _, _ = load_experiment_config(CFG)
    bank = load_seed_bank(experiment.seed_bank)
    texts = [s.text for s in bank.seeds]
    print("n_seeds", len(texts))
    for gen in experiment.generators:
        tok = load_tokenizer(gen.tokenizer_repo, gen.tokenizer_revision, CACHE)
        fails = 0
        for text in texts:
            ids = tok.encode(text)
            back = tok.decode(ids)
            if back != text:
                fails += 1
        print(gen.slug, "roundtrip_fail", fails, "of", len(texts), "rev", gen.tokenizer_revision)


if __name__ == "__main__":
    main()
