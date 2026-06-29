from src.llm.ollama_client import ask_qwen


def format_list(items):
    if not items:
        return "None"
    return ", ".join(items)


def build_player_evidence(player: dict) -> str:
    role = player.get("rule_based_profile", {})
    recent = player.get("recent_form", {})
    ml = player.get("ml_profile", {})
    stats = role.get("stats", {})

    return f"""
PLAYER: {player.get("name")}

ROLE:
- {role.get("primary_role")}

STATS:
- {stats.get("ppg")} PPG
- {stats.get("rpg")} RPG
- {stats.get("apg")} APG
- {stats.get("spg")} SPG
- {stats.get("bpg")} BPG
- {stats.get("mpg")} MPG
- 3PT%: {stats.get("three_pct")}
- Usage: {stats.get("usage_rate")}

OFFENSIVE PROFILE:
- {format_list(role.get("offensive_profile", []))}

PLAYMAKING PROFILE:
- {format_list(role.get("playmaking_profile", []))}

DEFENSIVE PROFILE:
- {format_list(role.get("defensive_profile", []))}

REBOUNDING PROFILE:
- {format_list(role.get("rebounding_profile", []))}

EFFICIENCY PROFILE:
- {format_list(role.get("efficiency_profile", []))}

RECENT FORM:
- {format_list(recent.get("recent_form", []))}

ATTACK SUGGESTION:
- {build_attack_suggestion(player)}

ML ARCHETYPE:
- {ml.get("ml_archetype", "N/A")}
- {ml.get("archetype_fit", "N/A")}
""".strip()


def generate_player_note(player: dict) -> str:
    evidence = build_player_evidence(player)

    prompt = f"""
    You are writing a personnel note for a college basketball scouting report.

    Use ONLY the evidence below.
    Do NOT infer anything that is not explicitly listed.
    Do NOT mention:
    - position
    - starter
    - bench
    - core player
    - league
    - transition
    - offensive glass
    - post play
    - handedness
    - injuries
    - schemes
    - personality traits
    - inside/out scoring
    unless those exact ideas appear in the evidence.

    Write exactly 2 short sentences as one personnel note.
    Do not label the sentences as Sentence 1 or Sentence 2.
    Sentence 1: summarize the player's role, main strengths, and statistical profile.
    Sentence 2: use the ATTACK SUGGESTION exactly as the basis for how to guard or attack this player.

    If no clear weakness exists, say what must be limited instead.

    EVIDENCE:
    {evidence}

    PERSONNEL NOTE:
    """.strip()
    return ask_qwen(prompt).strip()

def build_attack_suggestion(player: dict) -> str:
    role = player.get("rule_based_profile", {})
    stats = role.get("stats", {})
    offensive = role.get("offensive_profile", [])
    playmaking = role.get("playmaking_profile", [])
    efficiency = role.get("efficiency_profile", [])

    three_pct = stats.get("three_pct") or 0
    apg = stats.get("apg") or 0
    usage = stats.get("usage_rate") or 0

    if "Low-efficiency scorer" in efficiency:
        return "Make her take contested shots and avoid giving up clean rhythm looks."

    if "Below-average efficiency" in efficiency:
        return "Force contested finishes and make her score efficiently over pressure."

    if "3PT-heavy shot profile" in offensive and three_pct < 0.30:
        return "Run her off easy rhythm threes, but make her prove she can finish efficiently inside the arc."

    if "Three-point threat" in offensive and three_pct >= 0.32:
        return "Do not lose her on the perimeter; close out under control and limit catch-and-shoot rhythm."

    if "Gets to the line" in offensive:
        return "Defend without fouling and make her finish contested shots."

    if usage >= 0.24:
        return "Make her touches difficult and force her into lower-efficiency decisions."

    if "Creator / ball handler" in playmaking or apg >= 2.5:
        return "Pressure her decision-making and make her work to initiate offense."

    return "Make her earn touches and avoid giving up easy rhythm opportunities."


if __name__ == "__main__":
    from src.pipelines.scouting_context_builder import build_scouting_context

    context = build_scouting_context("Claremont_Mudd_Scripps")

    for player in context["players"][:5]:
        print("=" * 60)
        print(player["name"])
        print(generate_player_note(player))