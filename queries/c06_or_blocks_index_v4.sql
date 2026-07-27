-- Category: or_blocks_index | Variant 4
SELECT o.o_orderkey, o.o_totalprice, o.o_orderstatus
FROM orders o
WHERE o.o_orderstatus = 'O' OR o.o_totalprice > 10000;
