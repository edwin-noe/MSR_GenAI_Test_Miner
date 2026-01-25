import os, sys, signal
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from tqdm import tqdm
from .query_generator import QueryGenerator
from .repo_filter import RepoFilter
from .repo_enricher import RepoEnricher
from .github_miner import GitHubMiner
from .config import OUTPUT_FILE, PROGRESS_FILE


class MinerApp:
    """
    Main application for MSR GitHub repository mining.

    Features:
    - Sharded query generation to overcome 1,000-result limit
    - Comprehensive repository enrichment (30 characteristics)
    - Multi-stage filtering pipeline
    - Progress tracking and resumption
    - Deterministic execution with logging
    """

    def __init__(self, use_sharded_queries: bool = True, enrich_repos: bool = True):
        """
        Initialize the miner application.

        Args:
            use_sharded_queries: If True, use comprehensive sharded queries.
                                If False, use simple queries (for testing).
            enrich_repos: If True, perform full enrichment (slower but high quality).
                         If False, use basic filtering only.
        """
        os.makedirs("output", exist_ok=True)

        self.use_sharded_queries = use_sharded_queries
        self.enrich_repos = enrich_repos

        # Generate queries
        if use_sharded_queries:
            self.queries = QueryGenerator.generate_sharded_queries()
            print(f"📊 Generated {len(self.queries)} sharded queries")
        else:
            self.queries = QueryGenerator.generate_simple_queries()
            print(f"📊 Generated {len(self.queries)} simple queries")

        self.start_index = self.load_progress()
        self.all_results = self.load_results()
        self.seen_repos = set(r.get("full_name") for r in self.all_results if r.get("full_name"))

        self.miner = GitHubMiner()
        self.enricher = RepoEnricher() if enrich_repos else None

        # Setup signal handler for graceful interruption
        signal.signal(signal.SIGINT, self._handle_interrupt)

        # Logging
        self.log_file = "output/mining_log.txt"
        self._log(f"Mining session started at {datetime.now().isoformat()}")
        self._log(f"Configuration: sharded_queries={use_sharded_queries}, enrich_repos={enrich_repos}")
        self._log(f"Total queries: {len(self.queries)}")

        # Time tracking
        self.start_time = None
        self.query_times = []

    def load_progress(self) -> int:
        """Load progress from file."""
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, "r") as f:
                    index = int(f.read().strip())
                    # Validate index is within bounds
                    if index < 0 or index >= len(self.queries):
                        print(f"⚠️ Warning: Invalid progress index {index}, resetting to 0")
                        return 0
                    return index
            except (ValueError, IOError) as e:
                print(f"⚠️ Warning:  Could not load progress:  {e}")
                return 0
        return 0

    def save_progress(self, index: int = None):
        """Save current progress to file."""
        index = index if index is not None else self.start_index
        with open(PROGRESS_FILE, "w") as f:
            f.write(str(index))

    def load_results(self) -> List[Dict[str, Any]]:
        """Load existing results from CSV if available."""
        if os.path.exists(OUTPUT_FILE):
            try:
                df = pd.read_csv(OUTPUT_FILE)
                if df.empty:
                    return []
                # Validate that essential columns exist
                if 'full_name' not in df.columns:
                    print("⚠️ Warning:  Existing CSV missing 'full_name' column, ignoring file")
                    self._log("Warning: Existing CSV missing 'full_name' column, ignoring file")
                    return []
                return df.to_dict(orient="records")
            except Exception as e:
                print(f"⚠️ Warning:  Could not load existing results: {e}")
                print("   Starting with fresh results...")
                return []
        return []

    def save_results(self):
        """Save results to CSV and JSON formats with deduplication."""
        if not self.all_results:
            print("⚠️ No results to save")
            return

        df = pd.DataFrame(self.all_results)

        # Check if full_name column exists
        if "full_name" not in df.columns:
            print("⚠️ Warning: 'full_name' column missing from results")
            self._log("Warning: Cannot deduplicate - 'full_name' column missing")
            # Save what we have without deduplication
            df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
            json_file = OUTPUT_FILE.replace(". csv", ".json")
            with open(json_file, "w", encoding='utf-8') as f:
                json.dump(self.all_results, f, indent=2, default=str, ensure_ascii=False)
            print(f"💾 Saved {len(df)} repos (no deduplication - missing full_name)")
            return

        # Sort by quality score (if available) and stars before deduplication
        # This ensures we keep the best occurrence of each repository
        sort_cols = []
        if "quality_score" in df.columns:
            sort_cols.append("quality_score")
        if "stars" in df.columns:
            sort_cols.append("stars")

        if sort_cols:
            df = df.sort_values(by=sort_cols, ascending=False)

        # Deduplicate by full_name, keeping the best (first after sorting)
        df = df.drop_duplicates(subset="full_name", keep="first")

        # Re-sort for output consistency
        if sort_cols:
            df = df.sort_values(by=sort_cols, ascending=False)

        # Save CSV file with proper column/row format
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

        # Convert deduplicated dataframe back to list of dictionaries for JSON
        deduplicated_results = df.to_dict(orient="records")

        # Save JSON file with proper JSON array format (deduplicated data)
        json_file = OUTPUT_FILE.replace(".csv", ".json")
        with open(json_file, "w", encoding='utf-8') as f:
            json.dump(deduplicated_results, f, indent=2, default=str, ensure_ascii=False)

        self._log(f"Saved {len(df)} unique repos to CSV and JSON")

    def _handle_interrupt(self, signum, frame):
        """Handle interrupt signal (Ctrl+C) gracefully."""
        print("\n⏸️ Interrupted!  Saving current progress...")
        self.save_results()
        self.save_progress(self.start_index)
        self._log("Mining interrupted by user")
        sys.exit(0)

    def _log(self, message: str):
        """Log message to file with timestamp."""
        with open(self.log_file, "a") as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")

    def _estimate_time_remaining(self, current_index: int) -> str:
        """Estimate time remaining based on average query time."""
        if not self.query_times or current_index == 0:
            return "calculating..."

        avg_time = sum(self.query_times) / len(self.query_times)
        remaining_queries = len(self.queries) - current_index - 1
        remaining_seconds = avg_time * remaining_queries

        if remaining_seconds < 60:
            return f"{int(remaining_seconds)}s"
        elif remaining_seconds < 3600:
            return f"{int(remaining_seconds / 60)}m {int(remaining_seconds % 60)}s"
        else:
            hours = int(remaining_seconds / 3600)
            minutes = int((remaining_seconds % 3600) / 60)
            return f"{hours}h {minutes}m"

    def run(self):
        """Run the mining pipeline with progress tracking."""
        self.start_time = datetime.now()

        print(f"\n🚀 Starting mining from query {self.start_index + 1}/{len(self.queries)}")
        print(
            f"📋 Mode: {'Enriched' if self.enrich_repos else 'Basic'} | Queries: {'Sharded' if self.use_sharded_queries else 'Simple'}")
        print(f"📊 Current results: {len(self.all_results)} unique repos\n")

        total_found = 0
        total_accepted = 0

        # Progress bar for queries
        query_pbar = tqdm(
            enumerate(self.queries[self.start_index:], start=self.start_index),
            total=len(self.queries) - self.start_index,
            desc="Mining queries",
            unit="query",
            position=0,
            leave=True
        )

        for i, query in query_pbar:
            query_start_time = datetime.now()

            # Update query progress bar description
            query_pbar.set_description(f"Query {i + 1}/{len(self.queries)}")

            self._log(f"Query {i + 1}/{len(self.queries)}: {query}")

            try:
                repos = self.miner.github_search(query)
                total_found += len(repos)

                accepted_count = 0

                # Progress bar for repos in this query
                if repos and self.enrich_repos:
                    repo_pbar = tqdm(
                        repos,
                        desc=f"  Processing repos",
                        unit="repo",
                        position=1,
                        leave=False
                    )
                else:
                    repo_pbar = repos

                for repo in repo_pbar:
                    # Skip if already processed
                    full_name = repo.get("full_name")
                    if full_name in self.seen_repos:
                        continue

                    try:
                        if self.enrich_repos:
                            # Update repo progress bar
                            if hasattr(repo_pbar, 'set_description'):
                                repo_pbar.set_description(f"  Processing:  {full_name}")

                            # Full enrichment and filtering
                            enriched = self.enricher.enrich_repository(repo)
                            passes, quality_score = RepoFilter.high_precision_filter(enriched)

                            if passes:
                                enriched["quality_score"] = quality_score
                                self.all_results.append(enriched)
                                self.seen_repos.add(full_name)
                                accepted_count += 1
                                total_accepted += 1
                        else:
                            # Basic filtering only
                            if RepoFilter.simple_filter(repo):
                                self.all_results.append({
                                    "full_name": repo.get("full_name"),
                                    "html_url": repo.get("html_url"),
                                    "stars": repo.get("stargazers_count"),
                                    "language": repo.get("language"),
                                    "description": repo.get("description")
                                })
                                self.seen_repos.add(full_name)
                                accepted_count += 1
                                total_accepted += 1
                    except Exception as e:
                        self._log(f"Error processing {full_name}: {e}")

                # Close repo progress bar
                if hasattr(repo_pbar, 'close'):
                    repo_pbar.close()

            except Exception as e:
                tqdm.write(f"  ⚠️ Error executing query: {e}")
                self._log(f"Error executing query: {e}")

            # Calculate query time
            query_elapsed = (datetime.now() - query_start_time).total_seconds()
            self.query_times.append(query_elapsed)

            # Keep only last 10 query times for better ETA accuracy
            if len(self.query_times) > 10:
                self.query_times.pop(0)

            # Save progress after every query
            self.start_index = i + 1
            self.save_results()
            self.save_progress(self.start_index)

            # Update progress bar postfix with stats
            eta = self._estimate_time_remaining(i)
            query_pbar.set_postfix({
                'Found': total_found,
                'Accepted': total_accepted,
                'Unique': len(self.all_results),
                'ETA': eta
            })

        query_pbar.close()

        # Final save
        self.save_results()
        self.save_progress(self.start_index)

        elapsed_time = datetime.now() - self.start_time

        print(f"\n✅ Mining complete!")
        print(f"📊 Final Statistics:")
        print(f"   Total queries executed: {len(self.queries)}")
        print(f"   Total repos found: {total_found}")
        print(f"   Total repos accepted: {total_accepted}")
        print(f"   Unique repos saved: {len(self.all_results)}")
        print(f"   Time elapsed: {elapsed_time}")
        print(f"   Output files:")
        print(f"     📄 CSV:   {OUTPUT_FILE}")
        print(f"     📄 JSON: {OUTPUT_FILE.replace('. csv', '.json')}")

        self._log(f"Mining complete:  {len(self.all_results)} unique repos in {elapsed_time}")

        # Print quality statistics if available
        if self.enrich_repos and self.all_results:
            self._print_quality_stats()

    def _print_quality_stats(self):
        """Print statistics about quality scores."""
        scores = [r.get("quality_score", 0) for r in self.all_results if "quality_score" in r]
        if scores:
            print(f"\n📈 Quality Score Statistics:")
            print(f"   Mean: {sum(scores) / len(scores):.2f}")
            print(f"   Min: {min(scores):.2f}")
            print(f"   Max: {max(scores):.2f}")
            print(f"   Repos with score >= 20: {sum(1 for s in scores if s >= 20)}")
            print(f"   Repos with score >= 15: {sum(1 for s in scores if s >= 15)}")