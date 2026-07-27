-- Category: incomplete_join_condition | Variant 4
SELECT l.l_orderkey, s.s_name, l.l_extendedprice
FROM lineitem l, supplier s
WHERE l.l_suppkey = s.s_suppkey
  AND l.l_shipdate BETWEEN '2023-06-01' AND '2024-06-01';
