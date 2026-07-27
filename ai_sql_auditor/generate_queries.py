"""
Generates 120 test queries (15 categories x 8 variants each) against the
schema in schema.sql. Each category represents a well-known, realistic SQL
performance/style issue. Variants within a category use different tables,
columns, thresholds, or operators so they are genuinely distinct queries,
not copies.

Usage:
    python generate_queries.py
Writes files into queries/ as c<NN>_<category>_v<N>.sql
"""

import os

OUT_DIR = "queries"
os.makedirs(OUT_DIR, exist_ok=True)


def w(category_num, category_name, variant_num, sql):
    fname = f"c{category_num:02d}_{category_name}_v{variant_num}.sql"
    with open(os.path.join(OUT_DIR, fname), "w") as f:
        f.write(f"-- Category: {category_name} | Variant {variant_num}\n")
        f.write(sql.strip() + "\n")


# ---------------------------------------------------------------------------
# C01: Correlated scalar subquery in SELECT list (should often be a JOIN/window)
# ---------------------------------------------------------------------------
priorities = ["1-URGENT", "2-HIGH", "3-MEDIUM", "4-NOT SPECIFIED", "5-LOW"]
aggs = ["SUM", "AVG", "COUNT"]
combos = [(p, a) for p in priorities for a in aggs][:8]
for i, (priority, agg) in enumerate(combos, 1):
    expr = f"{agg}(l.l_extendedprice * (1 - l.l_discount))" if agg != "COUNT" else "COUNT(*)"
    w(1, "correlated_subquery", i, f"""
SELECT n.n_name,
       (SELECT {expr}
        FROM lineitem l
        JOIN orders o ON o.o_orderkey = l.l_orderkey
        JOIN customer c ON c.c_custkey = o.o_custkey
        WHERE c.c_nationkey = n.n_nationkey
          AND o.o_orderpriority = '{priority}') AS metric
FROM nation n
ORDER BY metric DESC NULLS LAST;
""")

# ---------------------------------------------------------------------------
# C02: SELECT * on wide multi-join, filter applied late
# ---------------------------------------------------------------------------
segments = ["AUTOMOBILE", "BUILDING", "FURNITURE", "MACHINERY", "HOUSEHOLD"]
dates = ["2023-01-01", "2023-06-01", "2024-01-01", "2024-06-01"]
combos = [(s, d) for s in segments for d in dates][:8]
for i, (seg, d) in enumerate(combos, 1):
    w(2, "select_star", i, f"""
SELECT *
FROM lineitem l
JOIN orders o ON o.o_orderkey = l.l_orderkey
JOIN customer c ON c.c_custkey = o.o_custkey
WHERE l.l_shipdate > '{d}'
  AND c.c_mktsegment = '{seg}';
""")

# ---------------------------------------------------------------------------
# C03: NOT IN with a subquery that can return NULLs (classic footgun)
# ---------------------------------------------------------------------------
years = ["2021", "2022", "2023", "2024"]
statuses = ["O", "F"]
combos = [(y, s) for y in years for s in statuses][:8]
for i, (y, s) in enumerate(combos, 1):
    w(3, "not_in_nulls", i, f"""
SELECT o.o_orderpriority, COUNT(*) AS order_count
FROM orders o
WHERE o.o_orderkey NOT IN (
    SELECT l.l_orderkey FROM lineitem l WHERE l.l_discount > 0.5
)
AND o.o_orderdate >= '{y}-01-01'
AND o.o_orderstatus = '{s}'
GROUP BY o.o_orderpriority;
""")

# ---------------------------------------------------------------------------
# C04: Function wrapped around a filter column (breaks sargability)
# ---------------------------------------------------------------------------
funcs_years = [("EXTRACT(YEAR FROM o.o_orderdate)", "2021"),
               ("EXTRACT(YEAR FROM o.o_orderdate)", "2022"),
               ("EXTRACT(YEAR FROM o.o_orderdate)", "2023"),
               ("EXTRACT(YEAR FROM o.o_orderdate)", "2024"),
               ("UPPER(c.c_mktsegment)", "AUTOMOBILE"),
               ("UPPER(c.c_mktsegment)", "BUILDING"),
               ("EXTRACT(MONTH FROM o.o_orderdate)", "6"),
               ("EXTRACT(MONTH FROM o.o_orderdate)", "12")]
for i, (expr, val) in enumerate(funcs_years, 1):
    condition = f"{expr} = {val}" if "MONTH" in expr or "YEAR" in expr else f"{expr} = '{val}'"
    w(4, "function_on_column", i, f"""
SELECT c.c_name, SUM(o.o_totalprice) AS total_spent
FROM customer c
JOIN orders o ON o.o_custkey = c.c_custkey
WHERE {condition}
GROUP BY c.c_name
ORDER BY total_spent DESC
LIMIT 20;
""")

# ---------------------------------------------------------------------------
# C05: Range filter on an unindexed column, varying ranges/tables
# ---------------------------------------------------------------------------
ranges = [("l_shipdate", "2023-01-01", "2023-06-01"),
          ("l_shipdate", "2023-06-01", "2024-01-01"),
          ("l_shipdate", "2024-01-01", "2024-06-01"),
          ("l_shipdate", "2024-06-01", "2025-01-01")]
discount_ranges = [(0.02, 0.04), (0.05, 0.07), (0.03, 0.06), (0.06, 0.09)]
combos = list(zip(ranges * 2, discount_ranges * 2))[:8]
for i, ((col, d1, d2), (disc1, disc2)) in enumerate(combos, 1):
    w(5, "missing_index_range", i, f"""
SELECT SUM(l.l_extendedprice * l.l_discount) AS revenue_impact
FROM lineitem l
WHERE l.{col} >= '{d1}'
  AND l.{col} < '{d2}'
  AND l.l_discount BETWEEN {disc1} AND {disc2}
  AND l.l_quantity < 24;
""")

# ---------------------------------------------------------------------------
# C06: OR conditions across columns that block index usage
# ---------------------------------------------------------------------------
combos = [("O", 5000), ("F", 8000), ("P", 3000), ("O", 10000),
          ("F", 2000), ("P", 6000), ("O", 7500), ("F", 12000)]
for i, (status, amt) in enumerate(combos, 1):
    w(6, "or_blocks_index", i, f"""
SELECT o.o_orderkey, o.o_totalprice, o.o_orderstatus
FROM orders o
WHERE o.o_orderstatus = '{status}' OR o.o_totalprice > {amt};
""")

# ---------------------------------------------------------------------------
# C07: Leading wildcard LIKE (cannot use a b-tree index efficiently)
# ---------------------------------------------------------------------------
patterns = ["son", "ing", "co", "an", "el", "ar", "en", "or"]
for i, p in enumerate(patterns, 1):
    w(7, "leading_wildcard_like", i, f"""
SELECT c.c_custkey, c.c_name
FROM customer c
WHERE c.c_name LIKE '%{p}%';
""")

# ---------------------------------------------------------------------------
# C08: Implicit type casting in WHERE clause (varchar compared to number, etc.)
# ---------------------------------------------------------------------------
keys = [10, 25, 50, 100, 250, 500, 750, 1000]
for i, k in enumerate(keys, 1):
    w(8, "implicit_cast", i, f"""
SELECT s.s_suppkey, s.s_name
FROM supplier s
WHERE CAST(s.s_suppkey AS TEXT) = '{k}';
""")

# ---------------------------------------------------------------------------
# C09: Cartesian-risk join (join condition present but incomplete for multi-key FK)
# ---------------------------------------------------------------------------
combos = [("2023-01-01", "2023-12-31"), ("2024-01-01", "2024-12-31"),
          ("2022-01-01", "2022-12-31"), ("2023-06-01", "2024-06-01")] * 2
for i, (d1, d2) in enumerate(combos[:8], 1):
    w(9, "incomplete_join_condition", i, f"""
SELECT l.l_orderkey, s.s_name, l.l_extendedprice
FROM lineitem l, supplier s
WHERE l.l_suppkey = s.s_suppkey
  AND l.l_shipdate BETWEEN '{d1}' AND '{d2}';
""")

# ---------------------------------------------------------------------------
# C10: Redundant SELECT DISTINCT masking a join fan-out (should use aggregation/window)
# ---------------------------------------------------------------------------
balances = [0, 500, 1000, 2000, 3000, 5000, 7500, 10000]
for i, bal in enumerate(balances, 1):
    w(10, "distinct_masks_fanout", i, f"""
SELECT DISTINCT c.c_custkey, c.c_name,
       COUNT(o.o_orderkey) OVER (PARTITION BY c.c_custkey) AS order_count
FROM customer c
JOIN orders o ON o.o_custkey = c.c_custkey
JOIN lineitem l ON l.l_orderkey = o.o_orderkey
WHERE c.c_acctbal > {bal};
""")

# ---------------------------------------------------------------------------
# C11: Subquery in SELECT list executed per row (N+1 pattern)
# ---------------------------------------------------------------------------
combos = [("p_retailprice", "ASC"), ("p_retailprice", "DESC"),
          ("p_partkey", "ASC"), ("p_partkey", "DESC")] * 2
for i, (col, order) in enumerate(combos[:8], 1):
    w(11, "subquery_in_select", i, f"""
SELECT p.p_partkey, p.p_name,
       (SELECT MIN(ps.ps_supplycost) FROM partsupp ps WHERE ps.ps_partkey = p.p_partkey) AS min_cost,
       (SELECT MAX(ps.ps_supplycost) FROM partsupp ps WHERE ps.ps_partkey = p.p_partkey) AS max_cost
FROM part p
ORDER BY p.{col} {order}
LIMIT 50;
""")

# ---------------------------------------------------------------------------
# C12: Unnecessary ORDER BY on a huge intermediate result before a small LIMIT
# ---------------------------------------------------------------------------
limits = [5, 10, 15, 20, 25, 30, 40, 50]
for i, lim in enumerate(limits, 1):
    w(12, "sort_before_limit", i, f"""
SELECT l.l_orderkey, l.l_extendedprice, l.l_discount, l.l_shipdate
FROM lineitem l
ORDER BY l.l_shipdate, l.l_extendedprice DESC
LIMIT {lim};
""")

# ---------------------------------------------------------------------------
# C13: IN vs EXISTS -- large IN subquery instead of EXISTS/semi-join
# ---------------------------------------------------------------------------
combos = [("AUTOMOBILE",), ("BUILDING",), ("FURNITURE",), ("MACHINERY",),
          ("HOUSEHOLD",), ("AUTOMOBILE",), ("BUILDING",), ("FURNITURE",)]
for i, (seg,) in enumerate(combos, 1):
    w(13, "in_instead_of_exists", i, f"""
SELECT o.o_orderkey, o.o_totalprice
FROM orders o
WHERE o.o_custkey IN (
    SELECT c.c_custkey FROM customer c WHERE c.c_mktsegment = '{seg}'
);
""")

# ---------------------------------------------------------------------------
# C14: Inefficient self-referencing style join used instead of window function
# ---------------------------------------------------------------------------
combos = [(1,), (2,), (3,), (5,), (10,), (15,), (20,), (25,)]
for i, (n,) in enumerate(combos, 1):
    w(14, "self_join_instead_of_window", i, f"""
SELECT p1.p_partkey, p1.p_name, p1.p_retailprice
FROM part p1
WHERE (
    SELECT COUNT(*) FROM part p2 WHERE p2.p_retailprice > p1.p_retailprice
) < {n};
""")

# ---------------------------------------------------------------------------
# C15: GROUP BY / HAVING used where a WHERE clause would filter earlier and cheaper
# ---------------------------------------------------------------------------
thresholds = [1000, 2500, 5000, 7500, 10000, 15000, 20000, 25000]
for i, t in enumerate(thresholds, 1):
    w(15, "having_instead_of_where", i, f"""
SELECT o.o_custkey, SUM(o.o_totalprice) AS total
FROM orders o
GROUP BY o.o_custkey
HAVING o.o_custkey > 0 AND SUM(o.o_totalprice) > {t};
""")

print("Generated 120 queries across 15 categories in queries/")
