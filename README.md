# MSR GenAI Test Miner

A research-grade GitHub mining system for discovering and analyzing repositories at the intersection of Generative AI and Software Testing.

## Overview

This tool implements a comprehensive methodology for Mining Software Repositories (MSR) with:

- **Sharded query generation** to overcome GitHub's 1,000-result limit
- **30 repository characteristics** across 7 dimensions for high-precision analysis
- **Multi-stage filtering pipeline** to reduce false positives
- **Reproducible execution** with checkpointing and comprehensive logging
- **Academic rigor** aligned with MSR/ICSE publication standards

## Project Workflow

```
┌─────────────────────┐
│  Query Generation   │  Sharded queries (2,500-4K)
│  (Overcoming 1K     │  - Star ranges
│   result limit)     │  - Time periods
└──────────┬──────────┘  - Languages
           │             - AI × Testing keywords
           v
┌─────────────────────┐
│  GitHub Search API  │  Discover repositories
│  with Pagination    │  - Rate limit handling
└──────────┬──────────┘  - Retry logic
           │
           v
┌─────────────────────┐
│ Repository          │  30 characteristics:
│ Enrichment          │  - Activity metrics
│                     │  - Community signals
└──────────┬──────────┘  - Testing indicators
           │             - AI integration
           v
┌─────────────────────┐
│ Multi-Stage         │  High-precision filtering:
│ Filtering           │  - Basic validation
│                     │  - Content analysis
└──────────┬──────────┘  - Activity validation
           │             - Quality scoring
           v
┌─────────────────────┐
│ Output              │  CSV + JSON + Logs
│ (Research Dataset)  │  - Deduplicated
└─────────────────────┘  - Scored & Sorted
```

## Requirements

- Python 3.8+
- [Docker](https://www.docker.com/get-started) (optional but recommended)
- GitHub Personal Access Token (required for authenticated API access)
  - Create at: https://github.com/settings/tokens
  - Required scopes: `public_repo`, `read:org`

## Installation

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/edwin-noe/MSR_GenAI_Test_Miner.git
cd MSR_GenAI_Test_Miner

# Build Docker image
docker build -t msr_genai_test_miner .

# Run with your GitHub token
docker run --rm -it \
  -v $(pwd)/output:/app/output \
  -e GITHUB_TOKEN="your_token_here" \
  msr_genai_test_miner
```

### Option 2: Local Python

```bash
# Clone repository
git clone https://github.com/edwin-noe/MSR_GenAI_Test_Miner.git
cd MSR_GenAI_Test_Miner

# Install dependencies
pip install -r requirements.txt

# Create .env file with your token
echo "GITHUB_TOKEN=your_token_here" > .env

# Run the miner
python -m src.main
```

## Usage Modes

### Full Mining (High Precision for Publication)

```bash
python -m src.main
```

- **Queries**: Sharded (~2,500-4,000 queries)
- **Enrichment**: Full (30 characteristics per repo)
- **Filtering**: Multi-stage with quality scoring
- **Time**: 8-24 hours
- **Use case**: Academic research, publication datasets

### Exploratory Mining

```bash
python -m src.main --no-enrich
```

- **Queries**: Sharded (~2,500-4,000 queries)
- **Enrichment**: Basic only (5 characteristics)
- **Filtering**: Simple validation
- **Time**: 2-4 hours
- **Use case**: Initial exploration, API quota conservation

### Quick Testing

```bash
python -m src.main --simple
```

- **Queries**: Simple (~21 queries)
- **Enrichment**: None
- **Filtering**: Minimal
- **Time**: 15-30 minutes
- **Use case**: System validation, quick tests

### Check Rate Limit Status

```bash
python -m src.main --check-rate-limit
```

## Running on Railway (job dispatcher)

Deploying the service **does not auto-run any job**. The container idles until you
explicitly select a job, so simply re-deploying or waking the service will *not*
re-launch a long mining run. A completion sentinel in the output volume also
prevents a restart from re-running a job that already finished.

Select a job with the `RUN_JOB` environment variable (Railway → service → Variables),
then deploy/restart:

| `RUN_JOB` value  | Runs |
|------------------|------|
| _unset_ / `idle` | nothing — container idles, ready to inspect |
| `mine`           | `python -m src.main` (Phase 1 mining) |
| `phase2`         | Phase 2 validation **+ Stage B** README language gate |
| `phase2-stage-a` | Phase 2 validation, Stage A only (no API calls) |

Other variables:
- `GITHUB_TOKEN` — required for `mine` and `phase2` (Stage B). **Never commit it.**
- `FORCE_RERUN=1` — re-run a job whose completion sentinel already exists.
- `PHASE1_CSV` — Phase 2 input (default `output/validated_repos.csv`, the miner's output).
- `PHASE2_DIR` — Phase 2 output dir (default `output/phase2`).

**Rate limits are waited out, not failed.** When GitHub's quota is exhausted, both
the miner and the Phase 2 Stage B fetcher sleep until the limit resets and then
retry, so long jobs survive quota exhaustion unattended.

Attach a Railway **Volume** at `/app/output` so results (and the resume
checkpoints) persist across restarts.

### Phase 2 validation locally

```bash
python scripts/phase2_validation.py            # Stage A only (no token needed)
python scripts/phase2_validation.py --stage-b  # + README language gate (needs GITHUB_TOKEN)
```

## Output Files

All outputs are saved to the `output/` directory:

- **`validated_repos.csv`**: Main results in CSV format
  - Deduplicated by repository
  - Sorted by quality score and stars
  - Contains all 30 characteristics

- **`validated_repos.json`**: Full-fidelity JSON format
  - Nested structures preserved
  - Timestamps in ISO 8601 format
  - Complete provenance

- **`mining_log.txt`**: Execution log
  - Session timestamps
  - Query execution trace
  - Error messages with context
  - Progress checkpoints

- **`progress.txt`**: Checkpoint file
  - Last completed query index
  - Enables resumption after interruption

## Resuming Interrupted Execution

The system automatically resumes from the last checkpoint:

```bash
# Start mining
python -m src.main

# Press Ctrl+C to interrupt (saves progress)
^C
⏸️ Interrupted! Saving current progress...
💾 Saved 1,234 unique repos

# Resume (automatically loads checkpoint)
python -m src.main
🚀 Starting mining from query 456/3,456
```

## Repository Characteristics (30 Total)

### Basic Metrics (5)
1. Stars count
2. Forks count
3. Watchers count
4. Open issues count
5. Repository size

### Activity Metrics (5)
6. Total commit count
7. Contributor count
8. Days since last commit
9. Days since creation
10. Commits per month

### Release Metrics (3)
11. Total release count
12. Days since last release
13. Release frequency

### Language Metrics (2)
14. Primary language
15. Language distribution

### Community Metrics (4)
16. Has wiki
17. Has GitHub pages
18. Has discussions
19. Has topics/tags

### Documentation (3)
20. README length
21. Has contributing guide
22. Has code of conduct

### Testing Indicators (2)
23. Has test directory
24. Has CI/CD config

### AI/Testing Intersection (3)
25. AI library dependencies
26. AI keyword frequency
27. Testing keyword frequency

### Quality Indicators (3)
28. Has license
29. Has description
30. Quality score (composite 0-30)

## Methodology

For detailed methodology, threats to validity, and academic documentation, see:

📄 **[METHODOLOGY.md](METHODOLOGY.md)**

Key highlights:
- Query sharding strategy to overcome 1,000-result limit
- Multi-dimensional filtering for high precision
- Reproducibility and determinism features
- Threats to validity and mitigation strategies

## Example Output

```csv
full_name,stars,quality_score,ai_keyword_count,test_keyword_count,has_test_directory
microsoft/playwright,50000,28.5,45,123,true
pytest-dev/pytest-gpt,2500,26.0,78,234,true
openai/openai-cookbook,25000,24.5,156,67,false
...
```

## Configuration

Edit `src/config.py` to customize:

- **AI Keywords**: Generative AI tools and models
- **Testing Keywords**: Testing frameworks and practices
- **Star Ranges**: For query sharding
- **Time Shards**: For temporal analysis
- **Filtering Thresholds**: Minimum stars, README length, etc.

## Performance

| Mode | Queries | API Calls | Estimated Time |
|------|---------|-----------|----------------|
| Full | ~3,000 | ~15,000 | 8-24 hours |
| No Enrich | ~3,000 | ~3,000 | 2-4 hours |
| Simple | ~21 | ~21 | 15-30 min |

**Note**: Actual time depends on result volume and API rate limits.

## Troubleshooting

### Rate Limit Errors

```bash
# Check current rate limit status
python -m src.main --check-rate-limit

# If limited, wait or use multiple tokens (not recommended for reproducibility)
```

### Empty Results

- Verify GitHub token is valid and has required scopes
- Check `output/mining_log.txt` for errors
- Try `--simple` mode first to validate setup

### Memory Issues

- System uses in-memory caching for API responses
- For very large datasets (>10K repos), consider periodic restarts

## Contributing

We welcome contributions! Areas for enhancement:

1. **Additional Characteristics**: Code complexity, test coverage
2. **Advanced Filtering**: ML-based relevance classification
3. **Validation Studies**: Precision/recall with manual validation
4. **Cross-Platform**: Extend to GitLab, Bitbucket

Please see our contribution guidelines:

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes with tests
4. Submit pull request

## Citation

If you use this tool in academic research, please cite:

```bibtex
@software{msr_genai_test_miner,
  author = {Edwin Noe},
  title = {MSR GenAI Test Miner: A Research-Grade GitHub Mining System},
  year = {2024},
  url = {https://github.com/edwin-noe/MSR_GenAI_Test_Miner}
}
```

## License



## Documentation

- 📘 [Methodology & Academic Documentation](METHODOLOGY.md)
- 📙 [GitHub REST API](https://docs.github.com/en/rest)
- 📕 [GitHub Search Syntax](https://docs.github.com/en/search-github/searching-on-github)

## API Reference

- [GitHub Search API](https://docs.github.com/en/rest/search)
- [GitHub Repository API](https://docs.github.com/en/rest/repos)
- [Rate Limiting](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting)






