import pandas as pd
import requests
from io import StringIO

HEADERS = {"User-Agent": "Mozilla/5.0"}

D3_STAT_LAB_ROSTER_URL = "https://thed3statlab.com/reports/team_roster_report.html"
# Add NPI URL here once you have the exact Stat Lab NPI page.
D3_STAT_LAB_NPI_URL = ""


def get_tables(url: str):
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return pd.read_html(StringIO(response.text))


def inspect_d3_stat_lab_roster():
    tables = get_tables(D3_STAT_LAB_ROSTER_URL)

    print(f"Found {len(tables)} roster tables")

    for i, table in enumerate(tables[:5]):
        print("\n" + "=" * 50)
        print(f"TABLE {i}")
        print("=" * 50)
        print(table.head())
        print(table.columns)


if __name__ == "__main__":
    inspect_d3_stat_lab_roster()