#!/usr/bin/env python3
"""
Quick demonstration script for MSR GenAI Test Miner.

This script demonstrates the core functionality without requiring
API access. Useful for testing setup and understanding the system.
"""

from src.query_generator import QueryGenerator
from src.repo_filter import RepoFilter
from src.repo_enricher import RepoEnricher


def demo_query_generation():
    """Demonstrate query generation capabilities."""
    print("=" * 70)
    print("QUERY GENERATION DEMO")
    print("=" * 70)
    
    # Simple queries
    print("\n1. Simple Queries (for testing):")
    simple_queries = QueryGenerator.generate_simple_queries()
    print(f"   Total: {len(simple_queries)}")
    print("   Examples:")
    for query in simple_queries[:3]:
        print(f"     - {query}")
    
    # Sharded queries
    print("\n2. Sharded Queries (for comprehensive mining):")
    sharded_queries = QueryGenerator.generate_sharded_queries()
    print(f"   Total: {len(sharded_queries)}")
    print("   Examples:")
    for query in sharded_queries[:5]:
        print(f"     - {query}")
    
    # Query statistics
    print("\n3. Query Statistics:")
    has_language = sum(1 for q in sharded_queries if "language:" in q)
    has_created = sum(1 for q in sharded_queries if "created:" in q)
    has_star_range = sum(1 for q in sharded_queries if ".." in q)
    
    print(f"   With language filter: {has_language}")
    print(f"   With time filter: {has_created}")
    print(f"   With star ranges: {has_star_range}")


def demo_filtering():
    """Demonstrate filtering capabilities."""
    print("\n" + "=" * 70)
    print("FILTERING DEMO")
    print("=" * 70)
    
    # Example repositories
    good_repo = {
        "full_name": "example/good-ai-test-repo",
        "stars": 500,
        "description": "AI-powered test generation using GPT-4",
        "archived": False,
        "readme_length": 2000,
        "ai_keyword_count": 15,
        "test_keyword_count": 20,
        "ai_dependency_count": 3,
        "has_test_directory": True,
        "has_ci_config": True,
        "intersection_phrase_count": 3,
        "days_since_last_push": 5,
        "commit_count": 500,
        "contributor_count": 10,
        "commits_per_month": 15,
        "has_discussions": True,
        "open_issues": 25,
        "has_topics": True,
        "has_contributing": True,
        "has_license": True,
        "has_code_of_conduct": True
    }
    
    bad_repo = {
        "full_name": "example/bad-repo",
        "stars": 10,
        "description": "",
        "archived": True
    }
    
    print("\n1. Good Repository Example:")
    print(f"   Name: {good_repo['full_name']}")
    print(f"   Stars: {good_repo['stars']}")
    passes, score = RepoFilter.high_precision_filter(good_repo)
    print(f"   Passes Filter: {passes}")
    print(f"   Quality Score: {score:.2f}/30.0")
    
    print("\n2. Bad Repository Example:")
    print(f"   Name: {bad_repo['full_name']}")
    print(f"   Stars: {bad_repo['stars']}")
    print(f"   Description: (empty)")
    passes = RepoFilter.simple_filter(bad_repo)
    print(f"   Passes Filter: {passes}")
    
    print("\n3. Quality Score Breakdown:")
    print("   The quality score (0-30 points) considers:")
    print("     - Popularity (0-5): Stars count")
    print("     - Activity (0-5): Recent commits, frequency")
    print("     - Community (0-5): Contributors, discussions")
    print("     - Documentation (0-5): README, guides, license")
    print("     - AI/Testing Signals (0-10): Keywords, intersection phrases")


def demo_enrichment():
    """Demonstrate enrichment capabilities."""
    print("\n" + "=" * 70)
    print("ENRICHMENT DEMO")
    print("=" * 70)
    
    enricher = RepoEnricher()
    
    print("\n30 Repository Characteristics Collected:")
    print("\n  Basic Metrics (5):")
    print("    1. Stars    2. Forks    3. Watchers    4. Issues    5. Size")
    
    print("\n  Activity Metrics (5):")
    print("    6. Commits    7. Contributors    8. Days since push")
    print("    9. Days since creation    10. Commits/month")
    
    print("\n  Release Metrics (3):")
    print("    11. Release count    12. Days since release")
    print("    13. Releases/year")
    
    print("\n  Language Metrics (2):")
    print("    14. Primary language    15. Language distribution")
    
    print("\n  Community Metrics (4):")
    print("    16. Has wiki    17. Has pages    18. Has discussions")
    print("    19. Has topics")
    
    print("\n  Documentation Metrics (3):")
    print("    20. README length    21. Has CONTRIBUTING")
    print("    22. Has CODE_OF_CONDUCT")
    
    print("\n  Testing Indicators (2):")
    print("    23. Has test directory    24. Has CI/CD config")
    
    print("\n  AI/Testing Intersection (3):")
    print("    25. AI dependencies    26. AI keywords")
    print("    27. Test keywords")
    
    print("\n  Quality Indicators (3):")
    print("    28. Has license    29. Has description")
    print("    30. Quality score")
    
    print("\n  Helper Functions Available:")
    print(f"    - _days_since(): Calculate age")
    print(f"    - _count_keywords_in_text(): Keyword frequency")
    print(f"    - _calculate_commits_per_month(): Activity rate")
    print(f"    - _calculate_releases_per_year(): Release cadence")
    
    # Test some helper functions
    print("\n  Example Calculations:")
    cpm = enricher._calculate_commits_per_month(120, 60)
    print(f"    120 commits in 60 days = {cpm:.1f} commits/month")
    
    rpy = enricher._calculate_releases_per_year(24, 730)
    print(f"    24 releases in 730 days = {rpy:.1f} releases/year")
    
    keywords = enricher._count_keywords_in_text(
        "This project uses ChatGPT and OpenAI for testing",
        ["ChatGPT", "OpenAI", "testing"]
    )
    print(f"    Keyword count in sample text: {keywords}")


def main():
    """Run all demonstrations."""
    print("\n")
    print("█" * 70)
    print("█  MSR GENAI TEST MINER - DEMONSTRATION")
    print("█" * 70)
    print("\nThis demo shows the core capabilities without requiring API access.\n")
    
    try:
        demo_query_generation()
        demo_filtering()
        demo_enrichment()
        
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print("\n✓ Query generation: Creates 2,500-4,000 sharded queries")
        print("✓ Filtering: Multi-stage pipeline with quality scoring")
        print("✓ Enrichment: Collects 30 repository characteristics")
        print("\nTo run the actual mining (requires GITHUB_TOKEN):")
        print("  python -m src.main              # Full mining")
        print("  python -m src.main --simple     # Quick test")
        print("  python -m src.main --help       # See all options")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
