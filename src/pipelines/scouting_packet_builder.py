from src.pipelines.scouting_context_builder import build_scouting_context
from src.pipelines.player_note_generator import generate_player_note

def format_list(items):
    if not items:
        return "- None listed"
    return "\n".join([f"- {item}" for item in items])


def format_player(player: dict) -> str:
    role = player.get("rule_based_profile", {})
    recent = player.get("recent_form", {})
    ml = player.get("ml_profile", {})
    stats = role.get("stats", {})

    lines = []
    lines.append(f"{player['name']}")
    lines.append(f"- Role: {role.get('primary_role', 'N/A')}")
    lines.append(
        f"- Stats: {stats.get('ppg')} PPG, {stats.get('rpg')} RPG, "
        f"{stats.get('apg')} APG, {stats.get('spg')} SPG, {stats.get('mpg')} MPG"
    )
    lines.append(f"- ML type: {ml.get('ml_archetype', 'N/A')}")

    try:
        note = generate_player_note(player)
        lines.append(f"- Personnel note: {note}")
    except Exception:
        pass

    offense = role.get("offensive_profile", [])
    defense = role.get("defensive_profile", [])
    playmaking = role.get("playmaking_profile", [])
    rebounding = role.get("rebounding_profile", [])
    efficiency = role.get("efficiency_profile", [])
    recent_form = recent.get("recent_form", [])

    if offense:
        lines.append(f"- Offense: {', '.join(offense)}")
    if playmaking:
        lines.append(f"- Playmaking: {', '.join(playmaking)}")
    if defense:
        lines.append(f"- Defense: {', '.join(defense)}")
    if rebounding:
        lines.append(f"- Rebounding: {', '.join(rebounding)}")
    if efficiency:
        lines.append(f"- Efficiency: {', '.join(efficiency)}")
    if recent_form:
        lines.append(f"- Recent form: {', '.join(recent_form)}")

    return "\n".join(lines)


def build_scouting_packet(team_name: str, coach_notes: str = "") -> str:
    context = build_scouting_context(team_name)

    team_style = context.get("team_style", {})
    team_recent = context.get("team_recent_form", {})
    team_ml = context.get("team_ml_profile", {})

    players = context.get("players", [])

    # Keep packet focused for the LLM.
    key_players = players[:8]

    lines = []

    lines.append(f"SCOUTING PACKET: {context.get('team_name')}")
    lines.append(f"Season: {context.get('season')}")
    lines.append("")

    if coach_notes:
        lines.append("COACH NOTES")
        lines.append(coach_notes)
        lines.append("")

    lines.append("TEAM IDENTITY")
    lines.append(f"- ML team type: {team_ml.get('team_ml_archetype', 'N/A')}")
    if team_ml.get("team_archetype_explanation"):
        lines.append(f"- {team_ml.get('team_archetype_explanation')}")
    lines.append("")
    lines.append("Offensive identity:")
    lines.append(format_list(team_style.get("offensive_identity", [])))
    lines.append("")
    lines.append("Defensive identity:")
    lines.append(format_list(team_style.get("defensive_identity", [])))
    lines.append("")

    lines.append("TEAM STRENGTHS")
    lines.append(format_list(team_style.get("strengths", [])))
    lines.append("")

    lines.append("AREAS TO ATTACK")
    lines.append(format_list(team_style.get("areas_to_attack", [])))
    lines.append("")

    lines.append("RECENT FORM")
    lines.append(format_list(team_recent.get("recent_identity", [])))
    lines.append("")
    lines.append("Recent strengths:")
    lines.append(format_list(team_recent.get("recent_strengths", [])))
    lines.append("")
    lines.append("Recent areas to attack:")
    lines.append(format_list(team_recent.get("recent_areas_to_attack", [])))
    lines.append("")

    lines.append("KEY PLAYERS")
    for player in key_players:
        lines.append("")
        lines.append(format_player(player))

    return "\n".join(lines)


if __name__ == "__main__":
    packet = build_scouting_packet(
        "Claremont_Mudd_Scripps",
        coach_notes="Team has been experimenting with more zone and shorter rotations.",
    )
    print(packet)