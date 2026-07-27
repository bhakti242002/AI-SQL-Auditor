-- Category: sort_before_limit | Variant 1
SELECT l.l_orderkey, l.l_extendedprice, l.l_discount, l.l_shipdate
FROM lineitem l
ORDER BY l.l_shipdate, l.l_extendedprice DESC
LIMIT 5;
