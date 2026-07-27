-- Category: implicit_cast | Variant 5
SELECT s.s_suppkey, s.s_name
FROM supplier s
WHERE CAST(s.s_suppkey AS TEXT) = '250';
