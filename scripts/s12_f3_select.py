"""Apply ADR-0023 F3 to L0 lock tables. Read-only. Does not use G_t."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

SEED_ORDER = [
    "physics",
    "finance",
    "biology",
    "war",
    "love",
    "recipe",
    "programming",
    "philosophy",
    "surreal",
    "noise",
]
FILES = [
    ("s9", Path("artifacts/stage-9/locks/persistence_locks_all.csv")),
    ("s10", Path("artifacts/stage-10/locks/persistence_locks_all.csv")),
    ("s11", Path("artifacts/stage-11/locks/persistence_locks_all.csv")),
]


def sto_id(value: str) -> int:
    text = str(value)
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else 99


def main() -> None:
    frames = []
    for stage, path in FILES:
        frame = pd.read_csv(path)
        frame["stage"] = stage
        frames.append(frame)
    locks = pd.concat(frames, ignore_index=True)
    locks = locks[locks["embedding"] == "local-bge-m3"].copy()
    locks["still_locked"] = locks["confirmed_lock"] & ~locks["confirmed_escape"]

    rank_rows = []
    for (stage, cell), block in locks.groupby(["stage", "cell"]):
        rank_rows.append(
            {
                "stage": stage,
                "cell": cell,
                "n_lock": int(block["confirmed_lock"].sum()),
                "n_still": int(block["still_locked"].sum()),
                "n_escape": int(block["confirmed_escape"].sum()),
                "n_seeds_lock": int(block.loc[block["confirmed_lock"], "seed_id"].nunique()),
            }
        )
    rank = pd.DataFrame(rank_rows).sort_values(
        ["n_still", "stage", "cell"], ascending=[False, True, True]
    )
    print("CHECKPOINT RANK by still-locked completers (BGE lock table)")
    print(rank.to_string(index=False))
    print()

    top = rank.head(2)
    for _, row in top.iterrows():
        block = locks[(locks["stage"] == row["stage"]) & (locks["cell"] == row["cell"])]
        locked = block[block["confirmed_lock"]]
        print(f"== F3 {row['stage']} {row['cell']} ==")
        seed_rows = []
        for seed, sblock in locked.groupby("seed_id"):
            med = float(sblock["tau_lock"].median())
            seed_rows.append((seed, med, int(len(sblock)), int(sblock["still_locked"].sum())))
        seed_rows.sort(key=lambda item: (item[1], SEED_ORDER.index(item[0]) if item[0] in SEED_ORDER else 99))
        for seed, med, n, n_still in seed_rows:
            print(f"  seed {seed} median_tau_lock={med} n_locked={n} n_still={n_still}")
        if not seed_rows:
            print("  no qualifying seeds")
            continue
        lowest = seed_rows[0]
        mid = seed_rows[(len(seed_rows) - 1) // 2]
        print(f"  CHOSEN lowest={lowest[0]} ({lowest[1]}) median={mid[0]} ({mid[1]})")
        for seed, _, _, _ in (lowest, mid):
            desc = locked[locked["seed_id"] == seed].copy()
            desc["sto"] = desc["trajectory_id"].map(lambda tid: sto_id(tid.split("__")[-1]))
            desc = desc.sort_values(["tau_lock", "sto"])
            print(f"  descendants {seed} (smallest tau_lock, then sto):")
            for _, d in desc.head(4).iterrows():
                print(
                    f"    {d['trajectory_id'].split('__')[-1]} tau_lock={d['tau_lock']} "
                    f"escape={d['confirmed_escape']} tau_escape={d['tau_escape']} still={d['still_locked']}"
                )
        print()


if __name__ == "__main__":
    main()
