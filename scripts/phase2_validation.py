#!/usr/bin/env python3
"""
Phase 2 — Repository Validation Pipeline.

Applies quality gates to the Phase 1 mined dataset and produces the validated
repository list plus a funnel report. Gates are ordered cheapest-first: Stage A
uses only the enriched columns already in the Phase 1 CSV (no API calls, no
token). Stage B (README language detection) re-fetches READMEs for Stage-A
survivors only, and waits out GitHub rate limits rather than failing.

Paths are repo-relative and overridable by environment variable so this runs
unchanged locally or on Railway:

    PHASE1_CSV   input dataset      (default: output/validated_repos.csv)
    PHASE2_DIR   output directory   (default: output/phase2)

Usage:
    python scripts/phase2_validation.py            # Stage A only
    python scripts/phase2_validation.py --stage-b  # Stage A + B (needs GITHUB_TOKEN)
"""

import argparse
import ast
import os
import re
import sys
from datetime import datetime, timezone

import pandas as pd

# ── Paths (repo-relative, env-overridable) ───────────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)  # so `import phase2_stage_b` works when run as a file

PHASE1_CSV = os.getenv("PHASE1_CSV", os.path.join(ROOT, "output", "validated_repos.csv"))
PHASE2_DIR = os.getenv("PHASE2_DIR", os.path.join(ROOT, "output", "phase2"))

PHASE2_VERSION = "v1.0"

# ── Stage 1: accepted OSS licenses (matched on GitHub's human-readable names) ─
# Close to the proposal list (MIT, Apache-2.0, GPL-3.0, BSD variants, ISC) plus
# widely accepted OSS siblings. Tunable allowlist documented for reproducibility.
ACCEPTED_LICENSES = {
    "MIT License",
    "MIT No Attribution",
    "Apache License 2.0",
    "GNU General Public License v3.0",
    "GNU General Public License v2.0",
    "GNU Affero General Public License v3.0",
    "GNU Lesser General Public License v3.0",
    "GNU Lesser General Public License v2.1",
    'BSD 3-Clause "New" or "Revised" License',
    'BSD 2-Clause "Simplified" License',
    "BSD 3-Clause Clear License",
    "ISC License",
    "Mozilla Public License 2.0",
}

# ── Stage 3: tutorial / educational / template exclusion taxonomy ─────────────
# Single-word triggers match a word token by EXACT or simple-plural form only.
# The proposal specified fuzzy ≥80%, but that over-matched ("lab"->"lb",
# "course"->"core", "sample"->"simple"); tightened to deterministic morphological
# matching. "learning" is deliberately excluded (matches "machine/deep learning").
TUTORIAL_KEYWORDS_SINGLE = [
    "tutorial", "assignment", "coursework", "lab", "exercise",
    "boilerplate", "sample", "demo", "scaffold", "template",
    "course", "workshop", "playground",
]
TUTORIAL_KEYWORDS_MULTI = ["starter template", "example project", "hello world"]
PLURAL_SKIP = {"lab"}  # "labs" is usually a company name, not a coursework lab


def _parse_topics(val):
    if isinstance(val, list):
        return val
    if not isinstance(val, str) or not val.strip():
        return []
    try:
        out = ast.literal_eval(val)
        return out if isinstance(out, list) else []
    except (ValueError, SyntaxError):
        return []


def _norm_tokens(text, topics):
    text = (text or "").lower()
    toks = {t for t in re.split(r"[^a-z0-9]+", text) if t}
    toks |= {str(t).lower().strip() for t in topics if str(t).strip()}
    return toks


def _tutorial_hit(text, topics):
    tokens = _norm_tokens(text, topics)
    for kw in TUTORIAL_KEYWORDS_SINGLE:
        forms = {kw}
        if kw not in PLURAL_SKIP:
            forms |= {kw + "s", kw + "es"}
        hit = tokens & forms
        if hit:
            return kw, sorted(hit)[0]
    flat = (text or "").lower()
    for kw in TUTORIAL_KEYWORDS_MULTI:
        if kw in flat:
            return kw, kw
    return None, None


def run_stage_a(df):
    funnel = []
    n0 = len(df)
    funnel.append(("Phase 1 candidates", n0, 0))
    excluded_rows = []

    def drop(mask, reason):
        nonlocal df
        removed = df[mask].copy()
        removed["exclusion_stage"] = reason
        excluded_rows.append(removed)
        return df[~mask].copy()

    lic_ok = df["license"].isin(ACCEPTED_LICENSES)
    df = drop(~lic_ok, "license: not an accepted OSS license")
    funnel.append(("Stage 1 - License gate", len(df), n0 - len(df)))
    n1 = len(df)

    has_infra = df["has_ci_config"].fillna(False).astype(bool) | \
                df["has_test_directory"].fillna(False).astype(bool)
    df = drop(~has_infra, "testing-infra: no CI/CD config and no test directory")
    funnel.append(("Stage 2 - Testing-infra gate", len(df), n1 - len(df)))
    n2 = len(df)

    tut_kw, tut_tok = [], []
    for _, r in df.iterrows():
        text = f"{r['full_name']} {r.get('description', '') or ''}"
        kw, tok = _tutorial_hit(text, _parse_topics(r.get("topics")))
        tut_kw.append(kw)
        tut_tok.append(tok)
    df = df.assign(_tk=tut_kw, _tt=tut_tok)
    is_tut = df["_tk"].notna()
    rm = df[is_tut].copy()
    rm["exclusion_stage"] = "tutorial: " + rm["_tk"].astype(str) + \
                            " (matched '" + rm["_tt"].astype(str) + "')"
    excluded_rows.append(rm.drop(columns=["_tk", "_tt"]))
    df = df[~is_tut].drop(columns=["_tk", "_tt"]).copy()
    funnel.append(("Stage 3 - Tutorial/template exclusion", len(df), n2 - len(df)))

    excluded = pd.concat(excluded_rows, ignore_index=True) if excluded_rows else pd.DataFrame()
    return df, excluded, funnel


def write_report(funnel, survivors, excluded, stage_b_done):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Phase 2 Validation Report", "",
        f"**Generated:** {now}  ",
        f"**Pipeline version:** {PHASE2_VERSION}  ",
        f"**Input:** `{os.path.relpath(PHASE1_CSV, ROOT)}`  ",
        f"**Stage B (language detection):** {'run' if stage_b_done else 'NOT run (Stage A only)'}",
        "", "## Validation funnel", "",
        "| Stage | Repos remaining | Removed at this stage |",
        "|-------|----------------:|----------------------:|",
    ]
    for name, kept, removed in funnel:
        lines.append(f"| {name} | {kept:,} | {removed:,} |")
    lines += ["", "## Exclusion breakdown", ""]
    if len(excluded):
        brk = excluded["exclusion_stage"].apply(lambda s: s.split(":")[0]).value_counts()
        lines += ["| Reason | Count |", "|--------|------:|"]
        for reason, c in brk.items():
            lines.append(f"| {reason} | {c:,} |")
    else:
        lines.append("_None excluded._")
    if len(survivors):
        lines += ["", "## Validated corpus profile", "",
                  f"- Validated repositories: {len(survivors):,}",
                  f"- With CI/CD: {int(survivors['has_ci_config'].sum()):,} "
                  f"({100*survivors['has_ci_config'].mean():.0f}%)",
                  f"- Median stars: {survivors['stars'].median():.0f}",
                  f"- Mean quality score: {survivors['quality_score'].mean():.1f}"]
    with open(os.path.join(PHASE2_DIR, "phase2_report.md"), "w") as f:
        f.write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage-b", action="store_true",
                    help="Also run README language detection (needs GITHUB_TOKEN)")
    args = ap.parse_args()

    os.makedirs(PHASE2_DIR, exist_ok=True)
    if not os.path.exists(PHASE1_CSV):
        sys.exit(f"Phase 1 input not found: {PHASE1_CSV} "
                 f"(set PHASE1_CSV or run the miner first).")

    df = pd.read_csv(PHASE1_CSV)
    print(f"Loaded {len(df):,} Phase 1 candidates from {PHASE1_CSV}", flush=True)

    survivors, excluded, funnel = run_stage_a(df)

    stage_b_done = False
    if args.stage_b:
        from phase2_stage_b import run_stage_b
        survivors, b_funnel = run_stage_b(survivors, PHASE2_DIR)
        funnel += b_funnel
        stage_b_done = True

    survivors = survivors.assign(phase2_pass=True)
    survivors.to_csv(os.path.join(PHASE2_DIR, "validated_repos.csv"), index=False)
    if len(excluded):
        excluded.to_csv(os.path.join(PHASE2_DIR, "excluded_repos.csv"), index=False)
    write_report(funnel, survivors, excluded, stage_b_done)

    print("\n=== FUNNEL ===", flush=True)
    for name, kept, removed in funnel:
        print(f"  {name:42s} {kept:>6,} remaining  (-{removed:,})", flush=True)
    print(f"\nValidated: {len(survivors):,} | Excluded: {len(excluded):,}", flush=True)
    print(f"Outputs -> {PHASE2_DIR}", flush=True)


if __name__ == "__main__":
    main()
