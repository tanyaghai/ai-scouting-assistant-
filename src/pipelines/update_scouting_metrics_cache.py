from src.models.scouting_metrics import build_scouting_metrics
from src.storage.cache_manager import load_team_data, save_team_data
from src.data_collection.sidearm_collector import SCIAC_TEAM_STATS_URLS


def update_scouting_metrics_for_team(team_name: str):
    team_data = load_team_data(team_name)
    metrics = build_scouting_metrics(team_name)

    team_data["advanced_team_metrics"] = metrics["team_metrics"]
    team_data["advanced_player_metrics"] = metrics["player_metrics"]

    save_team_data(team_name, team_data)

    print(f"Updated scouting metrics for {team_name}")


def update_all_sciac_scouting_metrics():
    for team_name in SCIAC_TEAM_STATS_URLS:
        update_scouting_metrics_for_team(team_name)


if __name__ == "__main__":
    update_all_sciac_scouting_metrics()