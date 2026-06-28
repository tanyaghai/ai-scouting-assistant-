import json
import math
from pathlib import Path
from datetime import datetime, timezone

TEAM_CACHE_DIR = Path("data/teams")
TEAM_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def clean_for_json(value):
    if isinstance(value, dict):
        return {k: clean_for_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean_for_json(v) for v in value]
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def normalize_team_name(team_name: str) -> str:
    return (
        team_name.lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace(".", "")
        .replace("'", "")
    )


def get_team_cache_dir(team_name: str) -> Path:
    path = TEAM_CACHE_DIR / normalize_team_name(team_name)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_current_team_cache_path(team_name: str) -> Path:
    return get_team_cache_dir(team_name) / "current.json"


def get_archived_team_cache_path(team_name: str, season: str) -> Path:
    return get_team_cache_dir(team_name) / f"{season}.json"


def cleanup_old_archives(team_name: str, keep_season: str) -> None:
    team_dir = get_team_cache_dir(team_name)

    for path in team_dir.glob("*.json"):
        if path.name == "current.json":
            continue
        if path.name == f"{keep_season}.json":
            continue
        path.unlink()


def team_exists(team_name: str, season: str = None) -> bool:
    if season:
        return get_archived_team_cache_path(team_name, season).exists()
    return get_current_team_cache_path(team_name).exists()


def save_current_team_data(team_name: str, data: dict) -> None:
    data["team_name"] = team_name
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    data = clean_for_json(data)

    with open(get_current_team_cache_path(team_name), "w") as f:
        json.dump(data, f, indent=2)


def save_archived_team_data(team_name: str, data: dict, season: str) -> None:
    data["team_name"] = team_name
    data["season"] = season
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    data = clean_for_json(data)

    with open(get_archived_team_cache_path(team_name, season), "w") as f:
        json.dump(data, f, indent=2)

    cleanup_old_archives(team_name, season)


def load_team_data(team_name: str, season: str = None) -> dict:
    path = (
        get_archived_team_cache_path(team_name, season)
        if season
        else get_current_team_cache_path(team_name)
    )

    if not path.exists():
        raise FileNotFoundError(f"No cached data found for {team_name}")

    with open(path, "r") as f:
        return json.load(f)