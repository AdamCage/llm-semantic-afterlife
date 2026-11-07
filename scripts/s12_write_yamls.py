"""Write one S12 generate YAML per continuation trajectory."""

from __future__ import annotations

from pathlib import Path

ROOT = Path("configs/stages/stage12_horizon")
CELLS = [
    ("mb-physics-s1", "pb-ministral-8b-base", "Ministral Base continuation of physics s1"),
    ("mb-physics-s2", "pb-ministral-8b-base", "Ministral Base continuation of physics s2"),
    ("mb-love-s1", "pb-ministral-8b-base", "Ministral Base continuation of love s1"),
    ("mb-love-s2", "pb-ministral-8b-base", "Ministral Base continuation of love s2"),
    ("qi-physics-s1", "pb-qwen3-8b-instruct", "Qwen Instruct continuation of physics s1"),
    ("qi-physics-s2", "pb-qwen3-8b-instruct", "Qwen Instruct continuation of physics s2"),
    ("qi-love-s1", "pb-qwen3-8b-instruct", "Qwen Instruct continuation of love s1"),
    ("qi-love-s2", "pb-qwen3-8b-instruct", "Qwen Instruct continuation of love s2"),
]


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    for seed_id, generator, desc in CELLS:
        path = ROOT / f"{seed_id}.yaml"
        path.write_text(
            "\n".join(
                [
                    f"# {desc}. One trajectory. Do not add a second slug.",
                    "include:",
                    "  - configs/stages/stage12_horizon/_base.yaml",
                    f"name: paperb-l2-{seed_id}",
                    "description: >-",
                    f"  S12 L2-escape. {desc}. Tail prompt, additional 4950016 tokens.",
                    "generators:",
                    f"  - {generator}",
                    "semantic_seeds:",
                    f"  - {seed_id}",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        print(path)


if __name__ == "__main__":
    main()
