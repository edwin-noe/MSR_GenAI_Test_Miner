"""
MSR GenAI Test Miner - Main Entry Point

Usage:
    python -m src.main                    # Full enrichment with sharded queries
    python -m src.main --simple           # Simple queries without enrichment
    python -m src.main --no-enrich        # Sharded queries without enrichment
    python -m src.main --check-rate-limit # Check API rate limit status
"""

import sys
from .miner_app import MinerApp
from .github_miner import GitHubMiner


def main():
    """Main entry point with argument parsing."""
    args = sys.argv[1:]
    
    # Check for rate limit status request
    if "--check-rate-limit" in args or "-r" in args:
        miner = GitHubMiner()
        miner.print_rate_limit_status()
        return
    
    # Parse arguments
    use_sharded = "--simple" not in args
    enrich_repos = "--no-enrich" not in args
    
    # Print configuration
    print("=" * 60)
    print("MSR GenAI Test Miner")
    print("=" * 60)
    print(f"Query Strategy: {'Sharded (comprehensive)' if use_sharded else 'Simple (testing)'}")
    print(f"Enrichment: {'Enabled (30 characteristics)' if enrich_repos else 'Disabled (basic only)'}")
    print("=" * 60)
    print()
    
    if "--help" in args or "-h" in args:
        print(__doc__)
        return
    
    # Run the application
    app = MinerApp(use_sharded_queries=use_sharded, enrich_repos=enrich_repos)
    app.run()


if __name__ == "__main__":
    main()
