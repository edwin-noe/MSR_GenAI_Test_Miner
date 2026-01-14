import requests, time
from tenacity import retry, wait_exponential, stop_after_attempt
from .config import GITHUB_API_URL, GITHUB_TOKEN

class GitHubMiner:
    def __init__(self):
        self.headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }

    @retry(wait=wait_exponential(min=2, max=60), stop=stop_after_attempt(5))
    def github_search(self, query: str):
        params = {"q": query, "sort": "stars", "order": "desc", "per_page": 50}
        response = requests.get(GITHUB_API_URL, headers=self.headers, params=params)
        if response.status_code == 403:
            reset_time = int(response.headers.get("X-RateLimit-Reset", time.time()))
            sleep_seconds = max(reset_time - time.time(), 5)
            print(f"⚠️ Rate limit hit, sleeping {sleep_seconds:.1f}s...")
            time.sleep(sleep_seconds)
            raise Exception("Rate limit hit, retrying...")
        response.raise_for_status()
        return response.json().get("items", [])
