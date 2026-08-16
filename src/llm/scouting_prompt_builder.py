"""
Prompt construction for the scouting assistant.

The whitelist is the important part. A scout that invents a player number
or a stat is worse than no scout, because a coach may act on it in a game.
Every name the model is allowed to say is listed explicitly, and it is
told to check its answer against that list before responding.
"""

import json

from src.config import OUR_TEAM


SYSTEM_PROMPT = """
You are a basketball scouting assistant for the {our_team} coaching staff.

You are writing for OUR staff about an opponent. Frame everything as
us-versus-them: what they do, and what WE do about it.

Hard rules:
- Use ONLY the scouting packet below. Every number and every name comes from it.
- Do NOT invent players, statistics, injuries, schemes, jersey numbers, or history.
- Mention ONLY players listed in the ROSTERS section.
- NEVER attribute a player to the wrong team. Our players are ours; their
  players are theirs. Before writing any player's name, check the ROSTERS
  section for which team they play for. Getting this wrong makes the
  entire scout useless to a coach.
- Defensive assignments run one way: OUR player guards THEIR player.
  Never the reverse.
- If something is not in the packet, say it is not available rather than guessing.
- Coach notes are HIGH PRIORITY and override the structured data when they conflict.
- Present SUGGESTED DEFENSIVE ASSIGNMENTS as recommendations. Do not invent
  assignments that are not in that section.
- ML archetypes are supporting language only. Do not overstate them.

Style:
- Write like a coach talking to coaches. Direct, concrete, no filler.
- Cite specific numbers when they support a point.
- Prefer "deny the middle drive" over "play good defense".
- Never pad. If a section is thin, keep it short.
""".strip()


REPORT_STRUCTURE = """
Unless the request asks for something else, structure a full scout as:

1. THEIR IDENTITY -- two or three sentences on how they play.
2. PERSONNEL -- their key players, with what each one does and how to
   handle them. Cite real numbers.
3. DEFENSIVE ASSIGNMENTS -- who guards who, drawn from the suggested
   assignments, with the emphasis for each.
4. KEYS TO THE GAME -- three or four, written from OUR perspective as
   things we must do. Draw these from AREAS TO ATTACK and their recent
   weaknesses, not from their strengths.
5. WHAT WORRIES ME -- one honest paragraph on how this team could beat us.
""".strip()


def _names_for(players: list) -> list:
    """
    Both spellings of every name.

    Roster tables publish "Ghai, Tanya" but the packet renders "Tanya Ghai",
    so the whitelist has to accept either -- otherwise the model reads its
    own correct output as a violation and drops real players.
    """
    from src.pipelines.matchup_builder import display_name

    names = set()
    for player in players or []:
        name = player.get("name")
        if name:
            names.add(display_name(name))

    return sorted(names)


def collect_allowed_names(
    opponent_players: list,
    our_players: list = None,
    opponent_team: str = "the opponent",
    our_team: str = OUR_TEAM,
) -> dict:
    """
    Names grouped BY TEAM, not as one flat list.

    A flat whitelist answers "may I say this name?" but not "whose player
    is this?", which is how our own players end up described as the
    opponent's. Grouping is the whole point.
    """
    return {
        "our_team": our_team,
        "opponent_team": opponent_team,
        "ours": _names_for(our_players),
        "theirs": _names_for(opponent_players),
    }


def _format_rosters(allowed: dict, our_team: str) -> str:
    """
    Two explicitly labelled lists. Every name is stated alongside the team
    it belongs to, so "whose player is this" is answerable without
    inference.
    """
    our_team = allowed.get("our_team") or our_team
    opponent_team = allowed.get("opponent_team") or "the opponent"

    ours = "\n".join(f"  - {name}" for name in allowed.get("ours", [])) or "  (none cached)"
    theirs = "\n".join(f"  - {name}" for name in allowed.get("theirs", [])) or "  (none)"

    return (
        "========================\n"
        "ROSTERS -- WHO PLAYS FOR WHOM\n"
        "========================\n"
        f"OUR PLAYERS ({our_team}) -- these play for US:\n"
        f"{ours}\n\n"
        f"THEIR PLAYERS ({opponent_team}) -- these play for the OPPONENT:\n"
        f"{theirs}\n\n"
        "These are the only names you may use. A name in the first list is\n"
        f"one of OUR players and must never be described as playing for\n"
        f"{opponent_team}. A name in the second list is one of THEIRS and\n"
        f"must never be described as playing for {our_team}."
    )


def build_scouting_prompt(
    packet: str,
    allowed_players: dict,
    user_request: str,
    coach_notes: str = "",
    style_text: str = "",
    our_team: str = OUR_TEAM,
) -> str:
    sections = [SYSTEM_PROMPT.format(our_team=our_team)]

    if style_text:
        sections.append(
            "========================\n"
            "STYLE EXAMPLES FROM PRIOR SCOUTS\n"
            "========================\n"
            f"{style_text}\n\n"
            "Use these ONLY for tone, formatting, section names, and short\n"
            "motivational language. Do NOT take any basketball content from\n"
            "them -- no tendencies, no personnel, no keys. All basketball\n"
            "content must come from the scouting packet or coach notes."
        )

    sections.append(_format_rosters(allowed_players, our_team))

    sections.append(
        "========================\n"
        "COACH NOTES\n"
        "========================\n"
        f"{coach_notes if coach_notes else 'None provided'}"
    )

    sections.append(
        "========================\n"
        "SCOUTING PACKET\n"
        "========================\n"
        f"{packet}"
    )

    sections.append(
        "========================\n"
        "REPORT STRUCTURE\n"
        "========================\n"
        f"{REPORT_STRUCTURE}"
    )

    sections.append(
        "========================\n"
        "REQUEST\n"
        "========================\n"
        f"{user_request}\n\n"
        "Before answering, re-read every player name you used and confirm\n"
        "against the ROSTERS section that you put them on the correct team.\n"
        "Remove any name that does not appear there at all."
    )

    return "\n\n".join(sections)
