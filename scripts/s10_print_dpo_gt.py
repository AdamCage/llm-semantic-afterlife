import pandas as pd

p = "runs/s10/s10-persistence-local-bge-m3-20260918T181744Z-8281a4d8/data/persistence_gt.parquet"
print(pd.read_parquet(p).to_string())
