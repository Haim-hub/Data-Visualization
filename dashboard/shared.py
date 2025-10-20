from pathlib import Path

import pandas as pd

import requests

# Fetch data from the NYC OpenData API
url = "https://data.cityofnewyork.us/resource/f55k-p6yu.json"
response = requests.get(url)
data = response.json()

# Convert the JSON data to a pandas DataFrame
df = pd.DataFrame(data)

# Now you can use `df` as your DataFrame, just like before
print(df.head())

