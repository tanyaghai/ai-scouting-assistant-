import re
from io import StringIO

import pandas as pd
import requests

from src.storage.cache_manager import load_team_data, save_team_data


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


SCIAC_TEAM_STATS_URLS = {
    "Claremont-Mudd-Scripps": "https://cmsathletics.org/sports/womens-basketball/stats",
    "Redlands": "https://goredlands.com/sports/womens-basketball/stats",
    "Chapman": "https://athletics.chapman.edu/sports/womens-basketball/stats",
    "Pomona-Pitzer": "https://sagehens.com/sports/womens-basketball/stats",
    "California Lutheran": "https://clusports.com/sports/womens-basketball/stats",
    "Caltech": "https://gocaltech.com/sports/womens-basketball/stats",
    "La Verne": "https://leopardathletics.com/sports/womens-basketball/stats",
    "Whittier": "https://wcpoets.com/sports/womens-basketball/stats",
    "Occidental": "https://oxyathletics.com/sports/womens-basketball/stats",
}


def clean_value(value):
    if pd.isna(value):
        return None
    return value


def get_tables(url: str):
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return pd.read_html(StringIO(response.text))


def clean_player_name(name: str) -> str:
    name = str(name)

    match = re.search(r"([A-Za-z'\-]+),\s*([A-Za-z'\-]+)", name)

    if match:
        last = match.group(1)
        first = match.group(2)
        return f"{first} {last}"

    name = re.sub(r"^#?\d+\s*", "", name)
    return name.strip()


def get_full_roster_stats(url: str) -> list[dict]:
    tables = get_tables(url)
    roster = tables[1].copy()

    players = []

    for _, row in roster.iterrows():
        raw_name = row.iloc[1]

        if pd.isna(raw_name):
            continue

        player = {
            "name": clean_player_name(raw_name),
            "games": clean_value(row.iloc[2]),
            "games_started": clean_value(row.iloc[3]),
            "minutes": clean_value(row.iloc[4]),
            "minutes_per_game": clean_value(row.iloc[5]),
            "fgm": clean_value(row.iloc[6]),
            "fga": clean_value(row.iloc[7]),
            "fg_pct": clean_value(row.iloc[8]),
            "three_made": clean_value(row.iloc[9]),
            "three_attempts": clean_value(row.iloc[10]),
            "three_pct": clean_value(row.iloc[11]),
            "ftm": clean_value(row.iloc[12]),
            "fta": clean_value(row.iloc[13]),
            "ft_pct": clean_value(row.iloc[14]),
            "points": clean_value(row.iloc[15]),
            "ppg": clean_value(row.iloc[16]),
            "off_rebounds": clean_value(row.iloc[17]),
            "def_rebounds": clean_value(row.iloc[18]),
            "rebounds": clean_value(row.iloc[19]),
            "rpg": clean_value(row.iloc[20]),
            "fouls": clean_value(row.iloc[21]),
            "assists": clean_value(row.iloc[22]),
            "turnovers": clean_value(row.iloc[23]),
            "steals": clean_value(row.iloc[24]),
            "blocks": clean_value(row.iloc[25]),
        }

        players.append(player)

    return players


def save_roster_to_cache(team_name: str, url: str):
    players = get_full_roster_stats(url)

    try:
        team_data = load_team_data(team_name)
    except FileNotFoundError:
        team_data = {
            "source": "Sidearm",
            "season": "2025",
            "team_stats": {}
        }

    team_data["player_stats"] = players
    team_data["player_stats_source_url"] = url

    save_team_data(team_name, team_data)

    print(f"Saved {len(players)} players for {team_name}")


def save_all_sciac_rosters_to_cache():
    for team_name, url in SCIAC_TEAM_STATS_URLS.items():
        save_roster_to_cache(team_name, url)


if __name__ == "__main__":
    save_all_sciac_rosters_to_cache()