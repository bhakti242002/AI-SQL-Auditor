-- Category: in_instead_of_exists | Variant 3
SELECT o.o_orderkey, o.o_totalprice
FROM orders o
WHERE o.o_custkey IN (
    SELECT c.c_custkey FROM customer c WHERE c.c_mktsegment = 'FURNITURE'
);
