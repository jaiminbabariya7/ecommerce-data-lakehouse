"""Tests for the synthetic data generator (scripts/generate_data.py)."""
import os
import random
import sys
from collections import defaultdict
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import generate_data as g  # noqa: E402


def _dataset(seed=7):
    random.seed(seed)
    customers = g.generate_customers(50)
    products = g.generate_products(20)
    orders, items = g.generate_orders(300, customers, products)
    return customers, products, orders, items


def test_referential_integrity():
    customers, products, orders, items = _dataset()
    cust_ids = {c["customer_id"] for c in customers}
    prod_ids = {p["product_id"] for p in products}
    order_ids = {o["order_id"] for o in orders}
    assert all(o["customer_id"] in cust_ids for o in orders)
    assert all(i["order_id"] in order_ids for i in items)
    assert all(i["product_id"] in prod_ids for i in items)


def test_order_total_equals_sum_of_lines():
    _, _, orders, items = _dataset()
    lines = defaultdict(float)
    for i in items:
        lines[i["order_id"]] += i["line_revenue"]
    assert all(abs(o["net_revenue"] - lines[o["order_id"]]) <= 0.05 for o in orders)


def test_orders_not_before_registration():
    customers, _, orders, _ = _dataset()
    registered = {c["customer_id"]: c["registration_date"] for c in customers}
    assert all(date.fromisoformat(o["order_date"]) >= date.fromisoformat(registered[o["customer_id"]])
               for o in orders)


def test_unique_ids_and_emails():
    customers, products, orders, items = _dataset()
    for rows, key in [(customers, "customer_id"), (customers, "email"), (products, "product_id"),
                      (orders, "order_id"), (items, "item_id")]:
        values = [r[key] for r in rows]
        assert len(values) == len(set(values)), key


def test_same_seed_same_data():
    assert _dataset(seed=3) == _dataset(seed=3)
