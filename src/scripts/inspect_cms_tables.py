import pandas as pd
import requests
from io import StringIO

URL = "https://cmsathletics.org/sports/womens-basketball/stats"

response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
tables = pd.read_html(StringIO(response.text))

print(f"Found {len(tables)} tables")

for i, table in enumerate(tables):
    print("\n" + "=" * 60)
    print(f"TABLE {i}")
    print("=" * 60)
    print(table.head())
    print(table.columns)