"""
database.py - SQLite helper for fashion products
"""

import sqlite3
import pandas as pd
import os
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "fashion.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_products_by_ids(product_ids):
    """Return list of product dicts for given product IDs."""
    if not product_ids:
        return []
    conn = get_connection()
    placeholders = ",".join("?" for _ in product_ids)
    rows = conn.execute(
        f"SELECT * FROM products WHERE ProductId IN ({placeholders})",
        [int(pid) for pid in product_ids],
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_product_by_id(product_id):
    """Return a single product dict."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM products WHERE ProductId = ?", (int(product_id),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_products(limit=None):
    """Return all products as a list of dicts."""
    conn = get_connection()
    query = "SELECT * FROM products"
    if limit:
        query += f" LIMIT {limit}"
    rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_featured_products(n=12):
    """Return random featured products for the homepage."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM products ORDER BY RANDOM() LIMIT ?", (n,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_categories():
    """Return distinct categories."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT Category, SubCategory FROM products ORDER BY Category"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
