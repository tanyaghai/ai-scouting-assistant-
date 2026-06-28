import pandas as pd

from src.storage.cache_manager import TEAM_CACHE_DIR, load_team_data


def safe_div(num, den):
    if not den:
        return 0
    return num / den


def get_cached_team_names():
    team_dirs = [
        path for path in TEAM_CACHE_DIR.iterdir()
        if path.is_dir() and (path / "current.json").exists()
    ]
    return [path.name for path in team_dirs]


def build_player_feature_table() -> pd.DataFrame:
    rows = []

    for team_name in get_cached_team_names():
        team_data = load_team_data(team_name)
        players = team_data.get("player_stats", [])
        advanced_players = team_data.get("advanced_player_metrics", {})

        for player in players:
            name = player.get("name")
            games = player.get("games") or 0
            advanced = advanced_players.get(name, {})

            row = {
                "team": team_data.get("team_name"),
                "player": name,
                "season": team_data.get("season"),
                "games": games,
                "ppg": player.get("ppg") or 0,
                "rpg": player.get("rpg") or 0,
                "apg": safe_div(player.get("assists") or 0, games),
                "spg": safe_div(player.get("steals") or 0, games),
                "bpg": safe_div(player.get("blocks") or 0, games),
                "mpg": player.get("minutes_per_game") or 0,
                "fg_pct": player.get("fg_pct") or 0,
                "three_pct": player.get("three_pct") or 0,
                "ft_pct": player.get("ft_pct") or 0,
                "usage_rate": advanced.get("usage_rate") or 0,
                "ts_pct": advanced.get("ts_pct") or 0,
                "efg_pct": advanced.get("efg_pct") or 0,
                "three_point_rate": advanced.get("three_point_rate") or 0,
                "free_throw_rate": advanced.get("free_throw_rate") or 0,
                "assist_to_turnover": advanced.get("assist_to_turnover") or 0,
            }

            rows.append(row)

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    # Keep one row per player/team/season.
    df = (
        df.sort_values(["team", "season", "player", "mpg"], ascending=[True, True, True, False])
        .drop_duplicates(subset=["team", "season", "player"], keep="first")
        .reset_index(drop=True)
    )

    df["eligible_for_ml"] = (df["mpg"] >= 12) & (df["games"] >= 10)

    return df


if __name__ == "__main__":
    df = build_player_feature_table()

    print(df.head())
    print()
    print(f"Players in feature table: {len(df)}")
    print(f"Eligible for ML: {df['eligible_for_ml'].sum()}")
    print(f"Columns: {list(df.columns)}")