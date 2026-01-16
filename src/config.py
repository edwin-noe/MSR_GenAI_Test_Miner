import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    # Only raise exception if actually trying to use the API, not during tests
    import sys
    if "pytest" not in sys.modules and "unittest" not in sys.modules:
        # Allow missing token during test import
        pass

GITHUB_API_URL = "https://api.github.com/search/repositories"
OUTPUT_FILE = "output/validated_repos.csv"
PROGRESS_FILE = "output/progress.txt"

GENAI_KEYWORDS = [
    "GitHub Copilot", "ChatGPT", "GPT-4", "Claude", "Gemini", "OpenAI",
    "CodeLlama", "Codestral", "StarCoder", "Mistral",
    "LangChain", "AutoGPT", "gpt-engineer", "AutoGen", "QWEN",
    "GPT-3.5", "Llama", "Anthropic", "Cohere", "AI21", "Tabnine"
]

TEST_AUTOMATION_KEYWORDS = [
    "Unit Testing", "Integration Testing", "E2E Testing", "Regression Testing",
    "Pytest", "Unittest", "Robot Framework",
    "JUnit", "TestNG", "Selenium", "Cucumber",
    "Jest", "Cypress", "Playwright", "Mocha", "Testing", "Test Generation"
]

INTERSECTION_PHRASES = [
    "AI-generated tests",
    "Copilot generated test",
    "GPT-4 for testing",
    "LLM-based test generation",
    "Automated test case generation",
    "Test oracle creation",
    "Evaluated by LLM",
    "LLM-as-a-judge",
    "AI test generation",
    "ML testing",
    "neural test"
]

REPO_FILES_TO_CHECK = ["README.md", "requirements.txt", "package.json", "pom.xml", "build.gradle", "Gemfile"]
AI_LIBRARIES = ["openai", "langchain", "deepeval", "gemini", "codegen", "autogen", "anthropic", "cohere", "transformers"]

# Languages for targeted search
TARGET_LANGUAGES = ["Python", "Java", "JavaScript", "TypeScript", "Go"]

# Star ranges for sharding to overcome 1000-result limit
STAR_RANGES = [
    (50, 100),
    (100, 200),
    (200, 500),
    (500, 1000),
    (1000, 5000),
    (5000, None)  # None means no upper limit
]

# Time ranges for created date sharding (format: YYYY-MM-DD)
# Start from when GitHub was founded, shard by quarters
TIME_SHARDS = [
    ("2008-01-01", "2015-12-31"),
    ("2016-01-01", "2018-12-31"),
    ("2019-01-01", "2020-12-31"),
    ("2021-01-01", "2021-12-31"),
    ("2022-01-01", "2022-06-30"),
    ("2022-07-01", "2022-12-31"),
    ("2023-01-01", "2023-06-30"),
    ("2023-07-01", "2023-12-31"),
    ("2024-01-01", "2024-06-30"),
    ("2024-07-01", "2025-12-31"),
]
