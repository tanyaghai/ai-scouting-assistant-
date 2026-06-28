from src.storage.team_repository import get_team_data


def classify_team_style(team_data: dict) -> dict:
    team_stats = team_data.get("team_stats", {})
    advanced = team_data.get("advanced_team_metrics", {})

    ppg = team_stats.get("ppg") or 0
    rebounds = team_stats.get("rebounds_per_game") or 0
    assists = team_stats.get("assists_per_game") or 0
    turnovers = team_stats.get("turnovers_per_game") or 0
    steals = team_stats.get("steals_per_game") or 0
    blocks = team_stats.get("blocks_per_game") or 0
    three_pct = team_stats.get("three_pct") or 0
    fg_pct = team_stats.get("fg_pct") or 0

    possessions = advanced.get("possessions_per_game") or 0
    efg_pct = advanced.get("efg_pct") or 0
    tov_pct = advanced.get("tov_pct") or 0
    ft_rate = advanced.get("ft_rate") or 0
    assist_rate = advanced.get("team_assist_rate") or 0

    offensive_identity = []
    defensive_identity = []
    strengths = []
    areas_to_attack = []

    if possessions >= 75:
        offensive_identity.append("Up-tempo team")
    elif possessions <= 66:
        offensive_identity.append("Slower-paced team")
    else:
        offensive_identity.append("Moderate pace")

    if ppg >= 70:
        strengths.append("High-scoring offense")
    elif ppg < 60:
        areas_to_attack.append("Lower-scoring offense")

    if efg_pct >= 0.48 or fg_pct >= 0.42:
        strengths.append("Efficient shooting team")
    elif efg_pct >= 0.43:
        offensive_identity.append("Average shooting efficiency")
    else:
        areas_to_attack.append("Below-average overall shooting efficiency")

    if three_pct >= 0.34:
        strengths.append("Strong perimeter shooting")
    elif three_pct >= 0.30:
        offensive_identity.append("Average perimeter shooting")
    else:
        areas_to_attack.append("Below-average perimeter shooting")

    if assist_rate >= 0.55 or assists >= 14:
        offensive_identity.append("Ball-movement oriented")
        strengths.append("Creates assisted baskets")
    elif assist_rate >= 0.48:
        offensive_identity.append("Balanced creation profile")
    else:
        areas_to_attack.append("Lower assist rate")

    if tov_pct >= 21 or turnovers >= 16:
        areas_to_attack.append("Can be turnover-prone")
    elif tov_pct <= 17 or turnovers <= 13:
        strengths.append("Takes care of the ball")

    if fg_pct < 0.40:
        areas_to_attack.append("Force contested twos / inefficient finishes")

    if turnovers >= 14:
        areas_to_attack.append("Apply pressure and make them handle")    

    if steals >= 10:
        defensive_identity.append("Pressure defense")
        strengths.append("Generates steals")
    elif steals >= 7:
        defensive_identity.append("Moderate defensive pressure")
    else:
        areas_to_attack.append("Limited steal production")

    if blocks >= 3.5:
        defensive_identity.append("Interior shot-blocking presence")
        strengths.append("Protects the rim")

    if rebounds >= 40:
        strengths.append("Strong rebounding team")
    elif rebounds >= 36:
        defensive_identity.append("Solid rebounding team")
    else:
        areas_to_attack.append("Can be attacked on the glass")

    if ft_rate >= 0.32:
        strengths.append("Gets to the free throw line")
    elif ft_rate < 0.24:
        areas_to_attack.append("Low free throw pressure")

    if not areas_to_attack:
        if three_pct < 0.32:
            areas_to_attack.append("Make them prove it from three")

        if turnovers > 12:
            areas_to_attack.append("Pressure ball handlers and test decision-making")

        if blocks < 3:
            areas_to_attack.append("Attack the paint; limited rim protection")

        if not areas_to_attack:
            areas_to_attack.append("No obvious statistical weakness; focus on personnel tendencies")

    return {
        "team_name": team_data.get("team_name"),
        "season": team_data.get("season"),
        "offensive_identity": offensive_identity,
        "defensive_identity": defensive_identity,
        "strengths": strengths,
        "areas_to_attack": areas_to_attack,
        "summary_stats": {
            "ppg": ppg,
            "possessions_per_game": possessions,
            "efg_pct": efg_pct,
            "fg_pct": fg_pct,
            "three_pct": three_pct,
            "assists_per_game": assists,
            "turnovers_per_game": turnovers,
            "steals_per_game": steals,
            "rebounds_per_game": rebounds,
            "ft_rate": ft_rate,
            "assist_rate": assist_rate,
        },
    }


def classify_team_style_by_name(team_name: str) -> dict:
    team_data = get_team_data(team_name)
    return classify_team_style(team_data)


if __name__ == "__main__":
    result = classify_team_style_by_name("Whittier")
    print(result)