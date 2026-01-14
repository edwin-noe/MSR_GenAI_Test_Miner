import os, sys, signal
import pandas as pd
from .query_generator import QueryGenerator
from .repo_filter import RepoFilter
from .github_miner import GitHubMiner
from .config import OUTPUT_FILE, PROGRESS_FILE

class MinerApp:
    def __init__(self):
        os.makedirs("output", exist_ok=True)
        self.queries = QueryGenerator.generate_queries()
        self.start_index = self.load_progress()
        self.all_results = self.load_results()
        self.miner = GitHubMiner()
        signal.signal(signal.SIGINT, self._handle_interrupt)

    def load_progress(self):
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, "r") as f:
                return int(f.read().strip())
        return 0

    def save_progress(self, index=None):
        index = index if index is not None else self.start_index
        with open(PROGRESS_FILE, "w") as f:
            f.write(str(index))

    def load_results(self):
        if os.path.exists(OUTPUT_FILE):
            return pd.read_csv(OUTPUT_FILE).to_dict(orient="records")
        return []

    def save_results(self):
        df = pd.DataFrame(self.all_results).drop_duplicates(subset="url")
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"💾 Progress saved, {len(df)} repos collected")

    def _handle_interrupt(self, signum, frame):
        print("\n⏸️ Interrupted! Saving current progress...")
        self.save_results()
        self.save_progress(self.start_index)
        sys.exit(0)

    def run(self):
        print(f"Resuming from query {self.start_index + 1}/{len(self.queries)}")
        for i, query in enumerate(self.queries[self.start_index:], start=self.start_index):
            print(f"[{i+1}/{len(self.queries)}] 🔍 Searching: {query}")
            try:
                repos = self.miner.github_search(query)
                for repo in repos:
                    if RepoFilter.high_precision_filter(repo):
                        self.all_results.append({
                            "name": repo.get("full_name"),
                            "url": repo.get("html_url"),
                            "stars": repo.get("stargazers_count"),
                            "language": repo.get("language"),
                            "description": repo.get("description")
                        })
            except Exception as e:
                print(f"⚠️ Error searching query: {query}")
                print(e)

            # Save progress every query
            self.start_index = i + 1
            self.save_results()
            self.save_progress(self.start_index)

        self.save_results()
        self.save_progress(self.start_index)
        print(f"✅ Done! Total {len(self.all_results)} repos saved to {OUTPUT_FILE}")
