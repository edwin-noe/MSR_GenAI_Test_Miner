"""
Unit tests for QueryGenerator module.

Tests the query generation logic including sharding strategies.
"""

import unittest
from src.query_generator import QueryGenerator


class TestQueryGenerator(unittest.TestCase):
    
    def test_generate_simple_queries(self):
        """Test simple query generation."""
        queries = QueryGenerator.generate_simple_queries()
        
        # Should have one query per AI keyword
        self.assertGreater(len(queries), 0)
        
        # All queries should have stars filter
        for query in queries:
            self.assertIn("stars:", query)
    
    def test_generate_sharded_queries(self):
        """Test sharded query generation."""
        queries = QueryGenerator.generate_sharded_queries()
        
        # Should generate many queries
        self.assertGreater(len(queries), 100)
        
        # Check for variety of sharding strategies
        has_language = any("language:" in q for q in queries)
        has_created = any("created:" in q for q in queries)
        has_star_range = any(".." in q for q in queries)
        
        self.assertTrue(has_language, "Should have language-based queries")
        self.assertTrue(has_created, "Should have time-based queries")
        self.assertTrue(has_star_range, "Should have star range queries")
    
    def test_query_deduplication(self):
        """Test that queries are deduplicated."""
        queries = QueryGenerator.generate_sharded_queries()
        
        # No duplicates
        self.assertEqual(len(queries), len(set(queries)))
    
    def test_queries_have_minimum_stars(self):
        """Test that all queries have a minimum star threshold."""
        queries = QueryGenerator.generate_sharded_queries()
        
        for query in queries:
            # Should have stars filter
            self.assertTrue(
                "stars:" in query or "stars>=" in query,
                f"Query missing stars filter: {query}"
            )
    
    def test_intersection_queries(self):
        """Test that AI + testing intersection queries are generated."""
        queries = QueryGenerator.generate_sharded_queries()
        
        # Should have queries with both AI and testing keywords
        intersection_queries = [
            q for q in queries 
            if any(ai_kw.lower() in q.lower() for ai_kw in ["chatgpt", "gpt-4", "openai"])
            and any(test_kw.lower() in q.lower() for test_kw in ["test", "pytest", "junit"])
        ]
        
        self.assertGreater(len(intersection_queries), 0, 
                          "Should have AI + testing intersection queries")


if __name__ == "__main__":
    unittest.main()
