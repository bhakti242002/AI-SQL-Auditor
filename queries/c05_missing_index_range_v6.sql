-- Category: missing_index_range | Variant 6
SELECT SUM(l.l_extendedprice * l.l_discount) AS revenue_impact
FROM lineitem l
WHERE l.l_shipdate >= '2023-06-01'
  AND l.l_shipdate < '2024-01-01'
  AND l.l_discount BETWEEN 0.05 AND 0.07
  AND l.l_quantity < 24;
