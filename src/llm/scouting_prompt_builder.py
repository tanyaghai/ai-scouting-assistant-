import json


SYSTEM_PROMPT = """
You are an AI basketball scouting assistant for a college coaching staff.

You MUST follow these rules:
- Use ONLY the provided scouting context.
- Do NOT invent player names, statistics, teams, injuries, schemes, or history.
- If something is not in the scouting context or coach notes, say that it is not available.
- The player names in the scouting context are the ONLY players you may mention.
- Coach notes override the structured context only when they clearly conflict.
- ML archetypes are supporting language only. Do not overstate them.
- Write concise, actionable basketball language.
"""


def build_scouting_prompt(
    context: dict,
    coach_notes: str,
    user_request: str,
) -> str:
    allowed_players = [player["name"] for player in context.get("players", [])]

    return f"""
{SYSTEM_PROMPT}

========================
ALLOWED PLAYER NAMES
========================
{json.dumps(allowed_players, indent=2)}

========================
COACH NOTES
========================
{coach_notes if coach_notes else "None"}

========================
SCOUTING CONTEXT
========================
{json.dumps(context, indent=2)}

========================
USER REQUEST
========================
{user_request}

Before answering, verify that every player name you mention appears in ALLOWED PLAYER NAMES.

Respond naturally as a basketball scouting assistant.
""".strip()