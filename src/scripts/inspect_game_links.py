import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL = "https://cmsathletics.org/sports/womens-basketball/stats"

response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

for link in soup.find_all("a"):
    text = link.get_text(strip=True)
    href = link.get("href")

    if not href:
        continue

    if "boxscore" in href.lower() or "box-score" in href.lower() or "womens-basketball" in href.lower():
        print(text, urljoin(URL, href))