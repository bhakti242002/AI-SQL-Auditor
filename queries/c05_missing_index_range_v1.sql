-- Category: missing_index_range | Variant 1
SELECT SUM(l.l_extendedprice * l.l_discount) AS revenue_impact
FROM lineitem l
WHERE l.l_shipdate >= '2023-01-01'
  AND l.l_shipdate < '2023-06-01'
  AND l.l_discount BETWEEN 0.02 AND 0.04
  AND l.l_quantity < 24;
