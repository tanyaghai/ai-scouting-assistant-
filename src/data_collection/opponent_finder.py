import os
from typing import Optional

import requests
from dotenv import load_dotenv

from src.data_collection.sidearm_collector import get_full_roster_stats

load_dotenv()

SERPER_URL = "https://google.serper.dev/search"


def search_web(query: str) -> list:
    api_key = os.getenv("SERPER_API_KEY")

    if not api_key:
        raise ValueError("Missing SERPER_API_KEY in .env")

    response = requests.post(
        SERPER_URL,
        headers={
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        },
        json={"q": query},
    )
    response.raise_for_status()

    return response.json().get("organic", [])


def is_valid_stats_url(url: str) -> bool:
    try:
        players = get_full_roster_stats(url)
        return len(players) > 0
    except Exception:
        return False


def find_opponent_stats_url(team_name: str) -> Optional[str]:
    query = f"{team_name} wbb stats"

    results = search_web(query)

    print(f"Search results for: {query}")

    for result in results:
        title = result.get("title", "")
        url = result.get("link", "")

        print(title)
        print(url)
        print()

        if "sports/womens-basketball/stats" not in url:
            continue

        if is_valid_stats_url(url):
            return url

    return None


if __name__ == "__main__":
    team_name = "George Fox"

    url = find_opponent_stats_url(team_name)

    print("Best stats URL:")
    print(url)