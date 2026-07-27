-- Run with: psql -d sql_auditor -f load_data.sql
-- (run generate_data.py first so the .tsv files exist in this directory)

\copy region FROM 'region.tsv'
\copy nation FROM 'nation.tsv'
\copy supplier FROM 'supplier.tsv'
\copy part FROM 'part.tsv'
\copy partsupp FROM 'partsupp.tsv'
\copy customer FROM 'customer.tsv'
\copy orders FROM 'orders.tsv'
\copy lineitem FROM 'lineitem.tsv'

ANALYZE;
