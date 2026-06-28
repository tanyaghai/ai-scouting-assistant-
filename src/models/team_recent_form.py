from src.storage.team_repository import get_team_data


def classify_team_recent_form(team_data: dict) -> dict:
    recent = team_data.get("recent_team_trends", {})

    ppg = recent.get("ppg") or 0
    wins = recent.get("wins") or 0
    losses = recent.get("losses") or 0
    fg_pct = recent.get("fg_pct") or 0
    three_pct = recent.get("three_pct") or 0
    turnovers = recent.get("turnovers") or 0
    steals = recent.get("steals") or 0
    rebounds = recent.get("rebounds") or 0

    recent_identity = []
    recent_strengths = []
    recent_areas_to_attack = []

    if wins >= 4:
        recent_identity.append("Hot recent stretch")
    elif losses >= 4:
        recent_identity.append("Struggling recently")
    else:
        recent_identity.append("Mixed recent results")

    if ppg >= 70:
        recent_strengths.append("Recent scoring surge")
    elif ppg < 58:
        recent_areas_to_attack.append("Recent offensive struggles")

    if fg_pct >= 0.42:
        recent_strengths.append("Shooting it well recently")
    elif fg_pct < 0.37:
        recent_areas_to_attack.append("Recent inefficient shooting")

    if three_pct >= 0.34:
        recent_strengths.append("Recent strong three-point shooting")
    elif three_pct < 0.29:
        recent_areas_to_attack.append("Recent poor three-point shooting")

    if turnovers >= 15:
        recent_areas_to_attack.append("Recently turnover-prone")
    elif turnovers <= 12:
        recent_strengths.append("Taking care of the ball recently")

    if steals >= 10:
        recent_strengths.append("Creating recent defensive pressure")

    if rebounds >= 40:
        recent_strengths.append("Strong recent rebounding")
    elif rebounds < 34:
        recent_areas_to_attack.append("Recent rebounding weakness")

    if not recent_areas_to_attack:
        recent_areas_to_attack.append("No major recent statistical weakness")

    return {
        "team_name": team_data.get("team_name"),
        "season": team_data.get("season"),
        "recent_identity": recent_identity,
        "recent_strengths": recent_strengths,
        "recent_areas_to_attack": recent_areas_to_attack,
        "last5_summary_stats": recent,
    }


def classify_team_recent_form_by_name(team_name: str) -> dict:
    team_data = get_team_data(team_name)
    return classify_team_recent_form(team_data)


if __name__ == "__main__":
    result = classify_team_recent_form_by_name("Claremont_Mudd_Scripps")
    print(result)