"""
Unit tests for RepoFilter module.

Tests the multi-stage filtering pipeline and quality scoring.
"""

import unittest
from src.repo_filter import RepoFilter


class TestRepoFilter(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.basic_repo = {
            "full_name": "test/repo",
            "stars": 100,
            "stargazers_count": 100,
            "description": "A test repository",
            "archived": False
        }
        
        self.enriched_repo = {
            "full_name": "test/repo",
            "stars": 100,
            "description": "AI testing repository",
            "archived": False,
            "readme_length": 500,
            "ai_keyword_count": 5,
            "test_keyword_count": 3,
            "ai_dependency_count": 1,
            "has_test_directory": True,
            "has_ci_config": True,
            "intersection_phrase_count": 1,
            "days_since_last_push": 30,
            "commit_count": 100,
            "contributor_count": 5,
            "commits_per_month": 10,
            "has_discussions": True,
            "open_issues": 10,
            "has_topics": True,
            "has_contributing": True,
            "has_license": True,
            "has_code_of_conduct": True
        }
    
    def test_basic_filter_pass(self):
        """Test basic filter with valid repository."""
        result = RepoFilter.basic_filter(self.basic_repo)
        self.assertTrue(result)
    
    def test_basic_filter_low_stars(self):
        """Test basic filter rejects low-starred repos."""
        low_stars = self.basic_repo.copy()
        low_stars["stars"] = 10
        low_stars["stargazers_count"] = 10
        
        result = RepoFilter.basic_filter(low_stars)
        self.assertFalse(result)
    
    def test_basic_filter_no_description(self):
        """Test basic filter rejects repos without description."""
        no_desc = self.basic_repo.copy()
        no_desc["description"] = ""
        
        result = RepoFilter.basic_filter(no_desc)
        self.assertFalse(result)
    
    def test_basic_filter_archived(self):
        """Test basic filter rejects archived repos."""
        archived = self.basic_repo.copy()
        archived["archived"] = True
        
        result = RepoFilter.basic_filter(archived)
        self.assertFalse(result)
    
    def test_content_filter_pass(self):
        """Test content filter with valid enriched repo."""
        result = RepoFilter.content_filter(self.enriched_repo)
        self.assertTrue(result)
    
    def test_content_filter_short_readme(self):
        """Test content filter rejects repos with short README."""
        short_readme = self.enriched_repo.copy()
        short_readme["readme_length"] = 50
        
        result = RepoFilter.content_filter(short_readme)
        self.assertFalse(result)
    
    def test_content_filter_no_ai_signals(self):
        """Test content filter rejects repos without AI signals."""
        no_ai = self.enriched_repo.copy()
        no_ai["ai_keyword_count"] = 0
        no_ai["ai_dependency_count"] = 0
        
        result = RepoFilter.content_filter(no_ai)
        self.assertFalse(result)
    
    def test_activity_filter_pass(self):
        """Test activity filter with active repo."""
        result = RepoFilter.activity_filter(self.enriched_repo)
        self.assertTrue(result)
    
    def test_activity_filter_old_push(self):
        """Test activity filter rejects old repos."""
        old = self.enriched_repo.copy()
        old["days_since_last_push"] = 1000
        
        result = RepoFilter.activity_filter(old)
        self.assertFalse(result)
    
    def test_calculate_quality_score(self):
        """Test quality score calculation."""
        score = RepoFilter.calculate_quality_score(self.enriched_repo)
        
        # Should be positive and reasonable
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 30)
    
    def test_quality_score_high_stars(self):
        """Test that high stars increase quality score."""
        low_stars = self.enriched_repo.copy()
        low_stars["stars"] = 100
        score_low = RepoFilter.calculate_quality_score(low_stars)
        
        high_stars = self.enriched_repo.copy()
        high_stars["stars"] = 10000
        score_high = RepoFilter.calculate_quality_score(high_stars)
        
        self.assertGreater(score_high, score_low)
    
    def test_quality_score_intersection_phrases(self):
        """Test that intersection phrases boost quality score."""
        no_intersection = self.enriched_repo.copy()
        no_intersection["intersection_phrase_count"] = 0
        score_low = RepoFilter.calculate_quality_score(no_intersection)
        
        with_intersection = self.enriched_repo.copy()
        with_intersection["intersection_phrase_count"] = 5
        score_high = RepoFilter.calculate_quality_score(with_intersection)
        
        self.assertGreater(score_high, score_low)
    
    def test_high_precision_filter(self):
        """Test complete filtering pipeline."""
        passes, score = RepoFilter.high_precision_filter(self.enriched_repo)
        
        self.assertTrue(passes)
        self.assertGreater(score, 0)
    
    def test_simple_filter(self):
        """Test simple filter (backward compatibility)."""
        result = RepoFilter.simple_filter(self.basic_repo)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
