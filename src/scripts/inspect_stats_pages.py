import pandas as pd
import requests
from io import StringIO

REQUEST_TIMEOUT = 15  # seconds; prevents a hung site from freezing the app

SCIAC_URL = "https://thesciac.org/stats.aspx?path=wbball&year=2025"
CMS_URL = "https://cmsathletics.org/sports/womens-basketball/stats"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def read_tables_from_url(url: str):
    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return pd.read_html(StringIO(response.text))


def inspect_page(name: str, url: str):
    print(f"\n=== {name} ===")
    tables = read_tables_from_url(url)

    print(f"Found {len(tables)} tables")

    for i, table in enumerate(tables):
        print(f"\n--- Table {i} ---")
        print(f"Shape: {table.shape}")
        print("Columns:")
        print(list(table.columns))
        print(table.head())


if __name__ == "__main__":
    inspect_page("SCIAC", SCIAC_URL)
    inspect_page("CMS", CMS_URL)