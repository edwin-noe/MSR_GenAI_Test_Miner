"""
Repository Filtering Module

Multi-stage filtering pipeline for high-precision repository selection.
Implements validation based on 25+ repository characteristics.
"""

from typing import Dict, Any
from .config import INTERSECTION_PHRASES, GENAI_KEYWORDS, TEST_AUTOMATION_KEYWORDS


class RepoFilter:
    """
    Multi-stage filtering pipeline for repository validation.
    
    Stages:
    1. Basic validation: Minimal quality thresholds
    2. Content analysis: AI/testing intersection signals
    3. Activity validation: Ensure repository is maintained
    4. Quality scoring: Composite score based on all metrics
    """
    
    # Thresholds for filtering
    MIN_STARS = 50
    MIN_README_LENGTH = 100
    MAX_DAYS_SINCE_PUSH = 730  # 2 years
    MIN_QUALITY_SCORE = 10  # Out of 30 points
    
    @staticmethod
    def basic_filter(repo: Dict[str, Any]) -> bool:
        """
        Stage 1: Basic validation filter.
        
        Checks:
        - Has minimum stars
        - Has description
        - Not archived (if available)
        - Not a fork (if we want original repos)
        """
        stars = repo.get("stars", repo.get("stargazers_count", 0))
        if stars < RepoFilter.MIN_STARS:
            return False
        
        description = repo.get("description", "")
        if not description:
            return False
        
        # Check if archived (archived repos are not actively maintained)
        if repo.get("archived", False):
            return False
        
        return True
    
    @staticmethod
    def content_filter(enriched_repo: Dict[str, Any]) -> bool:
        """
        Stage 2: Content-based filtering.
        
        Checks for AI/testing intersection signals:
        - AI keywords in README
        - Testing keywords in README
        - AI dependencies
        - Intersection phrases
        """
        # Must have some README content
        if enriched_repo.get("readme_length", 0) < RepoFilter.MIN_README_LENGTH:
            return False
        
        # Check for AI signals
        ai_signals = enriched_repo.get("ai_keyword_count", 0) + \
                     enriched_repo.get("ai_dependency_count", 0)
        
        # Check for testing signals
        test_signals = enriched_repo.get("test_keyword_count", 0) + \
                       (1 if enriched_repo.get("has_test_directory", False) else 0) + \
                       (1 if enriched_repo.get("has_ci_config", False) else 0)
        
        # Must have at least some AI signal
        if ai_signals < 1:
            return False
        
        # For high precision, prefer repos with intersection signals
        intersection_signals = enriched_repo.get("intersection_phrase_count", 0)
        
        # Accept if:
        # 1. Has explicit intersection phrases, OR
        # 2. Has both AI and testing signals
        return intersection_signals > 0 or (ai_signals >= 2 and test_signals >= 1)
    
    @staticmethod
    def activity_filter(enriched_repo: Dict[str, Any]) -> bool:
        """
        Stage 3: Activity-based filtering.
        
        Checks:
        - Recently active (pushed within last 2 years)
        - Has commits
        - Has contributors
        """
        days_since_push = enriched_repo.get("days_since_last_push")
        if days_since_push is None or days_since_push > RepoFilter.MAX_DAYS_SINCE_PUSH:
            return False
        
        # Must have some activity
        if enriched_repo.get("commit_count", 0) < 1:
            return False
        
        if enriched_repo.get("contributor_count", 0) < 1:
            return False
        
        return True
    
    @staticmethod
    def calculate_quality_score(enriched_repo: Dict[str, Any]) -> float:
        """
        Calculate composite quality score (0-30 points).
        
        Scoring rubric:
        - Popularity (0-5): Based on stars
        - Activity (0-5): Based on commits and recency
        - Community (0-5): Based on contributors, issues, discussions
        - Documentation (0-5): Based on README, guides, license
        - AI/Testing signals (0-10): Based on keyword counts and intersection
        """
        score = 0.0
        
        # Popularity (0-5)
        stars = enriched_repo.get("stars", 0)
        if stars >= 10000:
            score += 5
        elif stars >= 5000:
            score += 4
        elif stars >= 1000:
            score += 3
        elif stars >= 500:
            score += 2
        elif stars >= 100:
            score += 1
        
        # Activity (0-5)
        days_since_push = enriched_repo.get("days_since_last_push", 9999)
        if days_since_push <= 30:
            score += 3
        elif days_since_push <= 90:
            score += 2
        elif days_since_push <= 365:
            score += 1
        
        commits_per_month = enriched_repo.get("commits_per_month", 0)
        if commits_per_month >= 10:
            score += 2
        elif commits_per_month >= 5:
            score += 1
        
        # Community (0-5)
        contributors = enriched_repo.get("contributor_count", 0)
        if contributors >= 50:
            score += 2
        elif contributors >= 10:
            score += 1
        
        if enriched_repo.get("has_discussions", False):
            score += 1
        
        if enriched_repo.get("open_issues", 0) > 0:
            score += 1  # Active issue tracking
        
        if enriched_repo.get("has_topics", False):
            score += 1
        
        # Documentation (0-5)
        if enriched_repo.get("readme_length", 0) >= 1000:
            score += 2
        elif enriched_repo.get("readme_length", 0) >= 500:
            score += 1
        
        if enriched_repo.get("has_contributing", False):
            score += 1
        
        if enriched_repo.get("has_license", False):
            score += 1
        
        if enriched_repo.get("has_code_of_conduct", False):
            score += 1
        
        # AI/Testing signals (0-10) - Most important for research relevance
        ai_keyword_count = enriched_repo.get("ai_keyword_count", 0)
        test_keyword_count = enriched_repo.get("test_keyword_count", 0)
        intersection_count = enriched_repo.get("intersection_phrase_count", 0)
        
        # Intersection phrases are strong signals
        if intersection_count >= 3:
            score += 4
        elif intersection_count >= 1:
            score += 2
        
        # AI keywords
        if ai_keyword_count >= 10:
            score += 2
        elif ai_keyword_count >= 5:
            score += 1
        
        # Testing keywords
        if test_keyword_count >= 10:
            score += 2
        elif test_keyword_count >= 5:
            score += 1
        
        # Has AI dependencies
        if enriched_repo.get("ai_dependency_count", 0) > 0:
            score += 1
        
        # Has test infrastructure
        if enriched_repo.get("has_test_directory", False):
            score += 1
        
        return min(score, 30.0)  # Cap at 30
    
    @staticmethod
    def high_precision_filter(enriched_repo: Dict[str, Any]) -> tuple[bool, float]:
        """
        Complete filtering pipeline with quality scoring.
        
        Returns:
            Tuple of (passes_filter, quality_score)
        """
        # Stage 1: Basic filter
        if not RepoFilter.basic_filter(enriched_repo):
            return False, 0.0
        
        # Stage 2: Content filter
        if not RepoFilter.content_filter(enriched_repo):
            return False, 0.0
        
        # Stage 3: Activity filter
        if not RepoFilter.activity_filter(enriched_repo):
            return False, 0.0
        
        # Stage 4: Calculate quality score
        quality_score = RepoFilter.calculate_quality_score(enriched_repo)
        
        # Accept if score meets threshold
        passes = quality_score >= RepoFilter.MIN_QUALITY_SCORE
        
        return passes, quality_score
    
    @staticmethod
    def simple_filter(repo: Dict[str, Any]) -> bool:
        """Simple filter for basic search results (backward compatibility)."""
        return RepoFilter.basic_filter(repo)

