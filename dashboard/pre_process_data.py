import pandas as pd

# 1. Load your current data
df = pd.read_parquet("optimized_data.parquet")

# 2. Ensure dates are efficient
df["CRASH_DATE"] = pd.to_datetime(df["CRASH_DATE"])
df["YEAR"] = df["YEAR"].astype(int)

# 3. GENERATE SUMMARY FILES (Tiny files for fast loading)
# Group 1: Time of day animation
time_grouped = (
    df.groupby(["CRASH_HOUR_MINUTE", "YEAR"]).size().reset_index(name="count")
)
time_grouped.to_parquet("summary_time.parquet")

# Group 2: Calendar Heatmap
# Normalize date to remove time component for grouping
df["DATE_ONLY"] = df["CRASH_DATE"].dt.normalize()
day_grouped = (
    df.groupby(["YEAR", "DATE_ONLY"])
    .size()
    .reset_index(name="count")
    .rename(columns={"DATE_ONLY": "CRASH_DATE"})
)
day_grouped.to_parquet("summary_day.parquet")

print("Pre-processing complete. Upload 'summary_time.parquet' and 'summary_day.parquet'.")