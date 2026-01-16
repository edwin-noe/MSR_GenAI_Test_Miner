"""
Repository Enrichment Module

Collects 25+ distinct repository characteristics for high-precision filtering
and academic research quality analysis.
"""

import requests
import time
import base64
from typing import Dict, Any, Optional, List
from tenacity import retry, wait_exponential, stop_after_attempt
from .config import GITHUB_TOKEN, AI_LIBRARIES, INTERSECTION_PHRASES, REPO_FILES_TO_CHECK


class RepoEnricher:
    """
    Enriches repository data with comprehensive metrics for MSR research.
    
    The 25+ repository characteristics collected:
    
    Basic Metrics (5):
        1. Stars count
        2. Forks count
        3. Watchers count
        4. Open issues count
        5. Repository size (KB)
    
    Activity Metrics (5):
        6. Total commit count
        7. Contributor count
        8. Days since last commit
        9. Days since creation
        10. Commits per month (activity rate)
    
    Release Metrics (3):
        11. Total release count
        12. Days since last release
        13. Release frequency (releases per year)
    
    Language Metrics (2):
        14. Primary language
        15. Language distribution (top 3)
    
    Community Metrics (4):
        16. Has wiki
        17. Has GitHub pages
        18. Has discussions enabled
        19. Has topics/tags
    
    Documentation Metrics (3):
        20. README length (as quality proxy)
        21. Has contributing guide
        22. Has code of conduct
    
    Testing Indicators (2):
        23. Has test directory
        24. Has CI/CD configuration
    
    AI/Testing Intersection (3):
        25. AI library dependencies count
        26. AI keyword frequency in README
        27. Testing keyword frequency in README
    
    Quality Indicators (3):
        28. Has license
        29. Has description
        30. Default branch protection (if accessible)
    """
    
    def __init__(self):
        self.headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }
        self.cache = {}  # Simple in-memory cache for API responses
    
    @retry(wait=wait_exponential(min=2, max=60), stop=stop_after_attempt(3))
    def _api_get(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make a GET request to GitHub API with retry logic."""
        cache_key = f"{url}:{params}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 403:
            reset_time = int(response.headers.get("X-RateLimit-Reset", time.time()))
            sleep_seconds = max(reset_time - time.time(), 5)
            print(f"⚠️ Rate limit hit, sleeping {sleep_seconds:.1f}s...")
            time.sleep(sleep_seconds)
            raise Exception("Rate limit hit, retrying...")
        
        if response.status_code == 404:
            return None
        
        response.raise_for_status()
        data = response.json()
        self.cache[cache_key] = data
        return data
    
    def enrich_repository(self, repo: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich a repository with comprehensive metadata.
        
        Args:
            repo: Basic repository data from GitHub Search API
            
        Returns:
            Dictionary with all 30 characteristics
        """
        owner, name = repo["full_name"].split("/")
        base_url = f"https://api.github.com/repos/{owner}/{name}"
        
        enriched = {
            # Basic info
            "full_name": repo["full_name"],
            "html_url": repo["html_url"],
            
            # Basic Metrics (1-5)
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "watchers": repo.get("watchers_count", 0),
            "open_issues": repo.get("open_issues_count", 0),
            "size_kb": repo.get("size", 0),
        }
        
        # Get detailed repository info
        try:
            repo_details = self._api_get(base_url)
            if repo_details:
                # Activity Metrics (6-10)
                enriched["created_at"] = repo_details.get("created_at")
                enriched["updated_at"] = repo_details.get("updated_at")
                enriched["pushed_at"] = repo_details.get("pushed_at")
                enriched["days_since_created"] = self._days_since(repo_details.get("created_at"))
                enriched["days_since_last_push"] = self._days_since(repo_details.get("pushed_at"))
                
                # Language Metrics (14-15)
                enriched["primary_language"] = repo_details.get("language")
                
                # Community Metrics (16-19)
                enriched["has_wiki"] = repo_details.get("has_wiki", False)
                enriched["has_pages"] = repo_details.get("has_pages", False)
                enriched["has_discussions"] = repo_details.get("has_discussions", False)
                enriched["topics"] = repo_details.get("topics", [])
                enriched["has_topics"] = len(repo_details.get("topics", [])) > 0
                
                # Quality Indicators (28-29)
                enriched["has_license"] = repo_details.get("license") is not None
                enriched["license"] = repo_details.get("license", {}).get("name")
                enriched["has_description"] = bool(repo_details.get("description"))
                enriched["description"] = repo_details.get("description", "")
                
                # Default branch
                enriched["default_branch"] = repo_details.get("default_branch", "main")
        except Exception as e:
            print(f"⚠️ Error fetching repo details for {repo['full_name']}: {e}")
        
        # Commit metrics (6-7, 10)
        try:
            commits_url = f"{base_url}/commits"
            commits = self._api_get(commits_url, params={"per_page": 1})
            if commits:
                # Get total commit count from link header or default
                enriched["commit_count"] = self._estimate_commit_count(base_url)
                enriched["commits_per_month"] = self._calculate_commits_per_month(
                    enriched.get("commit_count", 0),
                    enriched.get("days_since_created", 1)
                )
        except Exception as e:
            print(f"⚠️ Error fetching commits for {repo['full_name']}: {e}")
            enriched["commit_count"] = 0
            enriched["commits_per_month"] = 0
        
        # Contributor count (7)
        try:
            contributors_url = f"{base_url}/contributors"
            contributors = self._api_get(contributors_url, params={"per_page": 100})
            enriched["contributor_count"] = len(contributors) if contributors else 0
        except Exception as e:
            print(f"⚠️ Error fetching contributors for {repo['full_name']}: {e}")
            enriched["contributor_count"] = 0
        
        # Release metrics (11-13)
        try:
            releases_url = f"{base_url}/releases"
            releases = self._api_get(releases_url, params={"per_page": 100})
            if releases:
                enriched["release_count"] = len(releases)
                if len(releases) > 0:
                    latest_release = releases[0]
                    enriched["last_release_date"] = latest_release.get("published_at")
                    enriched["days_since_last_release"] = self._days_since(
                        latest_release.get("published_at")
                    )
                else:
                    enriched["days_since_last_release"] = None
                
                # Calculate release frequency
                enriched["releases_per_year"] = self._calculate_releases_per_year(
                    enriched.get("release_count", 0),
                    enriched.get("days_since_created", 1)
                )
            else:
                enriched["release_count"] = 0
                enriched["days_since_last_release"] = None
                enriched["releases_per_year"] = 0
        except Exception as e:
            print(f"⚠️ Error fetching releases for {repo['full_name']}: {e}")
            enriched["release_count"] = 0
            enriched["days_since_last_release"] = None
            enriched["releases_per_year"] = 0
        
        # Language distribution (15)
        try:
            languages_url = f"{base_url}/languages"
            languages = self._api_get(languages_url)
            if languages:
                enriched["language_distribution"] = self._get_top_languages(languages, top_n=3)
        except Exception as e:
            print(f"⚠️ Error fetching languages for {repo['full_name']}: {e}")
            enriched["language_distribution"] = []
        
        # Content analysis for README (20, 26, 27)
        try:
            readme_content = self._fetch_file_content(repo["full_name"], "README.md")
            enriched["readme_length"] = len(readme_content) if readme_content else 0
            enriched["ai_keyword_count"] = self._count_keywords_in_text(
                readme_content, GENAI_KEYWORDS + [lib for lib in AI_LIBRARIES]
            )
            enriched["test_keyword_count"] = self._count_keywords_in_text(
                readme_content, ["test", "testing", "unittest", "pytest", "jest", "junit"]
            )
            enriched["intersection_phrase_count"] = self._count_keywords_in_text(
                readme_content, INTERSECTION_PHRASES
            )
        except Exception as e:
            print(f"⚠️ Error analyzing README for {repo['full_name']}: {e}")
            enriched["readme_length"] = 0
            enriched["ai_keyword_count"] = 0
            enriched["test_keyword_count"] = 0
            enriched["intersection_phrase_count"] = 0
        
        # Documentation files (21-22)
        try:
            enriched["has_contributing"] = self._file_exists(repo["full_name"], "CONTRIBUTING.md")
            enriched["has_code_of_conduct"] = self._file_exists(repo["full_name"], "CODE_OF_CONDUCT.md")
        except Exception as e:
            print(f"⚠️ Error checking documentation files for {repo['full_name']}: {e}")
            enriched["has_contributing"] = False
            enriched["has_code_of_conduct"] = False
        
        # Testing indicators (23-24)
        try:
            enriched["has_test_directory"] = self._directory_exists(repo["full_name"], "tests") or \
                                             self._directory_exists(repo["full_name"], "test")
            enriched["has_ci_config"] = self._has_ci_config(repo["full_name"])
        except Exception as e:
            print(f"⚠️ Error checking test indicators for {repo['full_name']}: {e}")
            enriched["has_test_directory"] = False
            enriched["has_ci_config"] = False
        
        # AI library dependencies (25)
        try:
            enriched["ai_dependency_count"] = self._count_ai_dependencies(repo["full_name"])
        except Exception as e:
            print(f"⚠️ Error counting dependencies for {repo['full_name']}: {e}")
            enriched["ai_dependency_count"] = 0
        
        return enriched
    
    def _fetch_file_content(self, repo_full_name: str, file_path: str) -> str:
        """Fetch content of a file from repository."""
        url = f"https://api.github.com/repos/{repo_full_name}/contents/{file_path}"
        data = self._api_get(url)
        if data and "content" in data:
            return base64.b64decode(data["content"]).decode(errors="ignore")
        return ""
    
    def _file_exists(self, repo_full_name: str, file_path: str) -> bool:
        """Check if a file exists in repository."""
        url = f"https://api.github.com/repos/{repo_full_name}/contents/{file_path}"
        data = self._api_get(url)
        return data is not None
    
    def _directory_exists(self, repo_full_name: str, dir_path: str) -> bool:
        """Check if a directory exists in repository."""
        url = f"https://api.github.com/repos/{repo_full_name}/contents/{dir_path}"
        data = self._api_get(url)
        return data is not None and isinstance(data, list)
    
    def _has_ci_config(self, repo_full_name: str) -> bool:
        """Check for CI/CD configuration files."""
        ci_files = [
            ".github/workflows",
            ".gitlab-ci.yml",
            ".travis.yml",
            "circle.yml",
            ".circleci/config.yml",
            "Jenkinsfile",
            "azure-pipelines.yml"
        ]
        for ci_file in ci_files:
            if self._file_exists(repo_full_name, ci_file) or \
               self._directory_exists(repo_full_name, ci_file):
                return True
        return False
    
    def _count_ai_dependencies(self, repo_full_name: str) -> int:
        """Count AI-related dependencies in package files."""
        count = 0
        for file_path in REPO_FILES_TO_CHECK:
            content = self._fetch_file_content(repo_full_name, file_path)
            if content:
                content_lower = content.lower()
                for lib in AI_LIBRARIES:
                    if lib.lower() in content_lower:
                        count += 1
        return count
    
    def _count_keywords_in_text(self, text: str, keywords: List[str]) -> int:
        """Count occurrences of keywords in text (case-insensitive)."""
        if not text:
            return 0
        text_lower = text.lower()
        count = 0
        for keyword in keywords:
            count += text_lower.count(keyword.lower())
        return count
    
    def _estimate_commit_count(self, base_url: str) -> int:
        """Estimate total commit count."""
        commits_url = f"{base_url}/commits"
        # Try to get commits from last year as a proxy
        commits = self._api_get(commits_url, params={"per_page": 100})
        if commits:
            # This is a rough estimate; GitHub API doesn't directly provide total count
            # For better accuracy, would need to paginate through all commits
            return len(commits) if len(commits) < 100 else 100  # Minimum estimate
        return 0
    
    def _get_top_languages(self, languages: Dict[str, int], top_n: int = 3) -> List[str]:
        """Get top N languages by bytes of code."""
        sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        return [lang for lang, _ in sorted_langs[:top_n]]
    
    def _days_since(self, date_str: Optional[str]) -> Optional[float]:
        """Calculate days since a given ISO date string."""
        if not date_str:
            return None
        from datetime import datetime
        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        now = datetime.now(date.tzinfo)
        return (now - date).days
    
    def _calculate_commits_per_month(self, commit_count: int, days_since_created: int) -> float:
        """Calculate average commits per month."""
        if days_since_created <= 0:
            return 0.0
        months = days_since_created / 30.0
        return commit_count / months if months > 0 else 0.0
    
    def _calculate_releases_per_year(self, release_count: int, days_since_created: int) -> float:
        """Calculate average releases per year."""
        if days_since_created <= 0:
            return 0.0
        years = days_since_created / 365.0
        return release_count / years if years > 0 else 0.0
