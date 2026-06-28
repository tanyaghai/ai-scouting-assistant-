from src.storage.cache_manager import team_exists, load_team_data
from src.storage.cache_refresh import should_refresh_team
from src.pipelines.ingest_opponent import ingest_opponent


def get_team_data(team_name: str, refresh_if_stale: bool = True):
    if team_exists(team_name):
        team_data = load_team_data(team_name)

        if refresh_if_stale and should_refresh_team(team_name):
            print(f"{team_name} cache is stale. Refreshing...")
            cached_url = team_data.get("stats_url") or team_data.get("player_stats_source_url")
            ingest_opponent(team_name, stats_url=cached_url)

        print(f"Loading {team_name} from cache.")
        return load_team_data(team_name)

    print(f"{team_name} not found in cache. Ingesting...")
    ingest_opponent(team_name)

    print(f"Loading {team_name} from cache.")
    return load_team_data(team_name)


if __name__ == "__main__":
    team_data = get_team_data("George Fox")
    print(team_data["team_name"])
    print(team_data.get("stats_url"))