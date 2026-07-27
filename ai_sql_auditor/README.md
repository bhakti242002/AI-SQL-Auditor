# AI SQL Auditor — Does AI's SQL advice actually hold up, at scale?

**The question:** AI coding assistants constantly suggest SQL "optimizations."
Nobody checks if they're actually right. This project does — across 120
queries, not just a handful.

**The method:** A templated generator (`generate_queries.py`) programmatically
produces 120 TPC-H-style analytical queries spanning **15 well-known categories
of real-world SQL anti-patterns** (8 varied instances of each): correlated
subqueries, `SELECT *` on wide joins, `NOT IN` with nulls, functions wrapped
around filter columns, missing indexes on range filters, `OR` conditions that
block index use, leading-wildcard `LIKE`, implicit type casts, incomplete
join conditions, `DISTINCT` masking join fan-out, N+1-style subqueries in the
SELECT list, unnecessary sorts before a small `LIMIT`, `IN` vs `EXISTS`,
inefficient self-joins, and `HAVING` used where `WHERE` would do.

Each of the 120 queries is sent to the Claude API for review, and each
suggested rewrite is then benchmarked against the original using Postgres's
`EXPLAIN ANALYZE` on real (synthetic) data — not just taken on faith.

**The output:** A results table / dashboard showing, per category: how often
AI flagged an issue, what it suggested, and whether the suggestion
*measurably* improved execution time — or didn't, broken down across all
15 anti-pattern categories rather than a handful of one-off examples.

**Why 120 and not fewer:** a small sample (e.g. 10) can only tell an anecdote.
120 queries across 15 defined categories lets you say something with actual
statistical shape — e.g. "AI's fixes for X category were reliable 90% of the
time, but for Y category they made things worse more often than not." That
category-level breakdown is the real finding, not just an overall percentage.

## Setup

1. **Install Postgres locally** (or use any reachable Postgres instance).
   Create a database:
   ```
   createdb sql_auditor
   psql -d sql_auditor -f schema.sql
   ```

2. **Generate and load synthetic data:**
   ```
   pip install faker --break-system-packages
   python generate_data.py
   psql -d sql_auditor -f load_data.sql
   ```
   This creates ~80k lineitem rows and proportional data in the other 7
   tables — enough for query plan differences to actually show up under
   EXPLAIN ANALYZE, without needing a huge dataset.

3. **Generate the 120-query test set:**
   ```
   python generate_queries.py
   ```
   This writes 120 `.sql` files into `queries/`, 8 variants each across
   15 anti-pattern categories (named `c01_...` through `c15_...`).

4. **Run the AI audit:**
   ```
   pip install anthropic --break-system-packages
   export ANTHROPIC_API_KEY="your-key-here"
   python ai_audit.py
   ```
   This sends each of the 120 queries in `queries/` to Claude and saves
   structured findings to `results/ai_audit_results.json`. At 120 queries
   with a 1-second pause between calls, expect this to take **~2-3 minutes**,
   and cost roughly **$0.50–$2** in API credits depending on query length —
   top up your Anthropic console credits accordingly before running.

5. **Verify the AI's suggestions against real query plans:**
   ```
   pip install psycopg2-binary --break-system-packages
   python verify_with_explain.py
   ```
   This runs `EXPLAIN (ANALYZE, FORMAT JSON)` on the original and
   AI-rewritten version of every query and records the verdict:
   `IMPROVED`, `WORSE`, `NO_MEANINGFUL_CHANGE`, or `COULD_NOT_VERIFY`
   (e.g. if the AI's rewrite had a SQL syntax error — worth flagging on
   its own).

6. **Load `results/verified_results.csv` into Power BI** and build:
   - A summary card: % of AI suggestions that measurably improved performance
     (overall, across all 120)
   - **A breakdown by category** (`filename` prefix `c01`–`c15`, or split
     `issue_type` out into its own column) — this is the most important
     visual, since "AI is 60% reliable overall" is far less useful than
     "AI is 90% reliable on missing-index issues but only 30% reliable on
     join-fanout issues"
   - A before/after execution-time comparison chart, faceted or filterable
     by category
   - A callout for any `COULD_NOT_VERIFY` cases — these are important:
     it means the AI's suggested SQL didn't even run, which is a finding
     in itself.

## Writing up the results

For your resume / portfolio page, the finding you want to highlight is the
category-level breakdown, not just one overall number: e.g. *"Audited 120
SQL queries across 15 anti-pattern categories using Claude. AI flagged an
issue in the large majority of queries, but verified performance impact via
EXPLAIN ANALYZE varied sharply by category — reliable fixes for some issue
types, and suggestions that measurably underperformed or failed to execute
for others."* Fill in your actual numbers once you have them — that's a
stronger, more specific claim than a single aggregate percentage, and it
shows you did a structured comparison rather than a handful of anecdotes.

## Optional supplement: real-world queries (qualitative only)

For extra credibility, you can also pull genuine open-source SQL files and
have Claude review them — clearly labeled as a separate, unverified
supplement (these use a different schema than your sandbox, so they can't
be run through `EXPLAIN ANALYZE`):

```
pip install requests --break-system-packages
python fetch_real_world_queries.py      # pulls real .sql files from dbt-labs' public "jaffle shop" demo project via GitHub's API
python audit_real_world.py              # sends them to Claude for style/pattern review only
```

This writes `results/real_world_review.json`. **Important:** when you write
this up, be explicit that this part is AI-review-only, with no execution
verification — don't blend these findings into your 120-query verified
numbers. Presented honestly, it's a nice add-on ("I also spot-checked
against real open-source SQL, not just synthetic benchmark queries") without
overstating what was actually verified.

## Notes / things to be upfront about if asked in an interview

- 120 queries across 15 categories (8 variants each) is a solid scale for
  a portfolio project, but it's still a synthetic benchmark on synthetic
  data — say so if asked. It's not a claim about every possible SQL
  pattern or every LLM.
- Results will vary by model and by how the prompt is worded — mention
  which model you used (Claude Sonnet) and that results aren't necessarily
  representative of every LLM or every prompting strategy.
