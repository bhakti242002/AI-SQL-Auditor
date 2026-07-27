"""
Generates synthetic data matching schema.sql (TPC-H style).
Sizes are chosen so query plan differences are actually visible under
EXPLAIN ANALYZE without needing gigabytes of data.

Usage:
    pip install faker psycopg2-binary --break-system-packages
    python generate_data.py
"""

import random
import datetime
from faker import Faker

fake = Faker()
random.seed(42)

N_REGIONS = 5
N_NATIONS = 25
N_SUPPLIERS = 500
N_PARTS = 2000
N_CUSTOMERS = 5000
N_ORDERS = 20000
AVG_LINEITEMS_PER_ORDER = 4  # -> ~80k lineitem rows

MKT_SEGMENTS = ["AUTOMOBILE", "BUILDING", "FURNITURE", "MACHINERY", "HOUSEHOLD"]
ORDER_PRIORITIES = ["1-URGENT", "2-HIGH", "3-MEDIUM", "4-NOT SPECIFIED", "5-LOW"]
ORDER_STATUSES = ["O", "F", "P"]


def random_date(start_year=2020, end_year=2025):
    start = datetime.date(start_year, 1, 1)
    end = datetime.date(end_year, 12, 31)
    delta = (end - start).days
    return start + datetime.timedelta(days=random.randint(0, delta))


def write_copy_file(path, rows, cols):
    with open(path, "w") as f:
        for row in rows:
            f.write("\t".join(str(v) for v in row) + "\n")


def main():
    print("Generating region...")
    regions = [(i, f"REGION_{i}", fake.sentence()) for i in range(N_REGIONS)]

    print("Generating nation...")
    nations = [(i, f"NATION_{i}", random.randrange(N_REGIONS), fake.sentence()) for i in range(N_NATIONS)]

    print("Generating supplier...")
    suppliers = [(i, fake.company()[:25], random.randrange(N_NATIONS), round(random.uniform(-999, 9999), 2))
                 for i in range(N_SUPPLIERS)]

    print("Generating part...")
    parts = [(i, fake.word()[:55], random.choice(["STANDARD", "ECONOMY", "PROMO", "SMALL", "MEDIUM"]),
               round(random.uniform(1, 2000), 2)) for i in range(N_PARTS)]

    print("Generating partsupp...")
    partsupp = []
    for p in range(N_PARTS):
        for s in random.sample(range(N_SUPPLIERS), k=min(4, N_SUPPLIERS)):
            partsupp.append((p, s, random.randint(1, 9999), round(random.uniform(1, 1000), 2)))

    print("Generating customer...")
    customers = [(i, fake.name()[:25], random.randrange(N_NATIONS), round(random.uniform(-999, 9999), 2),
                  random.choice(MKT_SEGMENTS)) for i in range(N_CUSTOMERS)]

    print("Generating orders + lineitem...")
    orders = []
    lineitems = []
    for o in range(N_ORDERS):
        cust = random.randrange(N_CUSTOMERS)
        odate = random_date()
        orders.append((o, cust, random.choice(ORDER_STATUSES), 0, odate, random.choice(ORDER_PRIORITIES)))
        n_items = random.randint(1, AVG_LINEITEMS_PER_ORDER * 2 - 1)
        total = 0
        for ln in range(n_items):
            part = random.randrange(N_PARTS)
            supp = random.randrange(N_SUPPLIERS)
            qty = random.randint(1, 50)
            price = round(random.uniform(1, 2000), 2)
            discount = round(random.uniform(0, 0.1), 2)
            shipdate = odate + datetime.timedelta(days=random.randint(1, 60))
            lineitems.append((o, part, supp, ln, qty, price, discount, shipdate))
            total += qty * price * (1 - discount)
        orders[-1] = (o, cust, orders[-1][2], round(total, 2), odate, orders[-1][5])

    print("Writing .tsv files for COPY...")
    write_copy_file("region.tsv", regions, None)
    write_copy_file("nation.tsv", nations, None)
    write_copy_file("supplier.tsv", suppliers, None)
    write_copy_file("part.tsv", parts, None)
    write_copy_file("partsupp.tsv", partsupp, None)
    write_copy_file("customer.tsv", customers, None)
    write_copy_file("orders.tsv", orders, None)
    write_copy_file("lineitem.tsv", lineitems, None)

    print(f"Done. ~{len(lineitems)} lineitem rows, {len(orders)} orders generated.")
    print("Load into Postgres with load_data.sql (uses \\copy).")


if __name__ == "__main__":
    main()
