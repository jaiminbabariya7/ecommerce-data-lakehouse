"""
Synthetic e-commerce data generator.
Produces realistic customers, products, orders, and order_items CSVs
for loading into BigQuery. Supports configurable record counts and
date ranges.

Usage:
    python scripts/generate_data.py --customers 5000 --orders 50000 --out data/
"""
from __future__ import annotations
import argparse, csv, os, random, uuid
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

COUNTRIES   = ["United States","United Kingdom","Germany","France","Canada","Australia","India","Brazil"]
CITIES      = {"United States":["New York","Los Angeles","Chicago"],"United Kingdom":["London","Manchester"],"Germany":["Berlin","Munich"],"France":["Paris","Lyon"],"Canada":["Toronto","Vancouver"],"Australia":["Sydney","Melbourne"],"India":["Mumbai","Bangalore"],"Brazil":["São Paulo","Rio"]}
CHANNELS    = ["online","store","mobile","marketplace"]
STATUSES    = ["completed","completed","completed","shipped","cancelled","pending"]
CATEGORIES  = ["Electronics","Clothing","Books","Home & Garden","Sports","Beauty","Toys","Food"]
ADJECTIVES  = ["Pro","Ultra","Eco","Smart","Premium","Classic","Lite","Max"]
NOUNS       = ["Widget","Gadget","Device","Kit","Set","Pack","Bundle","Edition"]

START_DATE  = date(2022, 1, 1)
END_DATE    = date(2024, 12, 31)
DATE_RANGE  = (END_DATE - START_DATE).days


def rand_date() -> date:
    return START_DATE + timedelta(days=random.randint(0, DATE_RANGE))


def generate_customers(n: int) -> list[dict]:
    rows = []
    for _ in range(n):
        country = random.choice(COUNTRIES)
        city    = random.choice(CITIES.get(country, ["Unknown"]))
        rows.append({
            "customer_id":       str(uuid.uuid4()),
            "first_name":        random.choice(["Alice","Bob","Carol","David","Eve","Frank","Grace","Hank","Iris","Jack"]),
            "last_name":         random.choice(["Smith","Jones","Williams","Brown","Taylor","Davies","Wilson","Evans","Thomas","Roberts"]),
            "email":             f"user{random.randint(1,99999)}@example.com",
            "country":           country,
            "city":              city,
            "registration_date": str(rand_date()),
            "is_active":         random.random() > 0.1,
        })
    return rows


def generate_products(n: int) -> list[dict]:
    rows = []
    for _ in range(n):
        unit_price = round(random.uniform(5, 500), 2)
        unit_cost  = round(unit_price * random.uniform(0.4, 0.75), 2)
        rows.append({
            "product_id":   str(uuid.uuid4()),
            "product_name": f"{random.choice(ADJECTIVES)} {random.choice(NOUNS)} {random.randint(100,999)}",
            "category":     random.choice(CATEGORIES),
            "unit_price":   unit_price,
            "unit_cost":    unit_cost,
        })
    return rows


def generate_orders(n: int, customers: list[dict], products: list[dict]) -> tuple[list[dict], list[dict]]:
    orders, items = [], []
    for _ in range(n):
        customer    = random.choice(customers)
        order_date  = rand_date()
        num_items   = random.choices([1,2,3,4,5], weights=[40,30,15,10,5])[0]
        order_items = random.sample(products, k=min(num_items, len(products)))
        net_revenue = 0.0
        order_id    = str(uuid.uuid4())
        for product in order_items:
            qty      = random.randint(1, 5)
            disc     = round(random.choice([0,0,0,0.05,0.1,0.15,0.2]), 2)
            revenue  = round(product["unit_price"] * qty * (1 - disc), 2)
            net_revenue += revenue
            items.append({
                "item_id":     str(uuid.uuid4()),
                "order_id":    order_id,
                "product_id":  product["product_id"],
                "quantity":    qty,
                "unit_price":  product["unit_price"],
                "discount_pct": disc,
                "line_revenue": revenue,
            })
        orders.append({
            "order_id":    order_id,
            "customer_id": customer["customer_id"],
            "order_date":  str(order_date),
            "status":      random.choice(STATUSES),
            "channel":     random.choice(CHANNELS),
            "net_revenue": round(net_revenue, 2),
        })
    return orders, items


def write_csv(rows: list[dict], path: str) -> None:
    if not rows:
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows):,} rows → {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--customers", type=int, default=5_000)
    parser.add_argument("--products",  type=int, default=500)
    parser.add_argument("--orders",    type=int, default=50_000)
    parser.add_argument("--out",       default="data")
    args = parser.parse_args()

    print("Generating data...")
    customers = generate_customers(args.customers)
    products  = generate_products(args.products)
    orders, items = generate_orders(args.orders, customers, products)

    write_csv(customers, f"{args.out}/customers.csv")
    write_csv(products,  f"{args.out}/products.csv")
    write_csv(orders,    f"{args.out}/orders.csv")
    write_csv(items,     f"{args.out}/order_items.csv")
    print("Done.")