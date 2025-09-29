from pathlib import Path

import pandas as pd

app_dir = Path(__file__).parent
pen_df = pd.read_csv(app_dir / "penguins.csv")
df = pd.read_csv(app_dir / "salaries_clean.csv")

