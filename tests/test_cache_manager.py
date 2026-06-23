from src.storage.cache_manager import save_team_data, load_team_data, team_exists

sample_data = {
    "team_stats": {
        "ppg": 72.5,
        "opp_ppg": 61.2
    },
    "player_stats": [
        {"name": "Player A", "ppg": 14.2}
    ]
}

save_team_data("Redlands", sample_data)

print(team_exists("Redlands"))
print(load_team_data("Redlands"))