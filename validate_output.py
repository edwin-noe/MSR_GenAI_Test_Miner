#!/usr/bin/env python3
"""
Output validation script for MSR GenAI Test Miner.

Validates the quality and completeness of mined repository data.
"""

import sys
import os
import pandas as pd
import json
from typing import Dict, List, Any

# Import MIN_STARS constant for consistency
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.repo_filter import RepoFilter


def load_results(output_file: str = "output/validated_repos.csv") -> pd.DataFrame:
    """Load results from CSV file."""
    if not os.path.exists(output_file):
        print(f"❌ Error: Output file not found: {output_file}")
        sys.exit(1)
    
    return pd.read_csv(output_file)


def validate_basic_structure(df: pd.DataFrame) -> List[str]:
    """Validate basic data structure."""
    issues = []
    
    # Check required columns
    required_cols = ["full_name", "html_url", "stars"]
    for col in required_cols:
        if col not in df.columns:
            issues.append(f"Missing required column: {col}")
    
    # Check for duplicates
    if "full_name" in df.columns:
        duplicates = df[df.duplicated(subset="full_name", keep=False)]
        if not duplicates.empty:
            issues.append(f"Found {len(duplicates)} duplicate repositories")
    
    # Check for null values in critical columns
    for col in required_cols:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                issues.append(f"Column '{col}' has {null_count} null values")
    
    return issues


def validate_enrichment(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate enrichment completeness."""
    stats = {
        "total_repos": len(df),
        "enrichment_completeness": {},
        "quality_scores": {}
    }
    
    # Expected enrichment columns (subset of 30)
    enrichment_cols = [
        "stars", "forks", "watchers", "open_issues", "size_kb",
        "commit_count", "contributor_count", "days_since_last_push",
        "primary_language", "has_wiki", "has_license",
        "readme_length", "has_test_directory", "has_ci_config",
        "ai_keyword_count", "test_keyword_count"
    ]
    
    for col in enrichment_cols:
        if col in df.columns:
            non_null = df[col].notnull().sum()
            percentage = (non_null / len(df)) * 100
            stats["enrichment_completeness"][col] = {
                "count": int(non_null),
                "percentage": round(percentage, 2)
            }
    
    # Quality score statistics
    if "quality_score" in df.columns:
        scores = df["quality_score"].dropna()
        if not scores.empty:
            stats["quality_scores"] = {
                "mean": float(scores.mean()),
                "median": float(scores.median()),
                "min": float(scores.min()),
                "max": float(scores.max()),
                "std": float(scores.std())
            }
    
    return stats


def validate_data_quality(df: pd.DataFrame) -> List[str]:
    """Validate data quality."""
    issues = []
    
    # Check star counts are reasonable
    if "stars" in df.columns:
        low_stars = df[df["stars"] < RepoFilter.MIN_STARS]
        if not low_stars.empty:
            issues.append(f"Found {len(low_stars)} repos with < {RepoFilter.MIN_STARS} stars (below threshold)")
    
    # Check for missing descriptions
    if "description" in df.columns:
        no_desc = df[df["description"].isnull() | (df["description"] == "")]
        if not no_desc.empty:
            issues.append(f"Found {len(no_desc)} repos without descriptions")
    
    # Check activity (if available)
    if "days_since_last_push" in df.columns:
        old_repos = df[df["days_since_last_push"] > 730]
        if not old_repos.empty:
            issues.append(f"Found {len(old_repos)} repos not pushed in > 2 years")
    
    # Check for AI/testing signals (if enriched)
    if "ai_keyword_count" in df.columns and "test_keyword_count" in df.columns:
        no_signals = df[(df["ai_keyword_count"] == 0) & (df["test_keyword_count"] == 0)]
        if not no_signals.empty:
            issues.append(f"Found {len(no_signals)} repos with no AI or testing signals")
    
    return issues


def print_statistics(df: pd.DataFrame):
    """Print dataset statistics."""
    print("\n" + "=" * 70)
    print("DATASET STATISTICS")
    print("=" * 70)
    
    print(f"Total repositories: {len(df)}")
    
    if "stars" in df.columns:
        print(f"\nStar distribution:")
        print(f"  Mean: {df['stars'].mean():.0f}")
        print(f"  Median: {df['stars'].median():.0f}")
        print(f"  Min: {df['stars'].min():.0f}")
        print(f"  Max: {df['stars'].max():.0f}")
    
    if "primary_language" in df.columns:
        print(f"\nTop 5 languages:")
        lang_counts = df["primary_language"].value_counts().head(5)
        for lang, count in lang_counts.items():
            print(f"  {lang}: {count}")
    
    if "quality_score" in df.columns:
        scores = df["quality_score"].dropna()
        if not scores.empty:
            print(f"\nQuality scores:")
            print(f"  Mean: {scores.mean():.2f}")
            print(f"  Median: {scores.median():.2f}")
            print(f"  Min: {scores.min():.2f}")
            print(f"  Max: {scores.max():.2f}")
            print(f"  Repos with score >= 20: {(scores >= 20).sum()}")
            print(f"  Repos with score >= 15: {(scores >= 15).sum()}")
    
    print("=" * 70)


def main():
    """Main validation routine."""
    print("MSR GenAI Test Miner - Output Validation")
    print("=" * 70)
    
    # Load results
    print("Loading results...")
    df = load_results()
    print(f"✓ Loaded {len(df)} repositories\n")
    
    # Validate structure
    print("Validating data structure...")
    structure_issues = validate_basic_structure(df)
    if structure_issues:
        print("❌ Structure validation issues:")
        for issue in structure_issues:
            print(f"  - {issue}")
    else:
        print("✓ Structure validation passed\n")
    
    # Validate enrichment
    print("Analyzing enrichment completeness...")
    enrichment_stats = validate_enrichment(df)
    
    print(f"✓ Enrichment analysis complete")
    print(f"  Total repos: {enrichment_stats['total_repos']}")
    
    if enrichment_stats["enrichment_completeness"]:
        avg_completeness = sum(
            v["percentage"] for v in enrichment_stats["enrichment_completeness"].values()
        ) / len(enrichment_stats["enrichment_completeness"])
        print(f"  Average completeness: {avg_completeness:.1f}%\n")
    
    # Validate data quality
    print("Validating data quality...")
    quality_issues = validate_data_quality(df)
    if quality_issues:
        print("⚠️  Quality validation warnings:")
        for issue in quality_issues:
            print(f"  - {issue}")
    else:
        print("✓ Quality validation passed\n")
    
    # Print statistics
    print_statistics(df)
    
    # Save validation report
    report = {
        "total_repos": len(df),
        "structure_issues": structure_issues,
        "quality_issues": quality_issues,
        "enrichment_stats": enrichment_stats
    }
    
    report_file = "output/validation_report.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✓ Validation report saved to: {report_file}")
    
    # Return exit code
    if structure_issues:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
