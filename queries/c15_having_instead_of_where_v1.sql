-- Category: having_instead_of_where | Variant 1
SELECT o.o_custkey, SUM(o.o_totalprice) AS total
FROM orders o
GROUP BY o.o_custkey
HAVING o.o_custkey > 0 AND SUM(o.o_totalprice) > 1000;
