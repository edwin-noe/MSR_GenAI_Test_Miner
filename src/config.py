import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise Exception("GITHUB_TOKEN not found! Add it to your .env file.")

GITHUB_API_URL = "https://api.github.com/search/repositories"
OUTPUT_FILE = "output/validated_repos.csv"
PROGRESS_FILE = "output/progress.txt"

GENAI_KEYWORDS = [
    "GitHub Copilot", "ChatGPT", "GPT-4", "Claude", "Gemini", "OpenAI",
    "CodeLlama", "Codestral", "StarCoder", "Mistral",
    "LangChain", "AutoGPT", "gpt-engineer", "AutoGen" , "QWEN"
]

# TEST_AUTOMATION_KEYWORDS = [
#     "Unit Testing", "Integration Testing", "E2E Testing", "Regression Testing",
#     "Pytest", "Unittest", "Robot Framework",
#     "JUnit", "TestNG", "Selenium", "Cucumber",
#     "Jest", "Cypress", "Playwright", "Mocha"
# ]
#
# INTERSECTION_PHRASES = [
#     "AI-generated tests",
#     "Copilot generated test",
#     "GPT-4 for testing",
#     "LLM-based test generation",
#     "Automated test case generation",
#     "Test oracle creation",
#     "Evaluated by LLM",
#     "LLM-as-a-judge"
# ]
#
# REPO_FILES_TO_CHECK = ["README.md", "requirements.txt", "package.json", "pom.xml"]
# AI_LIBRARIES = ["openai", "langchain", "deepeval", "gemini", "codegen", "autogen"]
