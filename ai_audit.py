"""
Sends each .sql file in queries/ to the Claude API, asking it to identify
performance/style issues and propose a rewritten version.

Requires: pip install anthropic --break-system-packages
Set your API key: export ANTHROPIC_API_KEY="sk-ant-..."

Usage:
    python ai_audit.py
"""

import os
import json
import glob
import time
import anthropic

SCHEMA_PATH = "schema.sql"
QUERIES_DIR = "queries"
OUTPUT_PATH = "results/ai_audit_results.json"

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a senior database performance engineer reviewing SQL queries.
You will be given a table schema and a single SQL query written against it.

Respond with ONLY a JSON object (no markdown fences, no preamble) with this exact shape:
{
  "issues_found": true or false,
  "issue_type": "one short label, e.g. 'correlated subquery', 'select *', 'NOT IN with nulls', 'function on filter column', 'none'",
  "severity": "low" | "medium" | "high",
  "explanation": "1-2 sentence plain explanation of the issue and why it matters for performance",
  "rewritten_query": "the improved SQL query as a single string, or the original unchanged if no issues found"
}
"""


def load_schema():
    with open(SCHEMA_PATH) as f:
        return f.read()


def audit_query(client, schema, query_text, filename):
    user_msg = f"""SCHEMA:
{schema}

QUERY ({filename}):
{query_text}

Analyze this query for performance and style issues given the schema above."""

    resp = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    raw_text = "".join(block.text for block in resp.content if block.type == "text")
    cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "issues_found": None,
            "issue_type": "PARSE_ERROR",
            "severity": None,
            "explanation": "Could not parse model response as JSON.",
            "rewritten_query": None,
            "raw_response": raw_text,
        }


def main():
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    schema = load_schema()

    query_files = sorted(glob.glob(os.path.join(QUERIES_DIR, "*.sql")))
    results = {}

    os.makedirs("results", exist_ok=True)

    for qf in query_files:
        name = os.path.basename(qf)
        print(f"Auditing {name}...")
        with open(qf) as f:
            query_text = f.read()

        result = audit_query(client, schema, query_text, name)
        result["original_query"] = query_text
        result["filename"] = name
        results[name] = result

        time.sleep(1)  # be polite to rate limits

    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nDone. Wrote {len(results)} results to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
