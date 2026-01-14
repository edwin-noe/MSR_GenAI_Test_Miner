from .config import GENAI_KEYWORDS
# from config import GENAI_KEYWORDS, TEST_AUTOMATION_KEYWORDS, INTERSECTION_PHRASES

class QueryGenerator:
    @staticmethod
    # def generate_sharded_queries():
    #     queries = []
    #     for genai in GENAI_KEYWORDS:
    #         for test in TEST_AUTOMATION_KEYWORDS:
    #             base = f'"{genai}" "{test}" stars:>=50'
    #             # intersection phrases
    #             for phrase in INTERSECTION_PHRASES:
    #                 queries.append(f'{base} "{phrase}"')
    #             # path/filename/extension filters
    #             queries.append(f'{base} path:**/tests/')
    #             queries.append(f'{base} filename:test_')
    #             queries.append(f'{base} extension:py')
    #             queries.append(f'{base} extension:java')
    #             queries.append(f'{base} extension:js')
    def generate_queries():
        queries = [f'"{ai}" stars:>50' for ai in GENAI_KEYWORDS]
        return queries
