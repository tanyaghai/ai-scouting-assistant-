from datetime import datetime, timezone, timedelta

from src.storage.cache_manager import load_team_data


def parse_last_updated(team_data: dict):
    last_updated = team_data.get("last_updated")

    if not last_updated:
        return None

    return datetime.fromisoformat(last_updated)


def should_refresh_team(team_name: str, max_age_hours: int = 24) -> bool:
    try:
        team_data = load_team_data(team_name)
    except FileNotFoundError:
        return True

    last_updated = parse_last_updated(team_data)

    if last_updated is None:
        return True

    age = datetime.now(timezone.utc) - last_updated

    return age > timedelta(hours=max_age_hours)


if __name__ == "__main__":
    print("Redlands refresh needed?")
    print(should_refresh_team("Redlands"))