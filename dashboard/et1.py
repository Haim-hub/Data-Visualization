import pandas as pd
from pathlib import Path

app_dir = Path(__file__).parent
csv_path = app_dir / "Motor_Vehicle_Collisions_-_Person_20251020.csv"
output_path = app_dir / "optimized_data.parquet"

keep_cols = [
    "CRASH_DATE", "CRASH_TIME", "PERSON_AGE", "PERSON_SEX", "PERSON_TYPE",
    "POSITION_IN_VEHICLE", "SAFETY_EQUIPMENT", "EJECTION", 
    "PED_LOCATION", "PED_ACTION", "BODILY_INJURY", "PERSON_INJURY"
]

df = pd.read_csv(csv_path, usecols=keep_cols)

print("2. Processing Dates...")
df["CRASH_DATE"] = pd.to_datetime(df["CRASH_DATE"])
df["CRASH_TIME"] = pd.to_datetime(df["CRASH_TIME"], format="%H:%M")

df["PERSON_AGE"] = pd.to_numeric(df["PERSON_AGE"], errors='coerce')


df["CRASH_HOUR_MINUTE"] = df["CRASH_TIME"].dt.floor("15T").dt.strftime("%H:%M")
df["YEAR"] = df["CRASH_DATE"].dt.year

print(f"5. Saving to {output_path}...")
df.to_parquet(output_path)
print("Done!")