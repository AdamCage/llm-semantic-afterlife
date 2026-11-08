import pandas as pd

locks = pd.read_csv("artifacts/stage-9/locks/persistence_locks_all.csv")
print(locks.groupby(["cell", "embedding"])["tau_lock"].agg(["min", "max", "nunique", "count"]))
print("escape", int(locks["confirmed_escape"].sum()))
print("unique tau", sorted(locks["tau_lock"].dropna().unique().tolist()))
