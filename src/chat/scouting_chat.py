from src.config import OUR_TEAM
from src.llm.ollama_client import ask_qwen
from src.llm.scouting_prompt_builder import build_scouting_prompt, collect_allowed_names
from src.pipelines.matchup_builder import build_matchup
from src.pipelines.scouting_packet_builder import build_scouting_packet
from src.rag.scout_style_loader import load_style_examples


def ask_scouting_assistant(
    team_name: str,
    user_request: str,
    coach_notes: str = "",
    our_team: str = OUR_TEAM,
) -> str:
    # Built once and threaded through: assembling a context runs classifier
    # passes over a whole roster, so rebuilding it per consumer is costly.
    matchup = build_matchup(team_name, our_team=our_team)

    packet = build_scouting_packet(
        team_name, coach_notes, our_team=our_team, matchup=matchup
    )

    # Names are whitelisted across BOTH rosters, so the model can name our
    # own players in defensive assignments without being free to invent any.
    opponent_players = matchup.get("their_context", {}).get("players", [])
    allowed_players = collect_allowed_names(
        opponent_players,
        matchup.get("our_players"),
        opponent_team=matchup.get("opponent", team_name),
        our_team=matchup.get("our_team", our_team),
    )

    style_examples = load_style_examples(max_reports=2)
    style_text = "\n\n".join(
        f"STYLE EXAMPLE: {example['filename']}\n{example['text']}"
        for example in style_examples
    )

    prompt = build_scouting_prompt(
        packet=packet,
        allowed_players=allowed_players,
        user_request=user_request,
        coach_notes=coach_notes,
        style_text=style_text,
        our_team=our_team,
    )

    return ask_qwen(prompt)


if __name__ == "__main__":
    print(ask_scouting_assistant(
        team_name="Chapman",
        coach_notes="They have been playing more zone and shortening the rotation.",
        user_request="Give me a full scout for this week.",
    ))
