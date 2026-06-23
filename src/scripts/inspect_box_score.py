import pandas as pd
import requests
from io import StringIO

URL = "https://cmsathletics.org/boxscore.aspx?id=9826&path=wbball"

response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
response.raise_for_status()

tables = pd.read_html(StringIO(response.text))

print(f"Found {len(tables)} tables")

for i, table in enumerate(tables):
    print("\n" + "=" * 60)
    print(f"TABLE {i}")
    print("=" * 60)
    print(table.head())
    print(table.columns)