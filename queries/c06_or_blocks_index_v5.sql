-- Category: or_blocks_index | Variant 5
SELECT o.o_orderkey, o.o_totalprice, o.o_orderstatus
FROM orders o
WHERE o.o_orderstatus = 'F' OR o.o_totalprice > 2000;
