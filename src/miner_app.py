import os, sys, signal
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Any
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
        self.seen_repos = set(r["full_name"] for r in self.all_results)  # Deduplication
        
        self.miner = GitHubMiner()
        self.enricher = RepoEnricher() if enrich_repos else None
        
        # Setup signal handler for graceful interruption
        signal.signal(signal.SIGINT, self._handle_interrupt)
        
        # Logging
        self.log_file = "output/mining_log.txt"
        self._log(f"Mining session started at {datetime.now().isoformat()}")
        self._log(f"Configuration: sharded_queries={use_sharded_queries}, enrich_repos={enrich_repos}")
        self._log(f"Total queries: {len(self.queries)}")
    
    def load_progress(self) -> int:
        """Load progress from file."""
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, "r") as f:
                return int(f.read().strip())
        return 0
    
    def save_progress(self, index: int = None):
        """Save current progress to file."""
        index = index if index is not None else self.start_index
        with open(PROGRESS_FILE, "w") as f:
            f.write(str(index))
    
    def load_results(self) -> List[Dict[str, Any]]:
        """Load existing results from CSV if available."""
        if os.path.exists(OUTPUT_FILE):
            df = pd.read_csv(OUTPUT_FILE)
            return df.to_dict(orient="records")
        return []
    
    def save_results(self):
        """Save results to CSV with deduplication."""
        if not self.all_results:
            print("⚠️ No results to save")
            return
        
        df = pd.DataFrame(self.all_results)
        
        # Deduplicate by full_name (repo identifier)
        df = df.drop_duplicates(subset="full_name", keep="first")
        
        # Sort by quality score (if available) and stars
        sort_cols = []
        if "quality_score" in df.columns:
            sort_cols.append("quality_score")
        if "stars" in df.columns:
            sort_cols.append("stars")
        
        if sort_cols:
            df = df.sort_values(by=sort_cols, ascending=False)
        
        df.to_csv(OUTPUT_FILE, index=False)
        
        # Also save as JSON for full fidelity
        json_file = OUTPUT_FILE.replace(".csv", ".json")
        with open(json_file, "w") as f:
            json.dump(self.all_results, f, indent=2, default=str)
        
        print(f"💾 Saved {len(df)} unique repos to {OUTPUT_FILE}")
        self._log(f"Saved {len(df)} unique repos")
    
    def _handle_interrupt(self, signum, frame):
        """Handle interrupt signal (Ctrl+C) gracefully."""
        print("\n⏸️ Interrupted! Saving current progress...")
        self.save_results()
        self.save_progress(self.start_index)
        self._log("Mining interrupted by user")
        sys.exit(0)
    
    def _log(self, message: str):
        """Log message to file with timestamp."""
        with open(self.log_file, "a") as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")
    
    def run(self):
        """Run the mining pipeline."""
        print(f"\n🚀 Starting mining from query {self.start_index + 1}/{len(self.queries)}")
        print(f"📋 Mode: {'Enriched' if self.enrich_repos else 'Basic'} | Queries: {'Sharded' if self.use_sharded_queries else 'Simple'}")
        print(f"📊 Current results: {len(self.all_results)} unique repos\n")
        
        total_found = 0
        total_accepted = 0
        
        for i, query in enumerate(self.queries[self.start_index:], start=self.start_index):
            print(f"[{i+1}/{len(self.queries)}] 🔍 Query: {query}")
            self._log(f"Query {i+1}/{len(self.queries)}: {query}")
            
            try:
                repos = self.miner.github_search(query)
                total_found += len(repos)
                print(f"  Found {len(repos)} repos")
                
                accepted_count = 0
                for repo in repos:
                    # Skip if already processed
                    full_name = repo.get("full_name")
                    if full_name in self.seen_repos:
                        continue
                    
                    try:
                        if self.enrich_repos:
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
                        print(f"  ⚠️ Error processing {full_name}: {e}")
                        self._log(f"Error processing {full_name}: {e}")
                
                print(f"  ✅ Accepted {accepted_count}/{len(repos)} repos")
                
            except Exception as e:
                print(f"  ⚠️ Error executing query: {e}")
                self._log(f"Error executing query: {e}")
            
            # Save progress after every query
            self.start_index = i + 1
            self.save_results()
            self.save_progress(self.start_index)
            
            # Print statistics every 10 queries
            if (i + 1) % 10 == 0:
                print(f"\n📊 Progress: {i+1}/{len(self.queries)} queries | Found: {total_found} | Accepted: {total_accepted} | Unique: {len(self.all_results)}\n")
        
        # Final save
        self.save_results()
        self.save_progress(self.start_index)
        
        print(f"\n✅ Mining complete!")
        print(f"📊 Final Statistics:")
        print(f"   Total queries executed: {len(self.queries)}")
        print(f"   Total repos found: {total_found}")
        print(f"   Total repos accepted: {total_accepted}")
        print(f"   Unique repos saved: {len(self.all_results)}")
        print(f"   Output file: {OUTPUT_FILE}")
        
        self._log(f"Mining complete: {len(self.all_results)} unique repos")
        
        # Print quality statistics if available
        if self.enrich_repos and self.all_results:
            self._print_quality_stats()
    
    def _print_quality_stats(self):
        """Print statistics about quality scores."""
        scores = [r.get("quality_score", 0) for r in self.all_results if "quality_score" in r]
        if scores:
            print(f"\n📈 Quality Score Statistics:")
            print(f"   Mean: {sum(scores)/len(scores):.2f}")
            print(f"   Min: {min(scores):.2f}")
            print(f"   Max: {max(scores):.2f}")
            print(f"   Repos with score >= 20: {sum(1 for s in scores if s >= 20)}")
            print(f"   Repos with score >= 15: {sum(1 for s in scores if s >= 15)}")
