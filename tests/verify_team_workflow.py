from src.storage.team_repository import get_team_data


def verify(team_name: str):
    print("\n" + "=" * 60)
    print(f"VERIFYING: {team_name}")
    print("=" * 60)

    team_data = get_team_data(team_name)

    required_keys = [
        "team_stats",
        "team_name",
        "stats_url",
        "player_stats",
        "recent_team_trends",
        "recent_player_impact",
        "advanced_team_metrics",
        "advanced_player_metrics",
    ]

    for key in required_keys:
        print(f"{'✅' if key in team_data else '❌'} {key}")

    print("Players:", len(team_data.get("player_stats", [])))
    print("Recent impact players:", len(team_data.get("recent_player_impact", [])))
    print("Advanced player metrics:", len(team_data.get("advanced_player_metrics", {})))
    print("Stats URL:", team_data.get("stats_url"))


if __name__ == "__main__":
    verify("George Fox")  # cached team
    verify("NYU")         # non-cached team