from src.data_collection.sidearm_collector import get_tables


def get_team_game_log(url: str):
    tables = get_tables(url)

    game_log = tables[5].copy()

    game_log = game_log[game_log["W/L"].notna()]
    game_log = game_log[game_log["Score"] != "-"]

    return game_log


def get_last_five_games(url: str):
    game_log = get_team_game_log(url)
    return game_log.tail(5)


def summarize_last_five_team_trends(url: str):
    last_five = get_last_five_games(url)

    summary = {
        "games": int(len(last_five)),
        "wins": int((last_five["W/L"] == "W").sum()),
        "losses": int((last_five["W/L"] == "L").sum()),
        "ppg": float(round(last_five["PTS"].mean(), 1)),
        "fg_pct": float(round(last_five["PCT"].mean(), 3)),
        "three_pct": float(round(last_five["PCT.1"].mean(), 3)),
        "ft_pct": float(round(last_five["PCT.2"].mean(), 3)),
        "rebounds": float(round(last_five["TOT"].mean(), 1)),
        "assists": float(round(last_five["AST"].mean(), 1)),
        "turnovers": float(round(last_five["TO"].mean(), 1)),
        "steals": float(round(last_five["STL"].mean(), 1)),
        "blocks": float(round(last_five["BLK"].mean(), 1)),
    }

    return summary


if __name__ == "__main__":
    cms_url = "https://cmsathletics.org/sports/womens-basketball/stats"

    print(summarize_last_five_team_trends(cms_url))