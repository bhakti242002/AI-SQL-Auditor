-- Category: or_blocks_index | Variant 3
SELECT o.o_orderkey, o.o_totalprice, o.o_orderstatus
FROM orders o
WHERE o.o_orderstatus = 'P' OR o.o_totalprice > 3000;
