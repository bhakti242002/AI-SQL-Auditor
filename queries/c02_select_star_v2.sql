-- Category: select_star | Variant 2
SELECT *
FROM lineitem l
JOIN orders o ON o.o_orderkey = l.l_orderkey
JOIN customer c ON c.c_custkey = o.o_custkey
WHERE l.l_shipdate > '2023-06-01'
  AND c.c_mktsegment = 'AUTOMOBILE';
