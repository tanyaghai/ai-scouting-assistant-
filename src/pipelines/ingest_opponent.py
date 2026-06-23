from src.data_collection.opponent_finder import find_opponent_stats_url
from src.data_collection.sidearm_collector import save_roster_to_cache
from src.data_collection.recent_games_collector import summarize_last_five_team_trends
from src.models.recent_player_impact import get_recent_player_impact
from src.storage.cache_manager import load_team_data, save_team_data


def ingest_opponent(team_name: str):
    print(f"Finding stats URL for {team_name}...")
    stats_url = find_opponent_stats_url(team_name)

    if not stats_url:
        raise ValueError(f"Could not find stats URL for {team_name}")

    print(f"Found stats URL: {stats_url}")

    save_roster_to_cache(team_name, stats_url)

    team_data = load_team_data(team_name)

    team_data["stats_url"] = stats_url
    team_data["recent_team_trends"] = summarize_last_five_team_trends(stats_url)

    recent_df = get_recent_player_impact(team_name, stats_url)
    team_data["recent_player_impact"] = recent_df.round(2).to_dict(orient="records")

    save_team_data(team_name, team_data)

    print(f"Finished ingesting {team_name}")


if __name__ == "__main__":
    ingest_opponent("George Fox")