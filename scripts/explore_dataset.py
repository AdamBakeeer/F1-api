import pandas as pd

files = [
    "drivers.csv",
    "constructors.csv",
    "circuits.csv",
    "races.csv",
    "results.csv",
    "status.csv"
]

for file in files:
    df = pd.read_csv(f"data/{file}")
    print("\n" + "="*70)
    print(f"{file}")
    print("Rows:", len(df))
    print("Columns:")
    print(df.columns.tolist())