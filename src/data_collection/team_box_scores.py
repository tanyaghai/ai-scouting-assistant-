import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

HEADERS = {"User-Agent": "Mozilla/5.0"}


def get_box_score_links(stats_url: str):
    response = requests.get(stats_url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    links = []

    for link in soup.find_all("a"):
        text = link.get_text(strip=True)
        href = link.get("href")

        if not href:
            continue

        if "boxscore.aspx" in href:
            full_url = urljoin(stats_url, href)

            item = {
                "opponent": text,
                "url": full_url
            }

            if item not in links:
                links.append(item)

    return links


def get_last_five_box_score_links(stats_url: str):
    links = get_box_score_links(stats_url)

    # Remove duplicates while preserving order by URL
    seen = set()
    unique_links = []

    for link in links:
        if link["url"] not in seen:
            unique_links.append(link)
            seen.add(link["url"])

    return unique_links[-5:]


if __name__ == "__main__":
    cms_url = "https://cmsathletics.org/sports/womens-basketball/stats"

    links = get_last_five_box_score_links(cms_url)

    for link in links:
        print(link)