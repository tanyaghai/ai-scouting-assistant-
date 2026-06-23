import re
from io import StringIO
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_tables(url: str):
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return pd.read_html(StringIO(response.text))


def clean_player_name(name: str) -> str:
    name = str(name)
    name = re.sub(r"^\d+\s*", "", name).strip()
    return name


def split_made_attempted(value: str):
    if pd.isna(value) or "-" not in str(value):
        return None, None

    made, attempted = str(value).split("-", 1)
    return int(made), int(attempted)


def parse_player_box_score(table: pd.DataFrame) -> list[dict]:
    players = []

    for _, row in table.iterrows():
        raw_name = row.get("Player")

        if pd.isna(raw_name):
            continue

        fgm, fga = split_made_attempted(row.get("FG"))
        threem, threea = split_made_attempted(row.get("3PT"))
        ftm, fta = split_made_attempted(row.get("FT"))

        player = {
            "name": clean_player_name(raw_name),
            "minutes": row.get("MIN"),
            "fgm": fgm,
            "fga": fga,
            "three_made": threem,
            "three_attempts": threea,
            "ftm": ftm,
            "fta": fta,
            "rebounds": row.get("REB"),
            "fouls": row.get("PF"),
            "assists": row.get("A"),
            "turnovers": row.get("TO"),
            "blocks": row.get("BLK"),
            "steals": row.get("STL"),
            "points": row.get("PTS"),
        }

        players.append(player)

    return players


def get_box_score_player_stats(url: str):
    tables = get_tables(url)

    # On Sidearm box scores:
    # Table 1 = away/team 1 player box
    # Table 4 = home/team 2 player box
    team_one_players = parse_player_box_score(tables[1])
    team_two_players = parse_player_box_score(tables[4])

    return {
        "team_one_players": team_one_players,
        "team_two_players": team_two_players,
    }


if __name__ == "__main__":
    url = "https://cmsathletics.org/boxscore.aspx?id=9826&path=wbball"

    data = get_box_score_player_stats(url)

    print("Team one players:")
    for player in data["team_one_players"][:5]:
        print(player)

    print("\nTeam two players:")
    for player in data["team_two_players"][:5]:
        print(player)