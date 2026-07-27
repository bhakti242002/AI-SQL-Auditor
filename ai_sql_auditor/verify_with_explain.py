"""
Loads results/ai_audit_results.json, runs EXPLAIN ANALYZE on both the
original and the AI-suggested rewrite for every query, and records whether
the suggestion actually improved execution time / planning cost.

Requires: pip install psycopg2-binary --break-system-packages
Set connection info via env vars or edit DB_DSN below.

Usage:
    python verify_with_explain.py
"""

import os
import re
import json
import psycopg2
DB_DSN = os.environ.get("SQL_AUDITOR_DSN", "dbname=sql_auditor user=postgres password=2406")
INPUT_PATH = "results/ai_audit_results.json"
OUTPUT_PATH = "results/verified_results.json"
OUTPUT_CSV = "results/verified_results.csv"


def get_explain_stats(cur, query):
    """Run EXPLAIN (ANALYZE, FORMAT JSON) and pull out total time + planning cost."""
    try:
        cur.execute("EXPLAIN (ANALYZE, FORMAT JSON) " + query)
        plan = cur.fetchone()[0][0]
        return {
            "planning_time_ms": plan.get("Planning Time"),
            "execution_time_ms": plan.get("Execution Time"),
            "total_cost": plan["Plan"].get("Total Cost"),
            "error": None,
        }
    except Exception as e:
        return {"planning_time_ms": None, "execution_time_ms": None, "total_cost": None, "error": str(e)}


def verdict(original_stats, rewritten_stats):
    if original_stats["error"] or rewritten_stats["error"]:
        return "COULD_NOT_VERIFY"
    orig_time = original_stats["execution_time_ms"]
    new_time = rewritten_stats["execution_time_ms"]
    if orig_time is None or new_time is None:
        return "COULD_NOT_VERIFY"
    improvement_pct = (orig_time - new_time) / orig_time * 100 if orig_time else 0
    if improvement_pct > 15:
        return f"IMPROVED ({improvement_pct:.1f}% faster)"
    elif improvement_pct < -15:
        return f"WORSE ({-improvement_pct:.1f}% slower)"
    else:
        return "NO_MEANINGFUL_CHANGE"


def main():
    with open(INPUT_PATH) as f:
        audit_results = json.load(f)

    conn = psycopg2.connect(DB_DSN)
    conn.autocommit = True
    cur = conn.cursor()

    verified = {}
    for name, entry in audit_results.items():
        print(f"Verifying {name}...")
        original_stats = get_explain_stats(cur, entry["original_query"])

        if entry.get("issues_found") and entry.get("rewritten_query"):
            rewritten_stats = get_explain_stats(cur, entry["rewritten_query"])
        else:
            rewritten_stats = original_stats  # no change suggested

        entry["original_stats"] = original_stats
        entry["rewritten_stats"] = rewritten_stats
        entry["verdict"] = verdict(original_stats, rewritten_stats)
        verified[name] = entry

    with open(OUTPUT_PATH, "w") as f:
        json.dump(verified, f, indent=2)

    # Also write a flat CSV for easy Power BI import
    import csv
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "filename", "category", "issue_type", "severity", "issues_found",
            "orig_exec_ms", "rewritten_exec_ms", "verdict"
        ])
        for name, e in verified.items():
            # filenames look like c04_function_on_column_v5.sql -> category = function_on_column
            category = re.sub(r"^c\d+_", "", name)
            category = re.sub(r"_v\d+\.sql$", "", category)
            writer.writerow([
                name, category, e.get("issue_type"), e.get("severity"), e.get("issues_found"),
                e["original_stats"].get("execution_time_ms"),
                e["rewritten_stats"].get("execution_time_ms"),
                e.get("verdict"),
            ])

    print(f"\nDone. Wrote {OUTPUT_PATH} and {OUTPUT_CSV}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
