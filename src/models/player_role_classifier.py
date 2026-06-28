from src.storage.team_repository import get_team_data


MIN_MAJOR_MPG = 18
MIN_ROTATION_MPG = 8


def safe_div(num, den):
    if not den:
        return 0
    return num / den


def classify_player_roles(player: dict, advanced_metrics: dict = None) -> dict:
    advanced_metrics = advanced_metrics or {}

    name = player.get("name")
    games = player.get("games") or 0
    mpg = player.get("minutes_per_game") or 0
    ppg = player.get("ppg") or 0
    rpg = player.get("rpg") or 0
    apg = safe_div(player.get("assists") or 0, games)
    spg = safe_div(player.get("steals") or 0, games)
    bpg = safe_div(player.get("blocks") or 0, games)
    three_attempts = player.get("three_attempts") or 0
    three_pct = player.get("three_pct") or 0

    three_point_rate = advanced_metrics.get("three_point_rate") or 0
    free_throw_rate = advanced_metrics.get("free_throw_rate") or 0
    ts_pct = advanced_metrics.get("ts_pct") or 0
    assist_to_turnover = advanced_metrics.get("assist_to_turnover") or 0
    usage_rate = advanced_metrics.get("usage_rate") or 0

    primary_role = "Deep bench / limited sample"

    offensive_profile = []
    defensive_profile = []
    playmaking_profile = []
    rebounding_profile = []
    efficiency_profile = []

    if mpg >= MIN_MAJOR_MPG:
        if ppg >= 13:
            primary_role = "Primary scorer"
        elif ppg >= 8:
            primary_role = "Secondary scorer"
        elif apg >= 2.5:
            primary_role = "Primary creator"
        elif rpg >= 5.5:
            primary_role = "Interior / rebounding presence"
        else:
            primary_role = "Starter / rotation contributor"
    elif mpg >= MIN_ROTATION_MPG:
        if ppg >= 6:
            primary_role = "Bench scorer"
        else:
            primary_role = "Rotation player"

    if mpg >= MIN_ROTATION_MPG:
        if three_attempts >= 50 and three_pct >= 0.32:
            offensive_profile.append("Three-point threat")

        if usage_rate >= 0.24:
            offensive_profile.append("High-usage player")

        if three_point_rate >= 0.45:
            offensive_profile.append("3PT-heavy shot profile")

        if free_throw_rate >= 0.35 and (mpg >= 18 or ppg >= 5):
            offensive_profile.append("Gets to the line")

        
        if ts_pct >= 0.52 and ppg >= 8:
            efficiency_profile.append("Efficient scorer")
        elif ts_pct >= 0.48:
            efficiency_profile.append("Average efficiency")
        elif ts_pct >= 0.42:
            efficiency_profile.append("Below-average efficiency")
        else:
            efficiency_profile.append("Low-efficiency scorer")

        if apg >= 2.5:
            playmaking_profile.append("Creator / ball handler")

        if apg >= 2 and assist_to_turnover >= 1.5:
            playmaking_profile.append("Low-turnover creator")

        if rpg >= 6:
            rebounding_profile.append("Rebounding threat")

        if spg >= 1.5:
            defensive_profile.append("Defensive disruptor")

        if bpg >= 1:
            defensive_profile.append("Rim protector")

        if mpg >= 12 and ppg < 6 and (spg >= 1.0 or bpg >= 0.5):
            defensive_profile.append("Defensive specialist")

    return {
        "name": name,
        "primary_role": primary_role,
        "offensive_profile": offensive_profile,
        "defensive_profile": defensive_profile,
        "playmaking_profile": playmaking_profile,
        "rebounding_profile": rebounding_profile,
        "efficiency_profile": efficiency_profile,
        "stats": {
            "ppg": ppg,
            "rpg": rpg,
            "apg": round(apg, 1),
            "spg": round(spg, 1),
            "bpg": round(bpg, 1),
            "mpg": mpg,
            "three_pct": three_pct,
            "usage_rate": usage_rate,
            "three_point_rate": three_point_rate,
            "free_throw_rate": free_throw_rate,
            "ts_pct": ts_pct,
            "assist_to_turnover": assist_to_turnover,
        },
    }


def classify_team_player_roles(team_name: str):
    team_data = get_team_data(team_name)
    players = team_data.get("player_stats", [])
    advanced_players = team_data.get("advanced_player_metrics", {})

    results = []

    for player in players:
        name = player.get("name")
        advanced = advanced_players.get(name, {})
        results.append(classify_player_roles(player, advanced))

    results.sort(
        key=lambda p: (
            p["primary_role"] == "Deep bench / limited sample",
            -(p["stats"]["mpg"] or 0),
            -(p["stats"]["ppg"] or 0),
        )
    )

    return results


if __name__ == "__main__":
    roles = classify_team_player_roles("Claremont_Mudd_Scripps")

    for player in roles:
        print(player)