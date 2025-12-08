from pathlib import Path
import pandas as pd

app_dir = Path(__file__).parent

# FAST LOAD: Reads the pre-processed Parquet file
# (Contains CRASH_DATE, YEAR, CRASH_HOUR_MINUTE already converted)
df = pd.read_parquet(app_dir / "optimized_data.parquet")

# --- PRE-CALCULATE GROUPS ---
# We do this here so these variables are ready for the app
# Grouping is fast; date conversion was the slow part.

# Used for the Animated Graph
time_grouped = (
    df.groupby(["CRASH_HOUR_MINUTE", "YEAR"]).size().reset_index(name="count")
)

# Used for the Heatmap and Year Filter
day_grouped = (
    df.groupby(["YEAR", df["CRASH_DATE"].dt.date])
    .size()
    .reset_index(name="count")
    .rename(columns={0: "count"})
)
day_grouped["CRASH_DATE"] = pd.to_datetime(day_grouped["CRASH_DATE"])