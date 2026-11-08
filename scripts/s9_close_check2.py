from pathlib import Path

import pandas as pd

from semantic_afterlife.config import get_settings

settings = get_settings()
degen = pd.read_csv(settings.paths.stage_artifacts("9") / "degeneracy" / "degeneracy_verdicts.csv")
print(degen.loc[degen["degenerate"] == False, ["cell", "trajectory_id", "looping_fraction", "n_chunks", "n_chunks_post_horizon"]])
print("--- instruct-int8 ids ---")
print(sorted(degen.loc[degen["cell"] == "instruct-int8", "trajectory_id"]))
locks = pd.read_csv(settings.paths.stage_artifacts("9") / "locks" / "persistence_locks_all.csv")
print("locks instruct-nf4", locks.loc[locks["cell"]=="instruct-nf4", "trajectory_id"].nunique())
print("locks vs degen nondeg in lock table?")
non = set(degen.loc[degen["degenerate"] == False, "trajectory_id"])
print(locks.loc[locks["trajectory_id"].isin(non), ["cell", "embedding", "trajectory_id", "confirmed_lock"]])
