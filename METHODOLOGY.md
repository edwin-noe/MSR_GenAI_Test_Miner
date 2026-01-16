# MSR GenAI Test Miner: Methodology & Academic Documentation

## Overview

This document provides comprehensive documentation of the methodology, design decisions, and threats to validity for the MSR GenAI Test Miner system. This system is designed to meet publication standards for Mining Software Repositories (MSR), International Conference on Software Engineering (ICSE), and related academic venues.

## Research Objective

**Primary Goal**: Discover and characterize GitHub repositories at the intersection of:
1. Generative AI technologies (LLMs, code generation tools)
2. Software testing and test automation

**Research Questions Supported**:
- RQ1: What is the landscape of AI-augmented testing tools and practices?
- RQ2: How are developers integrating generative AI into test automation workflows?
- RQ3: What characteristics distinguish high-quality AI-testing repositories?

## Methodology

### 1. Query Generation Strategy

**Challenge**: GitHub Search API limits results to 1,000 per query, introducing selection bias toward highly-starred repositories and truncating result sets.

**Solution**: Multi-dimensional query sharding to achieve comprehensive coverage:

1. **Keyword Intersection Sharding**
   - Cross-product of AI keywords (21 terms) × Testing keywords (17 terms)
   - Captures repositories explicitly discussing both domains
   - Example: `"ChatGPT" "Pytest" stars:50..100`

2. **Star Range Sharding**
   - Partition repositories into 6 star ranges: [50-100], [100-200], [200-500], [500-1000], [1000-5000], [5000+]
   - Ensures representation across popularity spectrum
   - Mitigates bias toward highly-starred repositories

3. **Language-Specific Sharding**
   - Separate queries for 5 primary languages: Python, Java, JavaScript, TypeScript, Go
   - Captures language-specific testing practices
   - Example: `"OpenAI" language:Python stars:100..200`

4. **Temporal Sharding**
   - Partition by creation date across 10 time periods (2008-2025)
   - Captures evolution of AI-testing practices
   - Recent periods (2022+) subdivided by semester for granularity
   - Example: `"GPT-4" created:2023-01-01..2023-06-30 stars:>=50`

5. **Intersection Phrase Targeting**
   - Direct queries for high-precision phrases like "AI-generated tests", "LLM test generation"
   - Highest precision for research relevance
   - Example: `"AI-generated tests" stars:50..100`

**Query Deduplication**: Hash-based deduplication ensures no redundant API calls.

**Estimated Coverage**: ~2,500-4,000 unique queries depending on keyword combinations, capable of discovering repositories that would be truncated in simple searches.

### 2. Repository Enrichment (30 Characteristics)

Each discovered repository is enriched with 30 distinct characteristics across 7 dimensions:

#### Basic Metrics (5 characteristics)
1. **Stars count**: Popularity indicator
2. **Forks count**: Reuse/derivative work indicator
3. **Watchers count**: Community interest
4. **Open issues count**: Active development signal
5. **Repository size (KB)**: Codebase scale

#### Activity Metrics (5 characteristics)
6. **Total commit count**: Development intensity
7. **Contributor count**: Collaboration level
8. **Days since last commit**: Maintenance status
9. **Days since creation**: Repository age
10. **Commits per month**: Activity rate

#### Release Metrics (3 characteristics)
11. **Total release count**: Maturity indicator
12. **Days since last release**: Release currency
13. **Release frequency (releases/year)**: Release cadence

#### Language Metrics (2 characteristics)
14. **Primary language**: Dominant technology
15. **Language distribution (top 3)**: Polyglot nature

#### Community Metrics (4 characteristics)
16. **Has wiki**: Documentation investment
17. **Has GitHub pages**: Project website presence
18. **Has discussions enabled**: Community engagement
19. **Has topics/tags**: Discoverability effort

#### Documentation Metrics (3 characteristics)
20. **README length**: Documentation quality proxy
21. **Has contributing guide**: Contributor-friendliness
22. **Has code of conduct**: Community governance

#### Testing Indicators (2 characteristics)
23. **Has test directory**: Test infrastructure presence
24. **Has CI/CD configuration**: Automation maturity

#### AI/Testing Intersection (3 characteristics)
25. **AI library dependencies count**: Direct AI integration
26. **AI keyword frequency in README**: AI focus intensity
27. **Testing keyword frequency in README**: Testing focus intensity

#### Quality Indicators (3 characteristics)
28. **Has license**: Legal clarity
29. **Has description**: Basic documentation
30. **Intersection phrase count**: Research relevance signal

### 3. Multi-Stage Filtering Pipeline

**Stage 1: Basic Validation**
- Minimum 50 stars (quality floor)
- Has description (basic documentation)
- Not archived (active development)
- **Rationale**: Eliminate low-quality, abandoned, or undocumented repositories

**Stage 2: Content Analysis**
- README length >= 100 characters (minimal documentation)
- AI signals: AI keywords + dependencies >= 1
- Testing signals: Test keywords + test directory + CI/CD >= 1
- Intersection: Either explicit intersection phrases OR (AI signals >= 2 AND test signals >= 1)
- **Rationale**: Ensure repositories genuinely relate to AI-testing intersection

**Stage 3: Activity Validation**
- Pushed within last 2 years (730 days)
- Has commits (not empty repository)
- Has contributors (not abandoned)
- **Rationale**: Focus on maintained, active repositories

**Stage 4: Quality Scoring (0-30 points)**

Composite score balancing multiple dimensions:

- **Popularity (0-5)**: Stars thresholds (100, 500, 1K, 5K, 10K)
- **Activity (0-5)**: Recent push (30d, 90d, 365d) + commits/month
- **Community (0-5)**: Contributors + discussions + issues + topics
- **Documentation (0-5)**: README length + guides + license + CoC
- **AI/Testing Signals (0-10)**: Intersection phrases + keywords + dependencies + test infrastructure

**Acceptance Threshold**: Quality score >= 10 (ensures multi-dimensional quality)

### 4. Reproducibility Features

**Deterministic Execution**:
- Queries executed in fixed order
- Deduplication based on repository full name
- Progress checkpointing after every query
- Results sorted by quality score then stars

**Comprehensive Logging**:
- Session timestamps in ISO 8601 format
- Query execution log with timestamps
- Error tracking with context
- API rate limit monitoring

**Output Formats**:
- CSV: Structured tabular data
- JSON: Full fidelity with nested structures
- Log file: Execution provenance

**Resumption Support**:
- Progress file tracks last completed query index
- Results file loaded on restart
- Graceful interrupt handling (Ctrl+C)
- Incremental saves prevent data loss

### 5. Rate Limit Management

**GitHub API Quotas**:
- Search API: 30 requests/minute (authenticated)
- Core API: 5,000 requests/hour (authenticated)

**Strategies**:
- Exponential backoff with retry (2s to 60s)
- Proactive rate limit checking
- Sleep before hitting limits (< 5 remaining)
- Respect reset timestamps from headers
- 0.5s delay between pagination requests

**Estimation**: Full mining with enrichment may require 8-24 hours depending on result volume and API conditions.

## Threats to Validity

### Construct Validity

**Threat**: Selected characteristics may not accurately capture repository quality or research relevance.

**Mitigation**:
- 30 characteristics span 7 validated dimensions (prior MSR research)
- Multi-stage filtering reduces false positives
- Quality scoring balances popularity bias with content signals
- Intersection phrases provide high-precision targeting

**Residual Risk**: Keyword-based detection may miss repositories using non-standard terminology.

### Internal Validity

**Threat**: GitHub Search API ranking and truncation may introduce selection bias.

**Mitigation**:
- Query sharding overcomes 1,000-result limit
- Star range sharding ensures low-popularity repositories included
- Temporal sharding captures evolution over time
- Language sharding prevents single-language bias

**Residual Risk**: GitHub's proprietary search algorithm may still influence discovery.

### External Validity

**Threat**: Results may not generalize beyond GitHub or to private repositories.

**Mitigation**:
- Focus explicitly on public GitHub repositories (clearly scoped)
- Documented methodology enables replication on other platforms
- Large sample size (thousands of repositories expected) improves generalizability

**Residual Risk**: Private/enterprise repositories not captured; findings limited to open-source context.

### Reliability

**Threat**: API rate limits and network issues may cause incomplete data collection.

**Mitigation**:
- Retry logic with exponential backoff
- Progress checkpointing and resumption
- Comprehensive error logging
- Rate limit prediction and throttling

**Residual Risk**: Transient API outages may still interrupt execution.

## Comparison to Related Work

| Feature | This System | Typical MSR Study |
|---------|-------------|-------------------|
| Query strategy | Sharded (2,500-4K queries) | Simple (10-50 queries) |
| Result limit handling | Star/time/language sharding | Accept 1,000-result cap |
| Characteristics | 30 metrics across 7 dimensions | 5-15 metrics |
| Filtering | Multi-stage with quality scoring | Single-stage keyword |
| Reproducibility | Checkpointing + logging + deterministic | Best effort |
| Rate limit handling | Proactive + predictive | Reactive retry |

## Usage Recommendations

### For High Precision (Academic Publication)
```bash
python -m src.main  # Full enrichment with sharded queries
```
- Use when: Preparing dataset for publication
- Time: 8-24 hours
- Output: High-quality, well-characterized repositories

### For Exploratory Analysis
```bash
python -m src.main --no-enrich  # Sharded queries, basic filtering
```
- Use when: Initial exploration or API quota limited
- Time: 2-4 hours
- Output: Broader set with basic metrics

### For Quick Testing
```bash
python -m src.main --simple  # Simple queries, no enrichment
```
- Use when: Testing setup or limited time
- Time: 15-30 minutes
- Output: Small sample for validation

## Data Collection Protocol

1. **Pre-execution**:
   - Verify GitHub token validity
   - Check rate limit status: `python -m src.main --check-rate-limit`
   - Clear output directory if fresh start desired

2. **Execution**:
   - Run with appropriate mode (see above)
   - Monitor progress in console output
   - Check `output/mining_log.txt` for errors

3. **Interruption Handling**:
   - Use Ctrl+C for graceful stop (saves progress)
   - Resume with same command (loads from checkpoint)

4. **Post-execution**:
   - Validate output files exist: `output/validated_repos.csv`, `output/validated_repos.json`
   - Review quality statistics in console output
   - Analyze `output/mining_log.txt` for warnings

## Ethical Considerations

- **Public Data Only**: Uses only publicly available GitHub repositories
- **Rate Limiting**: Respects GitHub API limits and terms of service
- **No Scraping**: Uses official GitHub APIs exclusively
- **Attribution**: Repository URLs preserved for proper citation
- **Privacy**: No personal data collected beyond public repository metadata

## Future Enhancements

1. **Additional Characteristics**:
   - Code complexity metrics (cyclomatic complexity)
   - Test coverage statistics (if available)
   - Dependency graph analysis
   - Commit message sentiment analysis

2. **Advanced Filtering**:
   - Machine learning-based relevance classification
   - Manual validation sample for precision/recall estimation
   - Active learning for threshold optimization

3. **Scalability**:
   - Parallel query execution (respecting rate limits)
   - Distributed execution across multiple tokens
   - Incremental updates for longitudinal studies

4. **Validation**:
   - Inter-rater reliability for manual validation
   - Comparison with expert-curated datasets
   - Cross-platform validation (GitLab, Bitbucket)

## References

- GitHub Search API: https://docs.github.com/en/rest/search
- MSR Best Practices: Munaiah et al., "Curating GitHub for Engineered Software Projects" (2017)
- Replication Packages: Rodríguez-Pérez et al., "Reproducibility in MSR" (2018)

## Contact

For questions about methodology or replication:
- Repository: https://github.com/edwin-noe/MSR_GenAI_Test_Miner
- Issues: https://github.com/edwin-noe/MSR_GenAI_Test_Miner/issues
