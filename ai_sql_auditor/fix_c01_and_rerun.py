"""
Fixes the missing-SELECT bug in category 1 (correlated_subquery), regenerates
just those 8 query files, and re-runs the AI audit ONLY for c01 files,
merging the new results into the existing results/ai_audit_results.json
(so you don't pay to re-audit all 120 queries again).

After running this, just re-run verify_with_explain.py (free, local only)
to refresh the full CSV with corrected c01 results.

Usage:
    python fix_c01_and_rerun.py
"""

import os
import json
import glob
import time
import anthropic

QUERIES_DIR = "queries"
RESULTS_PATH = "results/ai_audit_results.json"
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

priorities = ["1-URGENT", "2-HIGH", "3-MEDIUM", "4-NOT SPECIFIED", "5-LOW"]
aggs = ["SUM", "AVG", "COUNT"]


def regenerate_c01():
    combos = [(p, a) for p in priorities for a in aggs][:8]
    for i, (priority, agg) in enumerate(combos, 1):
        expr = f"{agg}(l.l_extendedprice * (1 - l.l_discount))" if agg != "COUNT" else "COUNT(*)"
        sql = f"""
SELECT n.n_name,
       (SELECT {expr}
        FROM lineitem l
        JOIN orders o ON o.o_orderkey = l.l_orderkey
        JOIN customer c ON c.c_custkey = o.o_custkey
        WHERE c.c_nationkey = n.n_nationkey
          AND o.o_orderpriority = '{priority}') AS metric
FROM nation n
ORDER BY metric DESC NULLS LAST;
"""
        fname = f"c01_correlated_subquery_v{i}.sql"
        with open(os.path.join(QUERIES_DIR, fname), "w") as f:
            f.write(f"-- Category: correlated_subquery | Variant {i} (fixed: added missing SELECT)\n")
            f.write(sql.strip() + "\n")
    print("Regenerated 8 fixed c01 query files.")


def load_schema():
    with open("schema.sql") as f:
        return f.read()


def audit_query(client, schema, query_text, filename):
    user_msg = f"SCHEMA:\n{schema}\n\nQUERY ({filename}):\n{query_text}\n\nAnalyze this query for performance and style issues given the schema above."
    resp = client.messages.create(
        model=MODEL, max_tokens=1000, system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw_text = "".join(b.text for b in resp.content if b.type == "text")
    cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"issues_found": None, "issue_type": "PARSE_ERROR", "raw_response": raw_text}


def main():
    regenerate_c01()

    with open(RESULTS_PATH) as f:
        all_results = json.load(f)

    client = anthropic.Anthropic()
    schema = load_schema()

    c01_files = sorted(glob.glob(os.path.join(QUERIES_DIR, "c01_*.sql")))
    for qf in c01_files:
        name = os.path.basename(qf)
        print(f"Re-auditing {name}...")
        with open(qf) as f:
            query_text = f.read()
        result = audit_query(client, schema, query_text, name)
        result["original_query"] = query_text
        result["filename"] = name
        all_results[name] = result
        time.sleep(1)

    with open(RESULTS_PATH, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nDone. Updated {len(c01_files)} c01 entries in {RESULTS_PATH}")
    print("Now run: python verify_with_explain.py  (free, refreshes the full CSV)")


if __name__ == "__main__":
    main()
