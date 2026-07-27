-- Category: incomplete_join_condition | Variant 7
SELECT l.l_orderkey, s.s_name, l.l_extendedprice
FROM lineitem l, supplier s
WHERE l.l_suppkey = s.s_suppkey
  AND l.l_shipdate BETWEEN '2022-01-01' AND '2022-12-31';
