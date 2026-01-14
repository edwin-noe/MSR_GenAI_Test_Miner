import os
import time
import requests
from tenacity import retry, wait_exponential, stop_after_attempt

GITHUB_API_URL = "https://api.github.com/search/repositories"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")


def github_search(query: str):
    """
    Search GitHub repositories using query (stars, language, keywords)
    Handles rate limits with retries.
    Returns a list of repository dicts.
    """

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    @retry(wait=wait_exponential(min=2, max=60), stop=stop_after_attempt(5))
    def fetch():
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": 50
        }
        response = requests.get(GITHUB_API_URL, headers=headers, params=params)

        if response.status_code == 403:
            reset_time = int(response.headers.get("X-RateLimit-Reset", time.time()))
            sleep_seconds = max(reset_time - time.time(), 5)
            print(f"Rate limit hit, sleeping {sleep_seconds}s...")
            time.sleep(sleep_seconds)
            raise Exception("Rate limit hit, retrying...")

        response.raise_for_status()
        return response.json().get("items", [])

    return fetch()
