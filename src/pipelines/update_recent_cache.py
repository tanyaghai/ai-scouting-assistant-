from src.models.recent_player_impact import get_recent_player_impact
from src.storage.cache_manager import load_team_data, save_team_data
from src.data_collection.recent_games_collector import summarize_last_five_team_trends

TEAM_URLS = {
    "Redlands": "https://goredlands.com/sports/womens-basketball/stats",
    "Chapman": "https://athletics.chapman.edu/sports/womens-basketball/stats",
    "Pomona-Pitzer": "https://sagehens.com/sports/womens-basketball/stats",
    "California Lutheran": "https://clusports.com/sports/womens-basketball/stats",
    "Caltech": "https://gocaltech.com/sports/womens-basketball/stats",
    "La Verne": "https://leopardathletics.com/sports/womens-basketball/stats",
    "Whittier": "https://wcpoets.com/sports/womens-basketball/stats",
    "Occidental": "https://oxyathletics.com/sports/womens-basketball/stats",
    "Claremont-Mudd-Scripps": "https://cmsathletics.org/sports/womens-basketball/stats"
}

for team_name, url in TEAM_URLS.items():
    print(f"Updating {team_name}")

    team_data = load_team_data(team_name)

    recent_df = get_recent_player_impact(team_name, url)

    team_data["recent_player_impact"] = (
        recent_df.round(2).to_dict(orient="records")
    )
    
    team_data["recent_team_trends"] = summarize_last_five_team_trends(url)

    save_team_data(team_name, team_data)

print("Done.")