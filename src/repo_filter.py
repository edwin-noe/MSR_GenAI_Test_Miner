import requests, time, base64
# from config import INTERSECTION_PHRASES, REPO_FILES_TO_CHECK, AI_LIBRARIES, GITHUB_TOKEN
from .config import GENAI_KEYWORDS

class RepoFilter:
    # @staticmethod
    # def fetch_file_content(repo_full_name, file_path):
    #     url = f"https://api.github.com/repos/{repo_full_name}/contents/{file_path}"
    #     headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    #     response = requests.get(url, headers=headers)
    #     if response.status_code == 404:
    #         return ""
    #     if response.status_code == 403:
    #         reset_time = int(response.headers.get("X-RateLimit-Reset", time.time()))
    #         sleep_seconds = max(reset_time - time.time(), 5)
    #         print(f"⚠️ Rate limit hit while fetching {file_path}, sleeping {sleep_seconds:.1f}s...")
    #         time.sleep(sleep_seconds)
    #         raise Exception("Rate limit hit, retrying...")
    #     response.raise_for_status()
    #     data = response.json()
    #     if "content" in data:
    #         return base64.b64decode(data["content"]).decode(errors="ignore")
    #     return ""
    #
    # @staticmethod
    # def repo_contains_ai_signals(repo_full_name):
    #     texts_to_scan = []
    #     for file_path in REPO_FILES_TO_CHECK:
    #         try:
    #             content = RepoFilter.fetch_file_content(repo_full_name, file_path)
    #             if content:
    #                 texts_to_scan.append(content.lower())
    #         except Exception as e:
    #             print(f"⚠️ Error fetching {file_path} from {repo_full_name}: {e}")
    #
    #     for phrase in INTERSECTION_PHRASES:
    #         if any(phrase.lower() in text for text in texts_to_scan):
    #             return True
    #
    #     for lib in AI_LIBRARIES:
    #         if any(lib.lower() in text for text in texts_to_scan):
    #             return True
    #
    #     return False

    @staticmethod
    def high_precision_filter(repo):
        desc = (repo.get("description") or "").lower()
        return bool(desc)
        # repo_full_name = repo.get("full_name")
        # desc = (repo.get("description") or "").lower()
        # if any(phrase.lower() in desc for phrase in INTERSECTION_PHRASES):
        #     return True
        # return RepoFilter.repo_contains_ai_signals(repo_full_name)

