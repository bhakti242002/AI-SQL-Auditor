-- Category: distinct_masks_fanout | Variant 1
SELECT DISTINCT c.c_custkey, c.c_name,
       COUNT(o.o_orderkey) OVER (PARTITION BY c.c_custkey) AS order_count
FROM customer c
JOIN orders o ON o.o_custkey = c.c_custkey
JOIN lineitem l ON l.l_orderkey = o.o_orderkey
WHERE c.c_acctbal > 0;
