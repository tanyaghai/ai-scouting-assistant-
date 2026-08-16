from src.config import OUR_TEAM
from src.pipelines.matchup_builder import build_matchup, display_name
from src.pipelines.player_note_generator import generate_player_note
from src.pipelines.scouting_context_builder import build_scouting_context

# How many opponents to detail. Beyond this we're describing players who
# barely see the floor.
KEY_PLAYER_COUNT = 10

# Ours only need enough detail to justify the assignments.
OUR_PLAYER_COUNT = 8


def format_list(items):
    if not items:
        return "- None listed"
    return "\n".join([f"- {item}" for item in items])


def _pct(value):
    """Stats arrive as either 0.412 or 41.2 depending on the source table."""
    if value in (None, ""):
        return None
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return f"{value * 100:.1f}%" if value <= 1 else f"{value:.1f}%"


def format_player(player: dict, team: str, detailed: bool = True) -> str:
    role = player.get("rule_based_profile", {})
    recent = player.get("recent_form", {})
    ml = player.get("ml_profile", {})
    stats = role.get("stats", {})

    # Team is stamped on every single player block, not just the section
    # header. A small model reading a long packet otherwise loses track of
    # which roster it is in and attributes our players to the opponent.
    lines = [f"{display_name(player['name'])}  [{team}]"]
    lines.append(f"- Team: {team}")
    lines.append(f"- Role: {role.get('primary_role', 'N/A')}")
    lines.append(
        f"- Line: {stats.get('ppg')} PPG, {stats.get('rpg')} RPG, "
        f"{stats.get('apg')} APG, {stats.get('spg')} SPG, "
        f"{stats.get('bpg')} BPG in {stats.get('mpg')} MPG"
    )

    if detailed:
        # Raw efficiency numbers, not just the labels derived from them --
        # the model writes far more specifically when it can cite figures.
        shooting = []
        if _pct(stats.get("ts_pct")):
            shooting.append(f"{_pct(stats.get('ts_pct'))} TS")
        if _pct(stats.get("three_pct")):
            shooting.append(f"{_pct(stats.get('three_pct'))} 3PT")
        if stats.get("usage_rate"):
            shooting.append(f"{_pct(stats.get('usage_rate'))} usage")
        if stats.get("assist_to_turnover"):
            shooting.append(f"{float(stats['assist_to_turnover']):.2f} A/TO")
        if shooting:
            lines.append(f"- Efficiency: {', '.join(shooting)}")

    if ml.get("ml_archetype"):
        lines.append(f"- ML type: {ml.get('ml_archetype')}")

    for key, label in [
        ("offensive_profile", "Offense"),
        ("playmaking_profile", "Playmaking"),
        ("defensive_profile", "Defense"),
        ("rebounding_profile", "Rebounding"),
        ("efficiency_profile", "Efficiency"),
    ]:
        values = role.get(key, [])
        if values:
            lines.append(f"- {label}: {', '.join(values)}")

    if recent.get("recent_form"):
        lines.append(f"- Recent form: {', '.join(recent['recent_form'])}")

    if detailed:
        try:
            note = generate_player_note(player)
            if note:
                lines.append(f"- Personnel note: {note}")
        except Exception as error:
            # Swallowed on purpose -- one failed note shouldn't sink the
            # packet -- but say so rather than dropping it silently.
            lines.append(f"- Personnel note unavailable ({type(error).__name__})")

    return "\n".join(lines)


def format_comparison(rows: list) -> str:
    if not rows:
        return "- Not available"

    lines = []
    for row in rows:
        ours, theirs = row["ours"], row["theirs"]
        if 0 < ours <= 1 and 0 < theirs <= 1:
            ours, theirs = f"{ours * 100:.1f}%", f"{theirs * 100:.1f}%"
        lines.append(f"- {row['label']}: us {ours} / them {theirs} (edge: {row['edge']})")

    return "\n".join(lines)


def format_assignments(assignments: list, our_team: str, opponent: str) -> str:
    if not assignments:
        return "- No assignments generated (our roster may not be cached yet)"

    blocks = []
    for item in assignments:
        # Direction is spelled out on both sides. "X guards Y" alone gets
        # reversed; naming the team on each half does not.
        blocks.append(
            f"OUR DEFENDER: {item['defender']} [{our_team}] ({item['defender_note']})\n"
            f"  GUARDS THEIR PLAYER: {item['assignment']} [{opponent}] "
            f"({item['assignment_note']})\n"
            f"  Why: {item['reason']}\n"
            f"  Emphasis: {item['emphasis']}"
        )

    return "\n\n".join(blocks)


def build_scouting_packet(
    team_name: str,
    coach_notes: str = "",
    our_team: str = OUR_TEAM,
    matchup: dict = None,
) -> str:
    if matchup is None:
        matchup = build_matchup(team_name, our_team=our_team)

    context = matchup.get("their_context") or build_scouting_context(team_name)

    team_style = context.get("team_style", {})
    team_recent = context.get("team_recent_form", {})
    team_ml = context.get("team_ml_profile", {})
    players = context.get("players", [])

    lines = []

    lines.append(f"SCOUTING PACKET: {matchup['our_team']} vs {context.get('team_name')}")
    lines.append(f"Season: {context.get('season')}")
    lines.append("")

    if coach_notes:
        lines.append("COACH NOTES")
        lines.append(coach_notes)
        lines.append("")

    lines.append("=== OPPONENT: " + str(context.get("team_name")) + " ===")
    lines.append("")

    lines.append("TEAM IDENTITY")
    if team_ml.get("team_ml_archetype"):
        lines.append(f"- ML team type: {team_ml.get('team_ml_archetype')}")
    if team_ml.get("team_archetype_explanation"):
        lines.append(f"- {team_ml.get('team_archetype_explanation')}")
    lines.append("")
    lines.append("Offensive identity:")
    lines.append(format_list(team_style.get("offensive_identity", [])))
    lines.append("")
    lines.append("Defensive identity:")
    lines.append(format_list(team_style.get("defensive_identity", [])))
    lines.append("")

    lines.append("THEIR STRENGTHS")
    lines.append(format_list(team_style.get("strengths", [])))
    lines.append("")

    lines.append("AREAS TO ATTACK")
    lines.append(format_list(team_style.get("areas_to_attack", [])))
    lines.append("")

    lines.append("THEIR RECENT FORM")
    lines.append(format_list(team_recent.get("recent_identity", [])))
    lines.append("")
    lines.append("Recent strengths:")
    lines.append(format_list(team_recent.get("recent_strengths", [])))
    lines.append("")
    lines.append("Recent areas to attack:")
    lines.append(format_list(team_recent.get("recent_areas_to_attack", [])))
    lines.append("")

    opponent_name = str(context.get("team_name"))

    lines.append(f"THEIR KEY PLAYERS -- these all play for {opponent_name} (the OPPONENT)")
    for player in players[:KEY_PLAYER_COUNT]:
        lines.append("")
        lines.append(format_player(player, opponent_name, detailed=True))
    lines.append("")

    if matchup["available"]:
        lines.append("=== US: " + str(matchup["our_team"]) + " ===")
        lines.append("")

        lines.append("HEAD-TO-HEAD NUMBERS")
        lines.append(format_comparison(matchup["comparison"]))
        lines.append("")

        lines.append(
            f"OUR PERSONNEL -- these all play for {matchup['our_team']} (US). "
            "They are NOT on the opponent's roster."
        )
        for player in matchup["our_players"][:OUR_PLAYER_COUNT]:
            lines.append("")
            lines.append(format_player(player, matchup["our_team"], detailed=False))
        lines.append("")

        lines.append("SUGGESTED DEFENSIVE ASSIGNMENTS")
        lines.append("(computed from both rosters -- present these as recommendations,")
        lines.append(" and do not invent assignments beyond this list)")
        lines.append("")
        lines.append(format_assignments(
            matchup["assignments"], matchup["our_team"], opponent_name
        ))
    else:
        lines.append("=== US ===")
        lines.append(f"Our roster ({matchup['our_team']}) is not cached, so no")
        lines.append("matchup analysis is available. Say so rather than guessing.")

    return "\n".join(lines)


if __name__ == "__main__":
    print(build_scouting_packet(
        "Chapman",
        coach_notes="They have been playing more zone and shortening the rotation.",
    ))
