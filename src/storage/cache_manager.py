import json
from pathlib import Path
from datetime import datetime, timezone

TEAM_CACHE_DIR = Path("data/teams")
TEAM_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def normalize_team_name(team_name: str) -> str:
    return (
        team_name.lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace(".", "")
        .replace("'", "")
    )


def get_team_cache_path(team_name: str) -> Path:
    filename = normalize_team_name(team_name) + ".json"
    return TEAM_CACHE_DIR / filename


def team_exists(team_name: str) -> bool:
    return get_team_cache_path(team_name).exists()


def save_team_data(team_name: str, data: dict) -> None:
    path = get_team_cache_path(team_name)

    data["team_name"] = team_name
    data["last_updated"] = datetime.now(timezone.utc).isoformat()

    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_team_data(team_name: str) -> dict:
    path = get_team_cache_path(team_name)

    if not path.exists():
        raise FileNotFoundError(f"No cached data found for {team_name}")

    with open(path, "r") as f:
        return json.load(f)