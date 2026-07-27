-- Category: not_in_nulls | Variant 1
SELECT o.o_orderpriority, COUNT(*) AS order_count
FROM orders o
WHERE o.o_orderkey NOT IN (
    SELECT l.l_orderkey FROM lineitem l WHERE l.l_discount > 0.5
)
AND o.o_orderdate >= '2021-01-01'
AND o.o_orderstatus = 'O'
GROUP BY o.o_orderpriority;
