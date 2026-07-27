-- Category: leading_wildcard_like | Variant 5
SELECT c.c_custkey, c.c_name
FROM customer c
WHERE c.c_name LIKE '%el%';
