import pandas as pd

from src.storage.cache_manager import list_cached_team_names, load_team_data


def get_cached_team_names():
    return list_cached_team_names()


def build_team_feature_table() -> pd.DataFrame:
    rows = []

    for team_name in get_cached_team_names():
        team_data = load_team_data(team_name)
        stats = team_data.get("team_stats", {})

        if not stats:
            continue

        rows.append({
            "team": team_data.get("team_name"),
            "season": team_data.get("season"),

            "ppg": stats.get("ppg") or 0,
            "fg_pct": stats.get("fg_pct") or 0,
            "three_pct": stats.get("three_pct") or 0,
            "rebounds_per_game": stats.get("rebounds_per_game") or 0,
            "assists_per_game": stats.get("assists_per_game") or 0,
            "turnovers_per_game": stats.get("turnovers_per_game") or 0,
            "blocks_per_game": stats.get("blocks_per_game") or 0,
            "steals_per_game": stats.get("steals_per_game") or 0,
        })

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = build_team_feature_table()
    print(df)
    print(f"\nTeams in feature table: {len(df)}")