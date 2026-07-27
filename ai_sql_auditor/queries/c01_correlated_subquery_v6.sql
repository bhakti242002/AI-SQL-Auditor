-- Category: correlated_subquery | Variant 6
SELECT n.n_name,
       (COUNT(*)
        FROM lineitem l
        JOIN orders o ON o.o_orderkey = l.l_orderkey
        JOIN customer c ON c.c_custkey = o.o_custkey
        WHERE c.c_nationkey = n.n_nationkey
          AND o.o_orderpriority = '2-HIGH') AS metric
FROM nation n
ORDER BY metric DESC NULLS LAST;
