"""
Pulls real-world .sql files from a public GitHub repo via the GitHub API
(no cloning, no auth required for this small a pull) and saves them into
real_world_queries/.

These are used ONLY for a qualitative AI-review supplement (see
audit_real_world.py) -- NOT for the EXPLAIN ANALYZE verification, since
they reference a different schema than schema.sql and cannot be executed
against your local sql_auditor database.

Usage:
    pip install requests --break-system-packages
    python fetch_real_world_queries.py
"""

import os
import requests

OUT_DIR = "real_world_queries"
os.makedirs(OUT_DIR, exist_ok=True)

# A well-known, real, public dbt demo project (dbt-labs' own "jaffle shop"
# example) -- genuine analytics SQL written by dbt-labs, not synthetic.
REPO = "dbt-labs/jaffle-shop-classic"
BRANCH = "main"

TREE_URL = f"https://api.github.com/repos/{REPO}/git/trees/{BRANCH}?recursive=1"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/"


def main():
    print(f"Fetching file tree for {REPO}...")
    resp = requests.get(TREE_URL, headers={"Accept": "application/vnd.github+json"})
    resp.raise_for_status()
    tree = resp.json()["tree"]

    sql_paths = [item["path"] for item in tree if item["path"].endswith(".sql")]
    print(f"Found {len(sql_paths)} .sql files. Downloading...")

    count = 0
    for path in sql_paths:
        raw_url = RAW_BASE + path
        r = requests.get(raw_url)
        if r.status_code != 200:
            print(f"  skipped (fetch failed): {path}")
            continue
        safe_name = path.replace("/", "__")
        with open(os.path.join(OUT_DIR, safe_name), "w") as f:
            f.write(f"-- Source: https://github.com/{REPO}/blob/{BRANCH}/{path}\n")
            f.write(r.text)
        count += 1
        print(f"  saved: {safe_name}")

    print(f"\nDone. Saved {count} real-world SQL files to {OUT_DIR}/")
    print("These will be used for AI-review-only analysis (no execution verification).")


if __name__ == "__main__":
    main()
