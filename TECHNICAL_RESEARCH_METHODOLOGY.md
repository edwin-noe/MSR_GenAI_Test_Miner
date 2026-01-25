# Technical Research Methodology: Mining Generative AI-Testing Repositories

## Research Problem Statement

The intersection of Generative Artificial Intelligence (GenAI) and Software Testing represents an emerging domain requiring systematic empirical investigation. Current approaches to identifying relevant repositories suffer from methodological limitations including GitHub's 1,000-result query cap, selection bias toward popular repositories, and insufficient characterization metrics for rigorous analysis.

## Research Objectives

1. **Primary Objective**: Systematically identify and characterize GitHub repositories implementing GenAI-assisted software testing practices.
2. **Secondary Objective**: Establish a reproducible methodology for mining software repositories at the intersection of AI and testing domains.
3. **Tertiary Objective**: Generate a validated dataset suitable for empirical analysis of AI-testing integration patterns.

## Technical Methodology

### 1. Query Generation Architecture

#### 1.1 Multi-Dimensional Query Sharding
To address GitHub's 1,000-result limitation, we implement a sharded query generation system with cross-product computation:

```
Q_total = |AI_keywords| × |Testing_keywords| × |Star_ranges| × |Languages| × |Time_periods|
Q_total ≈ 21 × 17 × 6 × 5 × 10 ≈ 2,916 queries
```

#### 1.2 Query Components
- **AI Keywords (21)**: `{ChatGPT, GPT-4, LLM, OpenAI, Anthropic, ...}`
- **Testing Keywords (17)**: `{pytest, unittest, test automation, CI/CD, ...}`
- **Star Ranges (6)**: `[50-100], [100-200], [200-500], [500-1000], [1000-5000], [5000+]`
- **Languages (5)**: `{Python, Java, JavaScript, TypeScript, Go}`
- **Time Periods (10)**: `{2008-2012, 2013-2015, ..., 2022-2023, 2024-2025}`

#### 1.3 Query Deduplication Algorithm
Hash-based deduplication prevents redundant API calls:
```
query_hash = hash(keyword_combination + star_range + language + time_period)
processed_queries = set()
```

### 2. Data Collection Pipeline

#### 2.1 GitHub API Integration
- **Authentication**: Personal Access Token with `public_repo` and `read:org` scopes
- **Rate Limiting**: 30 requests/minute (search), 5,000 requests/hour (core)
- **Pagination**: Up to 1,000 results per query (100 per page × 10 pages)

#### 2.2 API Call Optimization
- **Exponential Backoff**: 2s → 60s with max 5 retries
- **Proactive Throttling**: Sleep when `< 5` remaining requests
- **Inter-request Delay**: 0.5s between pagination requests

### 3. Repository Characterization Framework

#### 3.1 Multi-Dimensional Metric Collection (30 Characteristics)
Each repository is characterized across 7 dimensions:

**Basic Metrics (5)**:
- `stars_count`: Integer (popularity indicator)
- `forks_count`: Integer (reuse indicator)
- `watchers_count`: Integer (interest metric)
- `open_issues_count`: Integer (activity signal)
- `size_kb`: Integer (repository scale)

**Activity Metrics (5)**:
- `total_commits`: Integer (development intensity)
- `contributor_count`: Integer (collaboration level)
- `days_since_last_commit`: Integer (maintenance status)
- `days_since_creation`: Integer (repository age)
- `commits_per_month`: Float (activity rate)

**Release Metrics (3)**:
- `release_count`: Integer (maturity indicator)
- `days_since_last_release`: Integer (currency)
- `release_frequency`: Float (releases per year)

**Language Metrics (2)**:
- `primary_language`: String (dominant technology)
- `language_distribution`: Dict<String,Float> (top 3 languages)

**Community Metrics (4)**:
- `has_wiki`: Boolean (documentation investment)
- `has_pages`: Boolean (project presence)
- `has_discussions`: Boolean (engagement level)
- `has_topics`: Boolean (discoverability effort)

**Documentation Metrics (3)**:
- `readme_length`: Integer (documentation quality proxy)
- `has_contributing_guide`: Boolean (contributor-friendliness)
- `has_code_of_conduct`: Boolean (governance)

**Testing Indicators (2)**:
- `has_test_directory`: Boolean (infrastructure presence)
- `has_ci_config`: Boolean (automation maturity)

**AI/Testing Intersection (3)**:
- `ai_dependencies_count`: Integer (direct integration)
- `ai_keyword_frequency`: Integer (focus intensity)
- `testing_keyword_frequency`: Integer (focus intensity)

**Quality Indicators (3)**:
- `has_license`: Boolean (legal clarity)
- `has_description`: Boolean (basic documentation)
- `intersection_phrase_count`: Integer (research relevance)

#### 3.2 Characterization Algorithm
```
def enrich_repository(repo_data):
    characteristics = {}
    
    # Basic metrics from GitHub API
    characteristics.update(extract_basic_metrics(repo_data))
    
    # Activity metrics via commits API
    characteristics.update(fetch_activity_metrics(repo_data.full_name))
    
    # Release metrics via releases API
    characteristics.update(fetch_release_metrics(repo_data.full_name))
    
    # File structure analysis via contents API
    characteristics.update(analyze_file_structure(repo_data.full_name))
    
    # Content analysis via README and configuration files
    characteristics.update(analyze_readme_content(repo_data.full_name))
    
    return characteristics
```

### 4. Multi-Stage Filtering Pipeline

#### 4.1 Stage 1: Basic Validation
```
filter_stage_1(repo) = (
    repo.stars >= 50 AND
    repo.description IS NOT NULL AND
    repo.archived == False
)
```

#### 4.2 Stage 2: Content Analysis
```
filter_stage_2(repo) = (
    len(repo.readme_content) >= 100 AND
    (count_ai_signals(repo) >= 1 OR count_testing_signals(repo) >= 1) AND
    (
        count_intersection_phrases(repo) >= 1 OR
        (count_ai_signals(repo) >= 2 AND count_testing_signals(repo) >= 1)
    )
)
```

#### 4.3 Stage 3: Activity Validation
```
filter_stage_3(repo) = (
    days_since(repo.last_push) <= 730 AND
    repo.total_commits > 0 AND
    repo.contributor_count > 0
)
```

#### 4.4 Stage 4: Quality Scoring
Composite score calculation (0-30 points):
```
quality_score = popularity_score(0-5) + 
                activity_score(0-5) + 
                community_score(0-5) + 
                documentation_score(0-5) + 
                ai_testing_score(0-10)

accept_repo = quality_score >= 10
```

### 5. Quality Assurance Mechanisms

#### 5.1 Deduplication Strategy
Repository deduplication based on `full_name` (owner/repository) to prevent duplicate processing across sharded queries.

#### 5.2 Validation Criteria
- **Minimum Threshold**: Quality score ≥ 10
- **Completeness**: All 30 characteristics populated
- **Activity**: Pushed within last 2 years
- **Documentation**: README length ≥ 100 characters

### 6. Reproducibility Framework

#### 6.1 Deterministic Execution
- Fixed query ordering to ensure reproducible results
- Checkpoint persistence after each query completion
- Progress tracking with query index preservation

#### 6.2 Output Serialization
- **CSV Format**: Tabular data for statistical analysis
- **JSON Format**: Full fidelity with nested structures
- **Log Format**: Execution provenance with timestamps

#### 6.3 Resume Capability
Graceful interruption handling with automatic resumption from last completed query index.

### 7. Threats to Validity

#### 7.1 Construct Validity
- **Threat**: Keyword-based detection may miss repositories using non-standard terminology
- **Mitigation**: Comprehensive keyword lists validated against known repositories

#### 7.2 Internal Validity
- **Threat**: GitHub's proprietary search algorithm may introduce selection bias
- **Mitigation**: Multi-dimensional sharding reduces bias across popularity, time, and language dimensions

#### 7.3 External Validity
- **Threat**: Results limited to public GitHub repositories
- **Mitigation**: Clear scoping with documented limitations

#### 7.4 Reliability
- **Threat**: API rate limits and network issues may cause incomplete collection
- **Mitigation**: Comprehensive retry logic and checkpointing

### 8. Implementation Architecture

#### 8.1 Component Design
- `QueryGenerator`: Multi-dimensional sharding algorithm
- `GitHubMiner`: API client with rate limiting and pagination
- `RepoEnricher`: 30-characteristic extraction engine
- `RepoFilter`: Multi-stage filtering with quality scoring
- `MinerApp`: Workflow orchestration and state management

#### 8.2 Technology Stack
- **Language**: Python 3.8+
- **API Client**: requests library with async support
- **Data Processing**: pandas for CSV/JSON serialization
- **Configuration**: Environment variables and config files

### 9. Expected Dataset Properties

#### 9.1 Scale Estimation
- **Query Volume**: ~2,916 sharded queries
- **Expected Repositories**: Thousands of repositories (dependent on API results)
- **Characteristics per Repository**: 30 metrics across 7 dimensions

#### 9.2 Data Quality Targets
- **Completeness**: 100% of 30 characteristics populated
- **Accuracy**: Multi-stage validation with quality scoring
- **Reproducibility**: Deterministic execution with provenance logging

### 10. Validation Protocol

#### 10.1 Unit Testing
- **Coverage**: 29 unit tests across all components
- **Areas**: Query generation, filtering logic, characteristic extraction
- **Target**: 100% test pass rate

#### 10.2 Output Validation
- **Format Compliance**: CSV/JSON schema validation
- **Statistical Checks**: Range validation for numeric metrics
- **Completeness Verification**: Mandatory field presence

This methodology ensures systematic, reproducible, and high-quality data collection for empirical analysis of GenAI-testing intersections in open-source software repositories.