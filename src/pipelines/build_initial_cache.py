from src.data_collection.sidearm_collector import SCIAC_TEAM_STATS_URLS
from src.pipelines.ingest_opponent import ingest_opponent


def build_initial_cache():
    for team_name, stats_url in SCIAC_TEAM_STATS_URLS.items():
        print(f"\nBuilding cache for {team_name}")
        ingest_opponent(team_name, stats_url=stats_url)


if __name__ == "__main__":
    build_initial_cache()