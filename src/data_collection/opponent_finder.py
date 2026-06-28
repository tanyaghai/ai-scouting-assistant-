import os
from typing import Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from src.data_collection.sidearm_collector import get_full_roster_stats
from src.data_collection.season_detector import detect_season_from_stats_page
from src.storage.season_lifecycle import season_start_year


load_dotenv()

SERPER_URL = "https://google.serper.dev/search"


def normalize_text(value: str) -> str:
    return (
        str(value)
        .lower()
        .replace("-", " ")
        .replace(".", "")
        .replace("'", "")
        .strip()
    )


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


def page_mentions_team(url: str, team_name: str) -> bool:
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    page_text = soup.get_text(" ", strip=True)

    normalized_team = normalize_text(team_name)
    normalized_title = normalize_text(title)
    normalized_page = normalize_text(page_text)

    return (
        normalized_team in normalized_title
        or normalized_team in normalized_page[:5000]
    )


def is_valid_stats_url(url: str, team_name: str) -> bool:
    if ".pdf" in url.lower():
        return False

    if "sports/womens-basketball/stats" not in url.lower():
        return False

    try:
        players = get_full_roster_stats(url)

        if len(players) == 0:
            return False

        return page_mentions_team(url, team_name)

    except Exception:
        return False


def find_opponent_stats_url(team_name: str) -> Optional[str]:
    queries = [
        f"{team_name} women's basketball cumulative statistics",
        f"{team_name} women's basketball stats",
        f"{team_name} wbb stats",
    ]

    valid_candidates = []

    for query in queries:
        print(f"Search results for: {query}")
        results = search_web(query)

        for result in results:
            title = result.get("title", "")
            url = result.get("link", "")

            print(title)
            print(url)
            print()

            if not is_valid_stats_url(url, team_name):
                continue

            detected_season = detect_season_from_stats_page(url)

            if not detected_season:
                continue

            valid_candidates.append(
                {
                    "url": url,
                    "season": detected_season,
                    "season_start": season_start_year(detected_season),
                }
            )

    if not valid_candidates:
        return None

    best = max(valid_candidates, key=lambda item: item["season_start"])
    return best["url"]


if __name__ == "__main__":
    team_name = "George Fox"

    url = find_opponent_stats_url(team_name)

    print("Best stats URL:")
    print(url)