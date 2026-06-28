import re
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0"}


def detect_season_from_stats_page(stats_url: str):
    response = requests.get(stats_url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True)
    title = soup.title.get_text(" ", strip=True) if soup.title else ""

    combined = f"{title} {text}"

    match = re.search(r"(20\d{2})[-–](\d{2})", combined)
    if match:
        return f"{match.group(1)}-{match.group(2)}"

    return None