-- Simplified TPC-H style schema
-- Based on the standard TPC-H benchmark table structure (8 core tables)

DROP TABLE IF EXISTS lineitem, orders, customer, partsupp, part, supplier, nation, region CASCADE;

CREATE TABLE region (
    r_regionkey INT PRIMARY KEY,
    r_name      VARCHAR(25),
    r_comment   VARCHAR(152)
);

CREATE TABLE nation (
    n_nationkey INT PRIMARY KEY,
    n_name      VARCHAR(25),
    n_regionkey INT REFERENCES region(r_regionkey),
    n_comment   VARCHAR(152)
);

CREATE TABLE supplier (
    s_suppkey   INT PRIMARY KEY,
    s_name      VARCHAR(25),
    s_nationkey INT REFERENCES nation(n_nationkey),
    s_acctbal   NUMERIC(12,2)
);

CREATE TABLE part (
    p_partkey   INT PRIMARY KEY,
    p_name      VARCHAR(55),
    p_type      VARCHAR(25),
    p_retailprice NUMERIC(12,2)
);

CREATE TABLE partsupp (
    ps_partkey  INT REFERENCES part(p_partkey),
    ps_suppkey  INT REFERENCES supplier(s_suppkey),
    ps_availqty INT,
    ps_supplycost NUMERIC(12,2),
    PRIMARY KEY (ps_partkey, ps_suppkey)
);

CREATE TABLE customer (
    c_custkey   INT PRIMARY KEY,
    c_name      VARCHAR(25),
    c_nationkey INT REFERENCES nation(n_nationkey),
    c_acctbal   NUMERIC(12,2),
    c_mktsegment VARCHAR(10)
);

CREATE TABLE orders (
    o_orderkey   INT PRIMARY KEY,
    o_custkey    INT REFERENCES customer(c_custkey),
    o_orderstatus CHAR(1),
    o_totalprice NUMERIC(12,2),
    o_orderdate  DATE,
    o_orderpriority VARCHAR(15)
);

CREATE TABLE lineitem (
    l_orderkey  INT REFERENCES orders(o_orderkey),
    l_partkey   INT REFERENCES part(p_partkey),
    l_suppkey   INT REFERENCES supplier(s_suppkey),
    l_linenumber INT,
    l_quantity  NUMERIC(12,2),
    l_extendedprice NUMERIC(12,2),
    l_discount  NUMERIC(12,2),
    l_shipdate  DATE,
    PRIMARY KEY (l_orderkey, l_linenumber)
);

-- NOTE: Intentionally NOT adding secondary indexes here beyond primary keys.
-- Missing indexes on foreign key / filter columns (l_shipdate, o_orderdate,
-- c_mktsegment, etc.) is one of the realistic performance issues we want
-- the AI to potentially catch -- so don't "fix" this before running the audit.
