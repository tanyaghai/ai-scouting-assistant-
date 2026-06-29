from src.pipelines.scouting_packet_builder import build_scouting_packet
from src.llm.ollama_client import ask_qwen
from src.rag.scout_style_loader import load_style_examples

def ask_scouting_assistant(
    team_name: str,
    user_request: str,
    coach_notes: str = "",
) -> str:
    packet = build_scouting_packet(team_name, coach_notes)

    style_examples = load_style_examples(max_reports=2)

    style_text = "\n\n".join(
        [
            f"STYLE EXAMPLE: {example['filename']}\n{example['text']}"
            for example in style_examples
        ]
    )

    prompt = f"""
    You are a basketball scouting assistant.

    Use ONLY the scouting packet below. Do not invent player names, stats, injuries, or schemes.

    Coach notes are HIGH PRIORITY. If coach notes are provided, explicitly incorporate them into the response.

    STYLE EXAMPLES FROM PRIOR SCOUTS:
    {style_text}

    Use these examples ONLY for formatting, tone, section names, and short motivational language.
    Do NOT use any basketball strategy, opponent tendencies, player details, or keys from the style examples.
    All basketball content must come from the current scouting packet or coach notes.

    SCOUTING PACKET:
    {packet}

    USER REQUEST:
    {user_request}

    Write in concise, actionable coaching language.
    """.strip()

    return ask_qwen(prompt)


if __name__ == "__main__":
    response = ask_scouting_assistant(
        team_name="Claremont_Mudd_Scripps",
        coach_notes="Team has been experimenting with more zone and shorter rotations.",
        user_request=(
            "Give me a concise scouting report with team identity, top 3 key players, "
            "and three defensive keys. Defensive keys must be written from OUR perspective "
            "and must come only from Areas to Attack and Recent Areas to Attack. "
            "Do not use the opponent's strengths as our keys unless explaining what we must neutralize."
        )
    )

    print(response)