from src.pipelines.scouting_context_builder import build_scouting_context


def format_list(items):
    if not items:
        return "None listed"
    return "\n".join([f"- {item}" for item in items])


def build_report(team_name: str, coach_notes: str = "") -> str:
    context = build_scouting_context(team_name)

    team_style = context["team_style"]
    team_recent = context["team_recent_form"]
    team_ml = context.get("team_ml_profile", {})

    lines = []

    lines.append(f"# Scouting Report: {context['team_name']}")
    lines.append(f"Season: {context['season']}")
    lines.append("")

    if coach_notes:
        lines.append("## Coach Notes")
        lines.append(coach_notes)
        lines.append("")

    lines.append("## Team Identity")
    team_ml_archetype = team_ml.get("team_ml_archetype", "N/A")

    lines.append(f"ML Archetype: {team_ml_archetype}")
    lines.append(team_ml.get("team_archetype_explanation", ""))
    lines.append("")
    lines.append("Offensive Identity:")
    lines.append(format_list(team_style.get("offensive_identity", [])))
    lines.append("")
    lines.append("Defensive Identity:")
    lines.append(format_list(team_style.get("defensive_identity", [])))
    lines.append("")

    lines.append("## Strengths")
    lines.append(format_list(team_style.get("strengths", [])))
    lines.append("")

    lines.append("## Areas to Attack")
    lines.append(format_list(team_style.get("areas_to_attack", [])))
    lines.append("")

    lines.append("## Recent Form")
    lines.append(format_list(team_recent.get("recent_identity", [])))
    lines.append("")
    lines.append("Recent Strengths:")
    lines.append(format_list(team_recent.get("recent_strengths", [])))
    lines.append("")
    lines.append("Recent Areas to Attack:")
    lines.append(format_list(team_recent.get("recent_areas_to_attack", [])))
    lines.append("")

    lines.append("## Key Players")
    for player in context["players"][:8]:
        role = player["rule_based_profile"]
        recent = player.get("recent_form", {})
        ml = player.get("ml_profile", {})

        lines.append(f"### {player['name']}")
        lines.append(f"Role: {role.get('primary_role')}")
        ml_archetype = ml.get("ml_archetype", "N/A")
        ml_fit = ml.get("archetype_fit")

        if ml_fit and str(ml_fit) != "nan":
            lines.append(f"ML Archetype: {ml_archetype} ({ml_fit})")
        else:
            lines.append(f"ML Archetype: {ml_archetype}")
        stats = role.get("stats", {})
        lines.append(
            f"Stats: {stats.get('ppg')} PPG, {stats.get('rpg')} RPG, "
            f"{stats.get('apg')} APG, {stats.get('spg')} SPG, "
            f"{stats.get('mpg')} MPG"
        )
        lines.append("Offensive Profile:")
        lines.append(format_list(role.get("offensive_profile", [])))
        lines.append("Defensive Profile:")
        lines.append(format_list(role.get("defensive_profile", [])))
        lines.append("Recent Form:")
        lines.append(format_list(recent.get("recent_form", [])))
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    report = build_report(
        "Claremont_Mudd_Scripps",
        coach_notes="Example: team has been experimenting with more zone and shorter rotations.",
    )
    print(report)