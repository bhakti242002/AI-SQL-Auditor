-- Category: subquery_in_select | Variant 5
SELECT p.p_partkey, p.p_name,
       (SELECT MIN(ps.ps_supplycost) FROM partsupp ps WHERE ps.ps_partkey = p.p_partkey) AS min_cost,
       (SELECT MAX(ps.ps_supplycost) FROM partsupp ps WHERE ps.ps_partkey = p.p_partkey) AS max_cost
FROM part p
ORDER BY p.p_retailprice ASC
LIMIT 50;
