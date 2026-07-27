"""
Sends each real-world .sql file (pulled via fetch_real_world_queries.py) to
Claude for review. UNLIKE ai_audit.py, this does NOT attempt to verify
suggestions with EXPLAIN ANALYZE, because these queries reference a schema
(the dbt jaffle_shop models) that doesn't exist in your local sql_auditor
database. This is a qualitative supplement only -- label it as such in your
write-up.

Usage:
    python audit_real_world.py
"""

import os
import json
import glob
import time
import anthropic

QUERIES_DIR = "real_world_queries"
OUTPUT_PATH = "results/real_world_review.json"
MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a senior analytics engineer reviewing a real-world SQL file
from an open-source dbt project. You do NOT have the full schema, so focus on
style, readability, maintainability, and any performance patterns that are
evident from the query text alone (e.g. correlated subqueries, SELECT *,
non-sargable filters, redundant joins).

Respond with ONLY a JSON object (no markdown fences, no preamble):
{
  "issues_found": true or false,
  "issue_type": "short label, or 'none'",
  "severity": "low" | "medium" | "high",
  "explanation": "1-2 sentence explanation",
  "confidence_note": "1 short sentence on how confident this assessment can be without the full schema/data"
}
"""


def audit_query(client, query_text, filename):
    user_msg = f"QUERY FILE ({filename}):\n{query_text}\n\nReview this query."
    resp = client.messages.create(
        model=MODEL,
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw_text = "".join(b.text for b in resp.content if b.type == "text")
    cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"issues_found": None, "issue_type": "PARSE_ERROR", "raw_response": raw_text}


def main():
    client = anthropic.Anthropic()
    files = sorted(glob.glob(os.path.join(QUERIES_DIR, "*.sql")))
    if not files:
        print(f"No .sql files found in {QUERIES_DIR}/ -- run fetch_real_world_queries.py first.")
        return

    os.makedirs("results", exist_ok=True)
    results = {}
    for fpath in files:
        name = os.path.basename(fpath)
        print(f"Reviewing {name}...")
        with open(fpath) as f:
            text = f.read()
        result = audit_query(client, text, name)
        result["filename"] = name
        results[name] = result
        time.sleep(1)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDone. Wrote {len(results)} qualitative reviews to {OUTPUT_PATH}")
    print("Reminder: these are AI-review-only findings, NOT verified via EXPLAIN ANALYZE.")


if __name__ == "__main__":
    main()
