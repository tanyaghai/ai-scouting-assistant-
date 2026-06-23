import pandas as pd

from src.storage.cache_manager import load_team_data
from src.data_collection.team_box_scores import get_last_five_box_score_links
from src.data_collection.box_score_collector import get_box_score_player_stats


NUMERIC_COLUMNS = [
    "minutes",
    "fgm",
    "fga",
    "three_made",
    "three_attempts",
    "ftm",
    "fta",
    "rebounds",
    "fouls",
    "assists",
    "turnovers",
    "blocks",
    "steals",
    "points",
]


def normalize_name(name: str) -> str:
    name = str(name).strip()

    if "," in name:
        last, first = name.split(",", 1)
        name = f"{first.strip()} {last.strip()}"

    return (
        name
        .lower()
        .replace(",", "")
        .replace(".", "")
        .replace("-", " ")
        .strip()
    )


def get_roster_names(team_name: str) -> set[str]:
    team_data = load_team_data(team_name)
    players = team_data.get("player_stats", [])

    return {
        normalize_name(player["name"])
        for player in players
        if player.get("name")
    }


def get_recent_player_impact(team_name: str, stats_url: str):
    roster_names = get_roster_names(team_name)
    links = get_last_five_box_score_links(stats_url)

    all_rows = []

    for link in links:
        box_score = get_box_score_player_stats(link["url"])

        all_players = (
            box_score["team_one_players"]
            + box_score["team_two_players"]
        )

        for player in all_players:
            player_name = normalize_name(player["name"])

            if player_name not in roster_names:
                continue

            row = player.copy()
            row["opponent"] = link["opponent"]
            row["box_score_url"] = link["url"]
            all_rows.append(row)

    df = pd.DataFrame(all_rows)
    if df.empty:
        print(f"No matching players found for {team_name}.")
        print("Check roster name formatting vs box score name formatting.")
        return df

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    grouped = df.groupby("name").agg(
        games_played_recent=("name", "count"),
        last5_minutes=("minutes", "mean"),
        last5_points=("points", "mean"),
        last5_rebounds=("rebounds", "mean"),
        last5_assists=("assists", "mean"),
        last5_steals=("steals", "mean"),
        last5_blocks=("blocks", "mean"),
        last5_turnovers=("turnovers", "mean"),
        last5_fga=("fga", "mean"),
        last5_three_attempts=("three_attempts", "mean"),
    ).reset_index()

    return grouped.sort_values(
        by=["last5_points", "last5_minutes"],
        ascending=False
    )


if __name__ == "__main__":
    redlands_url = "https://goredlands.com/sports/womens-basketball/stats"

    df = get_recent_player_impact("Redlands", redlands_url)
    
    
    print(df)