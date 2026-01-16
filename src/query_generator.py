from .config import (
    GENAI_KEYWORDS, TEST_AUTOMATION_KEYWORDS, INTERSECTION_PHRASES,
    TARGET_LANGUAGES, STAR_RANGES, TIME_SHARDS
)

class QueryGenerator:
    @staticmethod
    def generate_sharded_queries():
        """
        Generate comprehensive sharded queries to overcome GitHub's 1,000-result limit.
        
        Sharding strategy:
        1. AI keywords × Test keywords for intersection
        2. Language-specific queries
        3. Star range sharding
        4. Time-based sharding for active periods
        
        Returns:
            List of query strings optimized for completeness and minimal duplication
        """
        queries = []
        seen_queries = set()  # Deduplication
        
        # Strategy 1: High-precision intersection queries (AI + Testing)
        for ai_keyword in GENAI_KEYWORDS:
            for test_keyword in TEST_AUTOMATION_KEYWORDS:
                # Base query with both keywords
                base = f'"{ai_keyword}" "{test_keyword}"'
                
                # Shard by star ranges to overcome 1000-result limit
                for star_min, star_max in STAR_RANGES:
                    if star_max:
                        star_filter = f"stars:{star_min}..{star_max}"
                    else:
                        star_filter = f"stars:>={star_min}"
                    
                    query = f"{base} {star_filter}"
                    if query not in seen_queries:
                        queries.append(query)
                        seen_queries.add(query)
        
        # Strategy 2: Language-specific queries for each AI keyword
        for ai_keyword in GENAI_KEYWORDS:
            for language in TARGET_LANGUAGES:
                for star_min, star_max in STAR_RANGES:
                    if star_max:
                        star_filter = f"stars:{star_min}..{star_max}"
                    else:
                        star_filter = f"stars:>={star_min}"
                    
                    query = f'"{ai_keyword}" language:{language} {star_filter}'
                    if query not in seen_queries:
                        queries.append(query)
                        seen_queries.add(query)
        
        # Strategy 3: Intersection phrases (high precision for recent repos)
        for phrase in INTERSECTION_PHRASES:
            for star_min, star_max in STAR_RANGES[:4]:  # Focus on lower star ranges
                if star_max:
                    star_filter = f"stars:{star_min}..{star_max}"
                else:
                    star_filter = f"stars:>={star_min}"
                
                query = f'"{phrase}" {star_filter}'
                if query not in seen_queries:
                    queries.append(query)
                    seen_queries.add(query)
        
        # Strategy 4: Time-based sharding for popular AI keywords (reduce bias toward older repos)
        for ai_keyword in GENAI_KEYWORDS[:10]:  # Top 10 most relevant
            for start_date, end_date in TIME_SHARDS:
                query = f'"{ai_keyword}" created:{start_date}..{end_date} stars:>=50'
                if query not in seen_queries:
                    queries.append(query)
                    seen_queries.add(query)
        
        return queries
    
    @staticmethod
    def generate_simple_queries():
        """
        Generate simple queries for quick testing or initial exploration.
        """
        queries = []
        for ai_keyword in GENAI_KEYWORDS:
            queries.append(f'"{ai_keyword}" stars:>=50')
        return queries
