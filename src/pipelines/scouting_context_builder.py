import pandas as pd

from src.storage.team_repository import get_team_data
from src.models.player_role_classifier import classify_team_player_roles
from src.models.recent_player_form import classify_team_recent_player_form
from src.models.team_style_classifier import classify_team_style_by_name
from src.models.team_recent_form import classify_team_recent_form_by_name


PLAYER_ARCHETYPES_PATH = "data/model_outputs/player_archetypes.csv"
TEAM_ARCHETYPES_PATH = "data/model_outputs/team_archetypes.csv"


def normalize_name(name: str) -> str:
    name = str(name).strip()

    if "," in name:
        last, first = [part.strip() for part in name.split(",", 1)]
        name = f"{first} {last}"

    return name.lower().replace("-", " ").replace("_", " ").strip()


def normalize_team(name: str) -> str:
    return str(name).lower().replace("-", " ").replace("_", " ").strip()


def load_ml_archetypes() -> pd.DataFrame:
    try:
        return pd.read_csv(PLAYER_ARCHETYPES_PATH)
    except FileNotFoundError:
        return pd.DataFrame()


def get_player_ml_archetype(team_name: str, player_name: str, ml_df: pd.DataFrame) -> dict:
    if ml_df.empty:
        return {}

    df = ml_df.copy()
    df["team_norm"] = df["team"].apply(normalize_team)
    df["player_norm"] = df["player"].apply(normalize_name)

    matches = df[
        (df["team_norm"] == normalize_team(team_name)) &
        (df["player_norm"] == normalize_name(player_name))
    ]

    if matches.empty:
        return {}

    row = matches.iloc[0]

    return {
        "ml_archetype": row.get("ml_archetype"),
        "archetype_fit": row.get("archetype_fit_label"),
        "player_archetype_explanation": row.get("player_archetype_explanation"),
    }


def build_player_context(team_name: str) -> list[dict]:
    team_data = get_team_data(team_name)
    canonical_team_name = team_data.get("team_name", team_name)

    raw_players = team_data.get("player_stats", [])
    player_roles = classify_team_player_roles(team_name)
    recent_forms = classify_team_recent_player_form(team_name)
    ml_df = load_ml_archetypes()

    raw_by_name = {
        normalize_name(player["name"]): player
        for player in raw_players
    }

    recent_by_name = {
        normalize_name(player["name"]): player
        for player in recent_forms
    }

    players = []

    for player in player_roles:
        name = player["name"]
        normalized = normalize_name(name)

        players.append({
            "name": name,
            "raw_stats": raw_by_name.get(normalized, {}),
            "rule_based_profile": player,
            "recent_form": recent_by_name.get(normalized, {}),
            "ml_profile": get_player_ml_archetype(canonical_team_name, name, ml_df),
        })

    return players

def load_team_archetypes() -> pd.DataFrame:
    try:
        return pd.read_csv(TEAM_ARCHETYPES_PATH)
    except FileNotFoundError:
        return pd.DataFrame()


def get_team_ml_archetype(team_name: str, team_ml_df: pd.DataFrame) -> dict:
    if team_ml_df.empty:
        return {}

    df = team_ml_df.copy()
    df["team_norm"] = df["team"].apply(normalize_team)

    matches = df[df["team_norm"] == normalize_team(team_name)]

    if matches.empty:
        return {}

    row = matches.iloc[0]

    return {
        "team_ml_archetype": row.get("team_ml_archetype"),
        "team_archetype_explanation": row.get("team_archetype_explanation"),
        "team_archetype_cluster": int(row.get("team_archetype_cluster")),
    }


def build_scouting_context(team_name: str) -> dict:
    team_data = get_team_data(team_name)
    canonical_team_name = team_data.get("team_name", team_name)

    team_ml_df = load_team_archetypes()

    return {
        "team_name": canonical_team_name,
        "season": team_data.get("season"),
        "stats_url": team_data.get("stats_url"),
        "team_stats": team_data.get("team_stats", {}),
        "team_style": classify_team_style_by_name(team_name),
        "team_recent_form": classify_team_recent_form_by_name(team_name),
        "team_ml_profile": get_team_ml_archetype(canonical_team_name, team_ml_df),
        "players": build_player_context(team_name),
    }

if __name__ == "__main__":
    context = build_scouting_context("Claremont_Mudd_Scripps")

    print(context["team_name"])
    print(context["team_style"])
    print(context["team_recent_form"])
    print("\nTeam ML Profile:")
    print(context["team_ml_profile"])

    print("\nPlayers:")
    for player in context["players"][:5]:
        print(player)