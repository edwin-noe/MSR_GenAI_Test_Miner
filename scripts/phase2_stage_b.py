"""
Phase 2 — Stage B: README language validation (>=80% English).

Re-fetches each survivor's README via the GitHub API, strips code blocks, and
detects language at line level. A repo passes if >=80% of substantive text
lines are English (configurable threshold).

Rate-limit policy (per requirement): on a GitHub rate limit, the fetcher WAITS
until the limit resets and retries — indefinitely — rather than failing. Only
genuine transient errors (network/5xx) are capped with exponential backoff.

Checkpointed: results cache to <PHASE2_DIR>/_stage_b_cache.csv so an interrupted
run resumes without re-fetching. Requires env var GITHUB_TOKEN.
"""

import base64
import os
import re
import time

import pandas as pd
from langdetect import detect_langs, DetectorFactory, LangDetectException

DetectorFactory.seed = 0  # deterministic langdetect

ENGLISH_THRESHOLD = 0.80

_CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`]*`")
_URL = re.compile(r"https?://\S+")
_MD_NOISE = re.compile(r"[#>*\-_=|\[\]()!]+")


def _clean_readme(md):
    md = _CODE_FENCE.sub(" ", md)
    md = _INLINE_CODE.sub(" ", md)
    md = _URL.sub(" ", md)
    md = _MD_NOISE.sub(" ", md)
    return md


def _english_share(md):
    cleaned = _clean_readme(md)
    lines = [ln.strip() for ln in cleaned.splitlines()]
    lines = [ln for ln in lines if len(re.sub(r"[^a-zA-Z]", "", ln)) >= 20]
    if not lines:
        try:
            for lang in detect_langs(cleaned):
                if lang.lang == "en":
                    return lang.prob
        except LangDetectException:
            pass
        return None
    en = 0
    for ln in lines:
        try:
            if detect_langs(ln)[0].lang == "en":
                en += 1
        except LangDetectException:
            continue
    return en / len(lines)


def _sleep_until_reset(resp, label="rate limit"):
    reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
    wait = max(reset - time.time(), 5) + 2
    mins = wait / 60.0
    print(f"  [{label}] waiting {wait:.0f}s ({mins:.1f}m) for quota reset...", flush=True)
    time.sleep(wait)


def _fetch_and_detect(full_name, headers):
    """Fetch README and return English share. Waits out rate limits indefinitely."""
    import requests
    url = f"https://api.github.com/repos/{full_name}/readme"
    transient = 0
    while True:
        try:
            r = requests.get(url, headers=headers, timeout=30)
        except requests.RequestException:
            transient += 1
            if transient > 5:
                return None, None
            time.sleep(min(2 ** transient, 30))
            continue

        # Rate limited (primary or secondary) -> wait for reset and retry forever
        if r.status_code in (403, 429):
            remaining = r.headers.get("X-RateLimit-Remaining")
            if remaining == "0" or "rate limit" in r.text.lower() or "secondary" in r.text.lower():
                _sleep_until_reset(r)
                continue
            return None, None  # 403 for another reason (e.g. blocked) -> skip
        if r.status_code == 404:
            return None, None
        if r.status_code != 200:
            transient += 1
            if transient > 5:
                return None, None
            time.sleep(min(2 ** transient, 30))
            continue

        data = r.json()
        content = base64.b64decode(data.get("content", "")).decode(errors="ignore")
        share = _english_share(content)
        # proactively pause if we're about to exhaust the quota
        if int(r.headers.get("X-RateLimit-Remaining", 100)) < 25:
            _sleep_until_reset(r, label="proactive throttle")
        lang = "en" if (share or 0) >= ENGLISH_THRESHOLD else ("non-en" if share is not None else None)
        return lang, share


def run_stage_b(survivors, phase2_dir):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN not set - cannot run Stage B.")
    headers = {"Authorization": f"token {token}",
               "Accept": "application/vnd.github+json"}

    cache_path = os.path.join(phase2_dir, "_stage_b_cache.csv")
    cache = {}
    if os.path.exists(cache_path):
        c = pd.read_csv(cache_path)
        cache = {row.full_name: (row.readme_lang, row.readme_lang_conf)
                 for row in c.itertuples()}
        print(f"  resuming Stage B: {len(cache)} cached results", flush=True)

    def flush_cache():
        pd.DataFrame(
            [{"full_name": k, "readme_lang": v[0], "readme_lang_conf": v[1]}
             for k, v in cache.items()]
        ).to_csv(cache_path, index=False)

    names = list(survivors["full_name"])
    for i, full in enumerate(names, 1):
        if full not in cache:
            cache[full] = _fetch_and_detect(full, headers)
            if i % 50 == 0:
                flush_cache()
                print(f"  {i}/{len(names)} processed", flush=True)
    flush_cache()

    res = pd.DataFrame(
        [{"full_name": k, "readme_lang": v[0], "readme_lang_conf": v[1]}
         for k, v in cache.items()]
    )
    survivors = survivors.merge(res, on="full_name", how="left")

    # Pass if English share >= threshold. Missing/undetectable READMEs are KEPT
    # (benefit of the doubt - they already cleared the Stage-A content gate).
    conf = survivors["readme_lang_conf"].fillna(1.0)
    is_en = survivors["readme_lang"].isna() | (conf >= ENGLISH_THRESHOLD)
    n_before = len(survivors)
    kept = survivors[is_en].copy()
    funnel = [("Stage B - Language gate (>=80% English)", len(kept), n_before - len(kept))]
    return kept, funnel
