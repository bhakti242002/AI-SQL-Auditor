-- Category: function_on_column | Variant 3
SELECT c.c_name, SUM(o.o_totalprice) AS total_spent
FROM customer c
JOIN orders o ON o.o_custkey = c.c_custkey
WHERE EXTRACT(YEAR FROM o.o_orderdate) = 2023
GROUP BY c.c_name
ORDER BY total_spent DESC
LIMIT 20;
