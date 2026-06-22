import os
from dotenv import load_dotenv

load_dotenv()

# Taxonomy version — bump this whenever keywords are changed so every mining
# run can be traced back to the exact keyword set used.
TAXONOMY_VERSION = "v2.1"
TAXONOMY_DATE    = "2026-06-11"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Validate token is present (allow missing during test imports)
if not GITHUB_TOKEN:
    import sys
    # Only raise exception if not in test context
    if "pytest" not in sys.modules and "unittest" not in sys.modules:
        # Check if we're actually trying to use the miner (not just importing)
        if any(arg in sys.argv for arg in ["src.main", "-m", "miner_app"]):
            raise Exception("GITHUB_TOKEN not found! Add it to your .env file.")

GITHUB_API_URL = "https://api.github.com/search/repositories"
OUTPUT_FILE = "output/validated_repos.csv"
PROGRESS_FILE = "output/progress.txt"

# ── GenAI keyword taxonomy (SAGA detection — prose-level) ─────────────────────
# These are terms developers write in natural language (READMEs, commit messages,
# code comments). NOT API model-ID strings (those are caught via AI_LIBRARIES).
# Design principle: brand-level terms (Claude, Llama) catch all versions;
# version-specific terms (Llama-2, GPT-4o) are added where developers commonly
# cite them by name in prose. Keep BOTH for full 2021–2026 corpus coverage.
GENAI_KEYWORDS = [
    # ── Anthropic ──────────────────────────────────────────────────────────────
    "Claude",           # brand-level catch-all (Claude 2/3/3.5/4/Code)
    "Anthropic",        # org-level, catches API and tool references
    "Claude Code",      # Anthropic's CLI coding agent (2025–2026)

    # ── OpenAI ─────────────────────────────────────────────────────────────────
    "ChatGPT",          # product name, widely used in prose
    "OpenAI",           # org-level catch-all
    "GPT-4",            # dominant 2023–2024 citation
    "GPT-4o",           # replaced GPT-4 as primary model mid-2024 onward
    "GPT-3.5",          # still cited in pre-2024 repos
    "GPT-5",            # 2025 release; appearing in recent repos
    "o1-mini",          # OpenAI reasoning model — more specific than bare "o1"
    "o3-mini",          # OpenAI reasoning model

    # ── Google ─────────────────────────────────────────────────────────────────
    "Gemini",           # brand-level (Gemini Pro, Flash, 2.0, 2.5)
    "Bard",             # legacy name; still in pre-2024 repos

    # ── Meta / Llama ───────────────────────────────────────────────────────────
    "Llama",            # brand-level catch-all
    "CodeLlama",        # code-focused variant, widely cited
    "Llama-2",          # heavily cited specific version
    "Llama 3",          # current generation (3.1, 3.2, 3.3)

    # ── Mistral AI ─────────────────────────────────────────────────────────────
    "Mistral",          # brand-level
    "Codestral",        # Mistral's code model
    "Mixtral",          # Mixture-of-Experts variant, frequently named separately

    # ── DeepSeek ───────────────────────────────────────────────────────────────
    "DeepSeek",         # brand-level (R1, V3, Coder) — critical gap in v1

    # ── Alibaba / Qwen ─────────────────────────────────────────────────────────
    "Qwen",             # consolidated from "QWEN"+"Qwen" — GitHub search is
                        # case-insensitive so both returned identical results;
                        # covers Qwen 2.5 Coder and all Qwen variants

    # ── Moonshot AI / Kimi ─────────────────────────────────────────────────────
    "Kimi",             # Moonshot AI's product; notable long-context/reasoning
                        # adoption in 2024–2025; paired queries mitigate
                        # false-positive risk from the short name

    # ── AI Coding Agents & IDEs ────────────────────────────────────────────────
    "GitHub Copilot",   # full product name
    "Copilot",          # short form — many repos omit "GitHub"
    "Cursor",           # dominant AI IDE 2024–2026; leaves .cursorrules artifacts
    "Aider",            # popular CLI coding agent; leaves commit trailers
    "LangChain",        # orchestration framework
    "AutoGPT",          # early autonomous agent
    "AutoGen",          # Microsoft multi-agent framework
    "gpt-engineer",     # CLI coding agent

    # ── Other ──────────────────────────────────────────────────────────────────
    "StarCoder",        # BigCode code model (StarCoder2 also caught by this)
    "Tabnine",          # AI code completion
    "Cohere",           # enterprise LLM provider
    "AI21",             # Jurassic/Jamba model family
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
    "GPT-4o for testing",
    "DeepSeek for testing",
    "LLM-based test generation",
    "Automated test case generation",
    "Test oracle creation",
    "Evaluated by LLM",
    "LLM-as-a-judge",
    "AI test generation",
    "ML testing",
    "neural test",
    "AI-assisted testing",
    "generated by Cursor",
    "generated by Aider",
]

REPO_FILES_TO_CHECK = [
    "README.md", "requirements.txt", "package.json", "pom.xml",
    "build.gradle", "Gemfile", "go.mod", "pyproject.toml",
]

# Dependency-level detection (requirements.txt, package.json, pom.xml etc.)
# These are pip/npm/maven package names, NOT natural-language prose terms.
AI_LIBRARIES = [
    # OpenAI / Anthropic / Google
    "openai",
    "anthropic",
    "google-generativeai",  # Gemini Python SDK (was incorrectly "gemini" in v1)
    "gemini",               # kept as fallback for repos that import it differently

    # Open-source model frameworks
    "transformers",         # HuggingFace
    "huggingface-hub",      # HuggingFace Hub client
    "llama-index",          # LlamaIndex / LlamaCloud
    "deepseek",             # DeepSeek API client

    # Orchestration / agent frameworks
    "langchain",
    "autogen",
    "crewai",
    "litellm",              # unified LLM API — indicates multi-model usage

    # Testing-specific AI libraries
    "deepeval",             # LLM evaluation / test framework
    "codegen",
    "cohere",

    # Moonshot AI / Kimi
    "moonshot",             # Kimi API Python client (pip install moonshot)
]

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
# 2024-07-01–2025-12-31 was a single 18-month shard in v1 — too coarse for the
# highest-volume GenAI adoption period and missed 2026 entirely. Now split into
# H2-2024, H1-2025, H2-2025, and H1-2026.
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
    ("2024-07-01", "2024-12-31"),   # split: H2 2024 (GPT-4o era begins)
    ("2025-01-01", "2025-06-30"),   # split: H1 2025 (DeepSeek-R1 release)
    ("2025-07-01", "2025-12-31"),   # split: H2 2025
    ("2026-01-01", "2026-06-30"),   # NEW:   H1 2026 (current period)
]
