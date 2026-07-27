-- Category: self_join_instead_of_window | Variant 5
SELECT p1.p_partkey, p1.p_name, p1.p_retailprice
FROM part p1
WHERE (
    SELECT COUNT(*) FROM part p2 WHERE p2.p_retailprice > p1.p_retailprice
) < 10;
