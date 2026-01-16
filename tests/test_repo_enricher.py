"""
Unit tests for RepoEnricher module.

Tests repository enrichment logic and characteristic extraction.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.repo_enricher import RepoEnricher


class TestRepoEnricher(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.enricher = RepoEnricher()
        
        self.mock_repo = {
            "full_name": "test/repo",
            "html_url": "https://github.com/test/repo",
            "stargazers_count": 100,
            "forks_count": 20,
            "watchers_count": 50,
            "open_issues_count": 5,
            "size": 1000
        }
    
    def test_days_since_calculation(self):
        """Test days since date calculation."""
        # Recent date (should be small number)
        from datetime import datetime, timedelta
        recent = (datetime.now() - timedelta(days=5)).isoformat()
        days = self.enricher._days_since(recent)
        self.assertIsNotNone(days)
        self.assertGreaterEqual(days, 4)
        self.assertLessEqual(days, 6)
    
    def test_days_since_none(self):
        """Test days since with None input."""
        result = self.enricher._days_since(None)
        self.assertIsNone(result)
    
    def test_calculate_commits_per_month(self):
        """Test commits per month calculation."""
        # 100 commits over 10 days
        cpm = self.enricher._calculate_commits_per_month(100, 10)
        self.assertGreater(cpm, 0)
        
        # Should be roughly 100 / (10/30) = 300
        self.assertAlmostEqual(cpm, 300, delta=10)
    
    def test_calculate_commits_per_month_zero_days(self):
        """Test commits per month with zero days."""
        cpm = self.enricher._calculate_commits_per_month(100, 0)
        self.assertEqual(cpm, 0.0)
    
    def test_calculate_releases_per_year(self):
        """Test releases per year calculation."""
        # 12 releases over 365 days
        rpy = self.enricher._calculate_releases_per_year(12, 365)
        self.assertAlmostEqual(rpy, 12, delta=0.1)
        
        # 24 releases over 730 days (2 years)
        rpy = self.enricher._calculate_releases_per_year(24, 730)
        self.assertAlmostEqual(rpy, 12, delta=0.5)
    
    def test_get_top_languages(self):
        """Test top languages extraction."""
        languages = {
            "Python": 10000,
            "JavaScript": 5000,
            "TypeScript": 3000,
            "HTML": 1000,
            "CSS": 500
        }
        
        top_3 = self.enricher._get_top_languages(languages, top_n=3)
        
        self.assertEqual(len(top_3), 3)
        self.assertEqual(top_3[0], "Python")
        self.assertEqual(top_3[1], "JavaScript")
        self.assertEqual(top_3[2], "TypeScript")
    
    def test_count_keywords_in_text(self):
        """Test keyword counting in text."""
        text = "This is a test with ChatGPT and OpenAI. ChatGPT is mentioned twice."
        keywords = ["ChatGPT", "OpenAI", "GPT-4"]
        
        count = self.enricher._count_keywords_in_text(text, keywords)
        
        # ChatGPT: 2, OpenAI: 1, GPT-4: 0 = 3 total
        self.assertEqual(count, 3)
    
    def test_count_keywords_case_insensitive(self):
        """Test keyword counting is case-insensitive."""
        text = "chatgpt OPENAI OpenAi"
        keywords = ["ChatGPT", "OpenAI"]
        
        count = self.enricher._count_keywords_in_text(text, keywords)
        
        # chatgpt: 1, OPENAI/OpenAi: 2 = 3 total
        self.assertEqual(count, 3)
    
    def test_count_keywords_empty_text(self):
        """Test keyword counting with empty text."""
        count = self.enricher._count_keywords_in_text("", ["keyword"])
        self.assertEqual(count, 0)
        
        count = self.enricher._count_keywords_in_text(None, ["keyword"])
        self.assertEqual(count, 0)
    
    @patch('src.repo_enricher.RepoEnricher._api_get')
    def test_enrich_repository_basic(self, mock_api_get):
        """Test basic repository enrichment."""
        # Mock API responses
        mock_api_get.side_effect = [
            {  # Repo details
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "pushed_at": "2024-01-15T00:00:00Z",
                "language": "Python",
                "has_wiki": True,
                "has_pages": False,
                "has_discussions": True,
                "topics": ["ai", "testing"],
                "license": {"name": "MIT"},
                "description": "Test repository",
                "default_branch": "main"
            },
            None,  # Commits
            None,  # Contributors
            None,  # Releases
            None,  # Languages
        ]
        
        enriched = self.enricher.enrich_repository(self.mock_repo)
        
        # Check basic metrics are preserved
        self.assertEqual(enriched["full_name"], "test/repo")
        self.assertEqual(enriched["stars"], 100)
        self.assertEqual(enriched["forks"], 20)
        
        # Check enriched fields exist
        self.assertIn("created_at", enriched)
        self.assertIn("primary_language", enriched)
        self.assertIn("has_wiki", enriched)
        self.assertIn("has_license", enriched)


if __name__ == "__main__":
    unittest.main()
