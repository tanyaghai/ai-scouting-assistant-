from src.data_collection.opponent_finder import find_opponent_stats_url
from src.data_collection.sidearm_collector import get_full_roster_stats, get_team_stats_from_sidearm
from src.data_collection.recent_games_collector import summarize_last_five_team_trends
from src.data_collection.season_detector import detect_season_from_stats_page
from src.models.recent_player_impact import get_recent_player_impact
from src.models.scouting_metrics import build_scouting_metrics
from src.storage.cache_manager import (
    load_team_data,
    save_current_team_data,
    save_archived_team_data,
)
from src.storage.season_lifecycle import should_save_as_current


def ingest_opponent(team_name: str, stats_url: str = None):
    if stats_url is None:
        print(f"Finding stats URL for {team_name}...")
        stats_url = find_opponent_stats_url(team_name)

        if not stats_url:
            raise ValueError(f"Could not find stats URL for {team_name}")
    else:
        print(f"Using cached stats URL for {team_name}: {stats_url}")

    print(f"Found stats URL: {stats_url}")

    detected_season = detect_season_from_stats_page(stats_url)
    print(f"Detected season: {detected_season}")

    players = get_full_roster_stats(stats_url)

    team_data = {
        "team_name": team_name,
        "stats_url": stats_url,
        "season": detected_season,
        "team_stats": get_team_stats_from_sidearm(stats_url),
        "player_stats": players,
        "recent_team_trends": summarize_last_five_team_trends(stats_url),
    }

    recent_df = get_recent_player_impact(team_name, stats_url, roster_players=players)
    team_data["recent_player_impact"] = recent_df.round(2).to_dict(orient="records")

    if detected_season and should_save_as_current(detected_season):
        save_current_team_data(team_name, team_data)
        team_data = load_team_data(team_name)

        metrics = build_scouting_metrics(team_name)
        team_data["advanced_team_metrics"] = metrics["team_metrics"]
        team_data["advanced_player_metrics"] = metrics["player_metrics"]

        save_current_team_data(team_name, team_data)
        print(f"Saved {team_name} as current season.")

    elif detected_season:
        save_archived_team_data(team_name, team_data, detected_season)
        team_data = load_team_data(team_name, season=detected_season)

        metrics = build_scouting_metrics(team_name, season=detected_season)
        team_data["advanced_team_metrics"] = metrics["team_metrics"]
        team_data["advanced_player_metrics"] = metrics["player_metrics"]

        save_archived_team_data(team_name, team_data, detected_season)
        print(f"Saved {team_name} as archived season {detected_season}.")

    else:
        save_current_team_data(team_name, team_data)
        print(f"Saved {team_name} as current because season could not be detected.")

    print(f"Finished ingesting {team_name}")


if __name__ == "__main__":
    ingest_opponent("George Fox")