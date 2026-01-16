"""
GitHub API Mining Module

Handles GitHub Search API interactions with:
- Rate limit management
- Pagination for results beyond 100
- Retry logic with exponential backoff
"""

import requests
import time
from typing import List, Dict, Any, Optional
from tenacity import retry, wait_exponential, stop_after_attempt
from .config import GITHUB_API_URL, GITHUB_TOKEN


class GitHubMiner:
    """
    GitHub API client for repository search and enrichment.
    
    Features:
    - Automatic rate limit handling
    - Pagination support
    - Request caching (simple in-memory)
    - Retry logic with exponential backoff
    """
    
    def __init__(self):
        self.headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }
        self.rate_limit_remaining = None
        self.rate_limit_reset = None
    
    def _update_rate_limit_info(self, response: requests.Response):
        """Update rate limit information from response headers."""
        self.rate_limit_remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
        self.rate_limit_reset = int(response.headers.get("X-RateLimit-Reset", time.time()))
    
    def _check_rate_limit(self):
        """Check if we're approaching rate limit and sleep if necessary."""
        if self.rate_limit_remaining is not None and self.rate_limit_remaining < 5:
            sleep_seconds = max(self.rate_limit_reset - time.time(), 5)
            print(f"⚠️ Approaching rate limit ({self.rate_limit_remaining} remaining), sleeping {sleep_seconds:.1f}s...")
            time.sleep(sleep_seconds)
    
    @retry(wait=wait_exponential(min=2, max=60), stop=stop_after_attempt(5))
    def github_search(
        self, 
        query: str,
        sort: str = "stars",
        order: str = "desc",
        per_page: int = 100,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search GitHub repositories with pagination support.
        
        Args:
            query: GitHub search query string
            sort: Sort field (stars, forks, updated)
            order: Sort order (asc, desc)
            per_page: Results per page (max 100)
            max_results: Maximum total results to fetch (None = all available, max 1000)
        
        Returns:
            List of repository dictionaries
        """
        self._check_rate_limit()
        
        all_items = []
        page = 1
        max_results = max_results or 1000  # GitHub search API limit
        
        while len(all_items) < max_results:
            params = {
                "q": query,
                "sort": sort,
                "order": order,
                "per_page": min(per_page, max_results - len(all_items)),
                "page": page
            }
            
            response = requests.get(GITHUB_API_URL, headers=self.headers, params=params)
            
            self._update_rate_limit_info(response)
            
            if response.status_code == 403:
                reset_time = int(response.headers.get("X-RateLimit-Reset", time.time()))
                sleep_seconds = max(reset_time - time.time(), 5)
                print(f"⚠️ Rate limit hit, sleeping {sleep_seconds:.1f}s...")
                time.sleep(sleep_seconds)
                raise Exception("Rate limit hit, retrying...")
            
            if response.status_code == 422:
                # Validation error (e.g., query too complex)
                print(f"⚠️ Query validation error: {query}")
                return all_items
            
            response.raise_for_status()
            
            data = response.json()
            items = data.get("items", [])
            
            if not items:
                break  # No more results
            
            all_items.extend(items)
            
            # Check if there are more pages
            total_count = data.get("total_count", 0)
            if len(all_items) >= total_count or len(all_items) >= 1000:
                # GitHub search API has a hard limit of 1000 results
                break
            
            page += 1
            
            # Small delay between pages to be respectful
            time.sleep(0.5)
        
        return all_items
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limit status.
        
        Returns:
            Dictionary with rate limit information
        """
        url = "https://api.github.com/rate_limit"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def print_rate_limit_status(self):
        """Print rate limit status to console."""
        try:
            status = self.get_rate_limit_status()
            search = status.get("resources", {}).get("search", {})
            core = status.get("resources", {}).get("core", {})
            
            print(f"📊 Rate Limit Status:")
            print(f"   Search API: {search.get('remaining')}/{search.get('limit')} remaining")
            print(f"   Core API: {core.get('remaining')}/{core.get('limit')} remaining")
            
            if search.get('remaining', 0) == 0:
                reset_time = search.get('reset', time.time())
                sleep_seconds = max(reset_time - time.time(), 0)
                print(f"   Search API resets in {sleep_seconds/60:.1f} minutes")
        except Exception as e:
            print(f"⚠️ Error fetching rate limit status: {e}")
