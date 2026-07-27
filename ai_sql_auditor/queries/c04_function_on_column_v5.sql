-- Category: function_on_column | Variant 5
SELECT c.c_name, SUM(o.o_totalprice) AS total_spent
FROM customer c
JOIN orders o ON o.o_custkey = c.c_custkey
WHERE UPPER(c.c_mktsegment) = 'AUTOMOBILE'
GROUP BY c.c_name
ORDER BY total_spent DESC
LIMIT 20;
