import pandas as pd
import requests
from io import StringIO
from src.storage.cache_manager import save_team_data

SCIAC_URL = "https://thesciac.org/stats.aspx?path=wbball&year=2025"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

TEAM_TABLES = {
    "ppg": 0,
    "scoring_margin": 1,
    "fg_pct": 3,
    "three_pct": 5,
    "ft_pct": 8,
    "rebounds": 10,
    "turnovers": 14,
    "ast_to_ratio": 16,
    "blocks": 17,
    "steals": 18,
    "assists": 19,
}

def get_sciac_tables():
    response = requests.get(SCIAC_URL, headers=HEADERS)
    response.raise_for_status()

    return pd.read_html(StringIO(response.text))


def clean_base_table(table: pd.DataFrame, stat_name: str, value_column: str) -> pd.DataFrame:
    return table[["Team", value_column]].rename(columns={value_column: stat_name})


def build_team_stats_dataframe():
    tables = get_sciac_tables()

    team_stats = tables[0][["Team", "G", "W-L", "PTS", "AVG/G"]].rename(
        columns={
            "AVG/G": "ppg",
            "PTS": "points",
            "W-L": "record",
            "G": "games"
        }
    )

    team_stats = team_stats.merge(
        tables[1][["Team", "Defense", "Margin"]].rename(
            columns={"Defense": "opp_ppg", "Margin": "scoring_margin"}
        ),
        on="Team",
        how="left"
    )

    stat_tables = {
        "fg_pct": (3, "PCT"),
        "three_pct": (5, "PCT"),
        "ft_pct": (8, "PCT"),
        "rebounds_per_game": (10, "AVG/G"),
        "turnovers_forced_per_game": (14, "AVG/G"),
        "ast_to_ratio": (16, "Ratio"),
        "blocks_per_game": (17, "AVG/G"),
        "steals_per_game": (18, "AVG/G"),
        "assists_per_game": (19, "AVG/G"),
    }

    for stat_name, (table_index, value_column) in stat_tables.items():
        temp = clean_base_table(tables[table_index], stat_name, value_column)
        team_stats = team_stats.merge(temp, on="Team", how="left")

    return team_stats

def save_sciac_teams_to_cache():
    df = build_team_stats_dataframe()

    for _, row in df.iterrows():
        team_name = row["Team"]

        team_stats = row.drop(labels=["Team"]).to_dict()

        data = {
            "source": "SCIAC",
            "season": "2025",
            "team_stats": team_stats,
            "player_stats": []
        }

        save_team_data(team_name, data)

    print(f"Saved {len(df)} SCIAC teams to cache.")


if __name__ == "__main__":
    df = build_team_stats_dataframe()
    print(df)

    df.to_csv("data/processed/sciac_wbb_team_stats_2025.csv", index=False)

    save_sciac_teams_to_cache()