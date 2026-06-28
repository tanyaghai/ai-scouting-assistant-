from src.storage.team_repository import get_team_data


def classify_recent_form(player_recent: dict) -> dict:
    ppg = player_recent.get("last5_points") or 0
    mpg = player_recent.get("last5_minutes") or 0
    rpg = player_recent.get("last5_rebounds") or 0
    apg = player_recent.get("last5_assists") or 0
    spg = player_recent.get("last5_steals") or 0
    games = player_recent.get("games_played_recent") or 0

    form_tags = []

    if games < 3:
        form_tags.append("Limited recent sample")

    if mpg >= 28:
        form_tags.append("Heavy recent minutes")

    if ppg >= 14:
        form_tags.append("Hot recent scorer")
    elif ppg >= 8:
        form_tags.append("Steady recent scorer")

    if rpg >= 6:
        form_tags.append("Recent rebounding impact")

    if apg >= 2.5:
        form_tags.append("Recent playmaking impact")

    if spg >= 1.5:
        form_tags.append("Recent defensive activity")

    if not form_tags:
        form_tags.append("Limited recent impact")

    return {
        "name": player_recent.get("name"),
        "recent_form": form_tags,
        "last5_stats": {
            "games": games,
            "ppg": ppg,
            "mpg": mpg,
            "rpg": rpg,
            "apg": apg,
            "spg": spg,
        },
    }


def classify_team_recent_player_form(team_name: str):
    team_data = get_team_data(team_name)
    recent_players = team_data.get("recent_player_impact", [])

    return [classify_recent_form(player) for player in recent_players]


if __name__ == "__main__":
    forms = classify_team_recent_player_form("Claremont_Mudd_Scripps")

    for form in forms:
        print(form)