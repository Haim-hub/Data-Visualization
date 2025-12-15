from pathlib import Path
import pandas as pd

app_dir = Path(__file__).parent

df = pd.read_parquet(app_dir / "optimized_data.parquet")


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