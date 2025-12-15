from pathlib import Path
import pandas as pd
import gc # Garbage collection

app_dir = Path(__file__).parent

# 1. Load the data
df_loaded = pd.read_parquet(app_dir / "optimized_data.parquet")
df = df_loaded.sample(n=300000, random_state=42)

# 2. CRITICAL MEMORY FIX: Convert String columns to Categories
# Even if they are compact on disk, strings take huge RAM. 
# Categories use integers pointers (tiny).
cat_cols = [
    "PERSON_SEX", "PERSON_TYPE", "POSITION_IN_VEHICLE", 
    "SAFETY_EQUIPMENT", "EJECTION", "PED_LOCATION", 
    "PED_ACTION", "BODILY_INJURY", "PERSON_INJURY"
]

for col in cat_cols:
    # Only convert if the column exists and is currently an object (string)
    if col in df.columns and df[col].dtype == 'object':
        df[col] = df[col].astype('category')

# 3. OPTIMIZE DATE GROUPING
# OLD WAY: df["CRASH_DATE"].dt.date creates a Python object for every row (Very Expensive)
# NEW WAY: .dt.normalize() sets time to 00:00:00 but keeps it as a compact datetime64 type.
df["CRASH_DATE_NORMALIZED"] = df["CRASH_DATE"].dt.normalize()

time_grouped = (
    df.groupby(["CRASH_HOUR_MINUTE", "YEAR"]).size().reset_index(name="count")
)

# Now group by the normalized timestamp (efficient) instead of date objects
day_grouped = (
    df.groupby(["YEAR", "CRASH_DATE_NORMALIZED"])
    .size()
    .reset_index(name="count")
    .rename(columns={"CRASH_DATE_NORMALIZED": "CRASH_DATE"})
)

# 4. CLEANUP
# If you don't need the helper column in the main dataframe, drop it to save space
del df["CRASH_DATE_NORMALIZED"]

# Force Python to release memory from the intermediate steps immediately
gc.collect()
