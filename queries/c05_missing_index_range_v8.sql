-- Category: missing_index_range | Variant 8
SELECT SUM(l.l_extendedprice * l.l_discount) AS revenue_impact
FROM lineitem l
WHERE l.l_shipdate >= '2024-06-01'
  AND l.l_shipdate < '2025-01-01'
  AND l.l_discount BETWEEN 0.06 AND 0.09
  AND l.l_quantity < 24;
