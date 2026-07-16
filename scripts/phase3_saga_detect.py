#!/usr/bin/env python3
"""
Phase 3 — SAGA detection (tightened rule-based baseline).

Supersedes phase3_saga_pilot.py. Adds three precision improvements identified
from the pilot, where 74% of mentions were low-signal name-drops with no testing
relevance and AI-catalog repositories dominated the counts:

  1. testing_relevant flag  — every mention is tagged for whether it plausibly
     concerns TESTING (via a testing-specific context classifier or a structural
     signal). The study is about GenAI *in testing*, so this is the primary lens.
  2. repo_kind classification — catalog / awesome-list repositories are flagged
     (precise name/description rules) so they can be separated as their own stratum
     rather than swamping the counts. (Also feeds a Phase 2 exclusion for the re-mine.)
  3. tightened context classifier — testing terms only; generic words like
     "workflow" or "document" alone no longer imply a testing context.

Disk-efficient: blobless clone -> mine -> discard (peak ~one repo).

Usage:
    python scripts/phase3_saga_detect.py --limit 5                 # first 5 (by ai_keyword_count)
    python scripts/phase3_saga_detect.py --limit 25 --random      # representative random sample
    python scripts/phase3_saga_detect.py --all                    # full validated corpus

Input:  data/phase2/validated_repos.csv
Output: data/phase3/saga_mentions.csv, data/phase3/repo_saga_summary.csv
"""

import argparse
import os
import re
import shutil
import subprocess
import tempfile

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Paths are env-overridable so the script runs unchanged locally or on Railway.
#   PHASE2_CSV  input validated-repos CSV (default: data/phase2/validated_repos.csv)
#   PHASE3_DIR  output directory        (default: data/phase3)
IN_CSV = os.getenv("PHASE2_CSV", os.path.join(ROOT, "data", "phase2", "validated_repos.csv"))
OUT_DIR = os.getenv("PHASE3_DIR", os.path.join(ROOT, "data", "phase3"))
TAXONOMY_VERSION = "v2.1"

# ── SAGA prose keywords ──────────────────────────────────────────────────────
SAGA_KEYWORDS = [
    "Claude", "Anthropic", "Claude Code", "ChatGPT", "OpenAI", "GPT-4", "GPT-4o",
    "GPT-3.5", "GPT-5", "o1-mini", "o3-mini", "Gemini", "Bard", "Llama", "CodeLlama",
    "Llama-2", "Llama 3", "Mistral", "Codestral", "Mixtral", "DeepSeek", "Qwen", "Kimi",
    "GitHub Copilot", "Copilot", "Cursor", "Aider", "LangChain", "AutoGPT", "AutoGen",
    "gpt-engineer", "StarCoder", "Tabnine", "Cohere", "AI21",
]
_KW_PATTERNS = [(kw, re.compile(r"(?<![A-Za-z0-9])" + re.escape(kw) + r"(?![A-Za-z0-9])",
                                re.IGNORECASE)) for kw in SAGA_KEYWORDS]

_TRAILER = re.compile(
    r"co-authored-by:\s*.*?(copilot|claude|cursor|aider|chatgpt|gpt|codex|devin)",
    re.IGNORECASE)

CONFIG_ARTIFACTS = {
    ".cursorrules": "Cursor", ".cursor/rules": "Cursor",
    ".github/copilot-instructions.md": "GitHub Copilot",
    "copilot-instructions.md": "GitHub Copilot",
    "AGENTS.md": "generic-agent", "CLAUDE.md": "Claude Code",
    ".aider.conf.yml": "Aider", ".windsurfrules": "Windsurf",
}

# ── Testing vocabulary (the study's domain) ──────────────────────────────────
# A mention is testing-relevant only if the surrounding context contains one of
# these terms, OR it is a structural signal (trailer/config) in a repo that has
# testing infrastructure. Deliberately testing-specific; generic dev words excluded.
_TESTING_TERMS = re.compile(
    r"\b(test|tests|testing|unit ?test|integration ?test|e2e|end.to.end|"
    r"pytest|unittest|jest|mocha|junit|testng|cypress|playwright|selenium|"
    r"vitest|rspec|phpunit|xunit|nunit|"
    r"assert|assertion|test ?case|test ?suite|test ?data|fixture|mock|stub|"
    r"coverage|regression|test ?oracle|flaky|test ?generation|tdd|bdd|"
    r"spec\b|\.spec\.|_test\.|test_)\b", re.IGNORECASE)

# Testing-specific context types for the RQ2 taxonomy seed.
CONTEXT_HINTS = {
    "test_case_generation": ["generate test", "generated test", "wrote test", "write test",
                             "add test", "added test", "create test", "created test",
                             "test generation", "new test", "test case"],
    "test_data_synthesis": ["test data", "mock data", "fixture", "synthetic data",
                            "test fixture", "sample data for test"],
    "test_maintenance": ["fix test", "fixed test", "update test", "updated test",
                         "refactor test", "flaky test", "failing test", "broken test"],
    "ci_cd_integration": ["ci pipeline", "ci/cd", "github action", "test workflow",
                          "test job", "run tests in ci", "pipeline test"],
    "test_documentation": ["test doc", "document the test", "testing guide", "how to test"],
    "defect_prediction": ["detect bug", "predict defect", "bug detection", "find bug"],
}

_URL = re.compile(r"https?://\S+")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_WS = re.compile(r"\s+")


def _clean_snippet(ctx):
    """Collapse all whitespace (newlines, tabs, CRs) and strip control chars so the
    snippet is a single safe CSV cell."""
    ctx = "".join(ch for ch in ctx if ch >= " " or ch == "\t")
    return _WS.sub(" ", ctx).strip()[:200]

# ── Catalog / awesome-list detection (precise) ───────────────────────────────
_CATALOG_NAME = re.compile(r"(^|/|-)awesome(-|$)|(-|^)(resources|cheat-?sheet)$|/awesome", re.IGNORECASE)
_CATALOG_DESC = re.compile(r"\b(awesome list|curated list|collection of|a list of|"
                           r"list of (awesome|curated)|catalog of|directory of)\b", re.IGNORECASE)


def is_catalog_repo(full_name, description, topics=""):
    name = full_name.lower()
    if _CATALOG_NAME.search(name):
        return True
    if _CATALOG_DESC.search((description or "") + " " + (topics or "")):
        return True
    return False


def _classify_context(text):
    t = text.lower()
    for ctype, hints in CONTEXT_HINTS.items():
        if any(h in t for h in hints):
            return ctype
    return "unspecified"


def _is_testing_related(ctx, artifact, repo_has_test_infra):
    if _classify_context(ctx) != "unspecified":
        return True
    if _TESTING_TERMS.search(ctx):
        return True
    # structural signals count as testing-relevant only in repos with test infra
    if artifact in ("commit_trailer", "config_artifact") and repo_has_test_infra:
        return True
    return False


def _mention_type(text):
    t = text.lower()
    if any(w in t for w in ["will use", "plan to", "todo", "consider using", "planning to"]):
        return "speculative-planned"
    if any(w in t for w in ["generated by", "generated with", "used", "wrote with",
                            "assisted", "co-authored", "written by", "help of"]):
        return "direct-usage"
    if any(w in t for w in ["integrat", "workflow", "action", "pipeline"]):
        return "tool-integration"
    return "reference"


def _confidence(artifact, ctx, testing_related):
    score = {"commit_trailer": 0.9, "config_artifact": 0.9,
             "commit_message": 0.55, "readme": 0.5}.get(artifact, 0.5)
    if _classify_context(ctx) != "unspecified":
        score += 0.15
    if not testing_related:
        score -= 0.2  # down-weight name-drops with no testing connection
    return round(min(max(score, 0.05), 1.0), 2)


def _detect_in_text(text, artifact, repo_id, has_test_infra, date=None, provenance=""):
    if not text:
        return []
    stripped = _EMAIL.sub(" ", _URL.sub(" ", text))
    out = []
    for kw, pat in _KW_PATTERNS:
        m = pat.search(stripped)
        if not m:
            continue
        s, e = max(0, m.start() - 70), min(len(stripped), m.end() + 70)
        ctx = _clean_snippet(stripped[s:e])
        tr = _is_testing_related(ctx, artifact, has_test_infra)
        out.append({
            "repo_id": repo_id, "source_artifact": artifact, "keyword": kw,
            "mention_type": _mention_type(ctx),
            "context_type": _classify_context(ctx),
            "testing_relevant": tr,
            "confidence_score": _confidence(artifact, ctx, tr),
            "mention_date": date, "detection_method": "keyword",
            "provenance": provenance, "context_snippet": ctx,
        })
    return out


def _blobless_clone(url, dest):
    subprocess.run(["git", "clone", "--filter=blob:none", "--single-branch", "--quiet", url, dest],
                   check=True, timeout=600,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def mine_repo(row, workdir, max_commits=0):
    from pydriller import Repository
    repo_id, url = row["full_name"], row["html_url"]
    has_infra = bool(row.get("has_ci_config")) or bool(row.get("has_test_directory"))
    dest = os.path.join(workdir, repo_id.replace("/", "__"))
    mentions = []
    try:
        _blobless_clone(url, dest)
        n_commits = 0
        capped = False
        for commit in Repository(dest).traverse_commits():
            n_commits += 1
            if max_commits and n_commits > max_commits:
                capped = True
                break
            date = commit.committer_date.isoformat() if commit.committer_date else None
            msg = commit.msg or ""
            mentions += _detect_in_text(msg, "commit_message", repo_id, has_infra, date, commit.hash)
            if _TRAILER.search(msg):
                tool = _TRAILER.search(msg).group(1)
                mentions.append({
                    "repo_id": repo_id, "source_artifact": "commit_trailer", "keyword": tool,
                    "mention_type": "direct-usage", "context_type": "ci_cd_integration",
                    "testing_relevant": has_infra, "confidence_score": 0.95,
                    "mention_date": date, "detection_method": "trailer",
                    "provenance": commit.hash, "context_snippet": "Co-authored-by trailer",
                })
        for fn in ("README.md", "README.rst", "README.txt", "readme.md"):
            p = os.path.join(dest, fn)
            if os.path.exists(p):
                with open(p, encoding="utf-8", errors="ignore") as f:
                    mentions += _detect_in_text(f.read(), "readme", repo_id, has_infra, provenance=fn)
                break
        for rel, tool in CONFIG_ARTIFACTS.items():
            if os.path.exists(os.path.join(dest, rel)):
                mentions.append({
                    "repo_id": repo_id, "source_artifact": "config_artifact", "keyword": tool,
                    "mention_type": "tool-integration", "context_type": "ci_cd_integration",
                    "testing_relevant": has_infra, "confidence_score": 0.9,
                    "mention_date": None, "detection_method": "artifact",
                    "provenance": rel, "context_snippet": f"present: {rel}",
                })
        dates = [m["mention_date"] for m in mentions if m["mention_date"]]
        tr_dates = [m["mention_date"] for m in mentions if m["mention_date"] and m["testing_relevant"]]
        summary = {
            "repo_id": repo_id, "repo_kind": "project",
            "n_commits_scanned": n_commits, "commit_cap_hit": capped,
            "n_saga_mentions": len(mentions),
            "n_testing_relevant": sum(m["testing_relevant"] for m in mentions),
            "has_saga": len(mentions) > 0,
            "has_testing_saga": any(m["testing_relevant"] for m in mentions),
            "first_saga_date": min(dates) if dates else None,
            "first_testing_saga_date": min(tr_dates) if tr_dates else None,
            "distinct_tools": len({m["keyword"] for m in mentions}),
        }
        return mentions, summary
    finally:
        shutil.rmtree(dest, ignore_errors=True)


def _append_csv(path, rows):
    """Append rows (list of dicts) to a CSV, writing the header only if new."""
    if not rows:
        return
    df = pd.DataFrame(rows)
    header = not os.path.exists(path) or os.path.getsize(path) == 0
    df.to_csv(path, mode="a", header=header, index=False)


def _load_done(progress_path):
    if os.path.exists(progress_path):
        with open(progress_path) as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--random", action="store_true", help="random sample instead of top-by-keyword")
    ap.add_argument("--all", action="store_true", help="process the entire validated corpus")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-suffix", default="", help="suffix for output files, e.g. _sample25")
    ap.add_argument("--max-commits", type=int, default=25000,
                    help="cap commit-history traversal per repo (0 = no cap)")
    ap.add_argument("--include-catalog", action="store_true",
                    help="do NOT skip catalog/awesome-list repos (default: skip before cloning)")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    df = pd.read_csv(IN_CSV)
    if args.all:
        sel = df
    elif args.random:
        sel = df.sample(n=min(args.limit, len(df)), random_state=args.seed)
    else:
        sort_col = "ai_keyword_count" if "ai_keyword_count" in df.columns else "stars"
        sel = df.sort_values(sort_col, ascending=False).head(args.limit)

    sfx = args.out_suffix
    mpath = os.path.join(OUT_DIR, f"saga_mentions{sfx}.csv")
    spath = os.path.join(OUT_DIR, f"repo_saga_summary{sfx}.csv")
    ppath = os.path.join(OUT_DIR, f".progress{sfx}.txt")
    cpath = os.path.join(OUT_DIR, f"skipped_catalog{sfx}.csv")

    done = _load_done(ppath)  # repos already processed (resume support)
    mode = "random" if args.random else "all" if args.all else "top-keyword"
    print(f"Detecting SAGA in {len(sel)} repos ({mode}), taxonomy {TAXONOMY_VERSION}; "
          f"max_commits={args.max_commits or 'none'}; resume={len(done)} already done\n", flush=True)

    n_done = n_skip_cat = n_fail = 0
    with tempfile.TemporaryDirectory(prefix="saga_") as wd:
        for i, (_, row) in enumerate(sel.iterrows(), 1):
            repo = row["full_name"]
            if repo in done:
                continue  # resume: already processed in a prior run
            # (2) skip catalog repos BEFORE cloning — avoids huge histories & noise
            if not args.include_catalog and \
               is_catalog_repo(repo, row.get("description", ""), str(row.get("topics", ""))):
                _append_csv(cpath, [{"repo_id": repo, "reason": "catalog/awesome-list"}])
                with open(ppath, "a") as f:
                    f.write(repo + "\n")
                n_skip_cat += 1
                print(f"[{i}/{len(sel)}] {repo} ... SKIP (catalog)", flush=True)
                continue
            print(f"[{i}/{len(sel)}] {repo} ...", end=" ", flush=True)
            try:
                ms, sm = mine_repo(row, wd, max_commits=args.max_commits)
                # (1) incremental checkpoint write per repo — survives crashes
                _append_csv(mpath, ms)
                _append_csv(spath, [sm])
                with open(ppath, "a") as f:
                    f.write(repo + "\n")
                n_done += 1
                cap = " [capped]" if sm.get("commit_cap_hit") else ""
                print(f"{sm['n_saga_mentions']} mentions "
                      f"({sm['n_testing_relevant']} testing-relevant){cap}", flush=True)
            except subprocess.TimeoutExpired:
                n_fail += 1; print("SKIP (clone timeout)", flush=True)
            except subprocess.CalledProcessError:
                n_fail += 1; print("SKIP (clone failed)", flush=True)
            except Exception as e:
                n_fail += 1; print(f"ERROR: {type(e).__name__}: {e}", flush=True)

    print(f"\n=== RUN COMPLETE (taxonomy {TAXONOMY_VERSION}) ===", flush=True)
    print(f"  processed this run:  {n_done}")
    print(f"  skipped (catalog):   {n_skip_cat}")
    print(f"  failed (clone/err):  {n_fail}")
    if os.path.exists(spath):
        s = pd.read_csv(spath)
        print(f"  total repos in output: {len(s)}")
        print(f"  repos with testing-SAGA: {int(s['has_testing_saga'].sum())} "
              f"({100*s['has_testing_saga'].mean():.0f}%)")
    print(f"\nOutputs -> {mpath}\n            {spath}", flush=True)


if __name__ == "__main__":
    main()
