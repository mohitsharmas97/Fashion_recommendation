"""
setup_database.py
=================
Run this ONE TIME to:
  1. Read fashion.csv
  2. Create SQLite database (fashion.db) with products table
  3. Generate sentence embeddings and store in ChromaDB

Usage:
    python setup_database.py

Make sure fashion.csv is in this directory (copy it from the Kaggle dataset).
The image paths from the dataset's ImageURL column are used directly (Myntra CDN).
"""

import os
import sys

# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
import sqlite3
import pandas as pd
import random
import chromadb
from sentence_transformers import SentenceTransformer
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

CSV_PATH = os.path.join(os.path.dirname(__file__), "fashion.csv")
DB_PATH = os.path.join(os.path.dirname(__file__), "fashion.db")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")

# Price ranges for each product type (simulated since dataset has no prices)
PRICE_MAP = {
    "Shirts": (599, 2499),
    "Tshirts": (299, 1499),
    "Tops": (399, 1999),
    "Jeans": (799, 3499),
    "Trousers": (699, 2999),
    "Shorts": (399, 1499),
    "Skirts": (499, 1999),
    "Dresses": (699, 3999),
    "Leggings": (299, 999),
    "Track Pants": (499, 1499),
    "Sweatshirts": (599, 2499),
    "Jackets": (999, 5999),
    "Sweaters": (699, 2999),
    "Sandals": (399, 2499),
    "Casual Shoes": (699, 3999),
    "Sports Shoes": (799, 4999),
    "Heels": (699, 3499),
    "Flip Flops": (199, 799),
    "Flats": (399, 1999),
    "Sneakers": (699, 3999),
    "Loafers": (599, 2999),
}

DEFAULT_PRICE_RANGE = (499, 2999)


def generate_price(product_type):
    low, high = PRICE_MAP.get(product_type, DEFAULT_PRICE_RANGE)
    return random.randint(low // 100, high // 100) * 100


def create_text_description(row):
    """Create a rich text description for embedding."""
    parts = [
        row["ProductTitle"],
        f"Color: {row['Colour']}",
        f"Gender: {row['Gender']}",
        f"Category: {row['Category']}",
        f"Type: {row['ProductType']}",
        f"Sub-category: {row['SubCategory']}",
        f"Usage: {row['Usage']}",
        # Add synonyms for better search
        f"This is a {row['Colour'].lower()} {row['ProductType'].lower()} for {row['Gender'].lower()}.",
        f"Suitable for {row['Usage'].lower()} occasions.",
    ]
    return " | ".join(parts)


def setup():
    # ── 1. Validate CSV ──────────────────────────────────────
    if not os.path.exists(CSV_PATH):
        print(f"[X] fashion.csv not found at: {CSV_PATH}")
        print("    Please copy fashion.csv from the Kaggle dataset into this folder.")
        return

    print("[*] Loading fashion.csv...")
    df = pd.read_csv(CSV_PATH)
    print(f"    Loaded {len(df)} products.")

    # ── 2. Add simulated prices ──────────────────────────────
    random.seed(42)
    df["Price"] = df["ProductType"].apply(generate_price)
    df["Rating"] = [round(random.uniform(3.5, 5.0), 1) for _ in range(len(df))]
    df["Reviews"] = [random.randint(10, 500) for _ in range(len(df))]

    # ── 3. Create SQLite DB ──────────────────────────────────
    print("[*] Creating SQLite database (fashion.db)...")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("products", conn, if_exists="replace", index=False)
    conn.close()
    print(f"    Saved {len(df)} products to fashion.db.")

    # ── 4. Build ChromaDB vector store ───────────────────────
    print("[*] Loading Sentence Transformer model (all-MiniLM-L6-v2)...")
    model_name = "all-MiniLM-L6-v2"
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name=model_name)

    print("[*] Initializing ChromaDB...")
    if os.path.exists(CHROMA_PATH):
        import shutil
        shutil.rmtree(CHROMA_PATH)

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(
        name="fashion_products",
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    print("[*] Generating text embeddings for all products...")
    batch_size = 100
    total = len(df)

    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch = df.iloc[start:end]

        documents = [create_text_description(row) for _, row in batch.iterrows()]
        ids = [str(row["ProductId"]) for _, row in batch.iterrows()]
        metadatas = [
            {
                "ProductId": str(row["ProductId"]),
                "ProductTitle": row["ProductTitle"],
                "Gender": row["Gender"],
                "Category": row["Category"],
                "SubCategory": row["SubCategory"],
                "ProductType": row["ProductType"],
                "Colour": row["Colour"],
                "Usage": row["Usage"],
                "Price": int(row["Price"]),
                "ImageURL": row["ImageURL"],
            }
            for _, row in batch.iterrows()
        ]

        collection.add(documents=documents, ids=ids, metadatas=metadatas)
        print(f"    Progress: {end}/{total} products embedded...")

    print(f"\n[OK] Setup complete!")
    print(f"    - SQLite DB:  {DB_PATH}")
    print(f"    - ChromaDB:   {CHROMA_PATH}")
    print(f"    - Products:   {total}")
    print(f"\n>>> Now run:  python app.py")


if __name__ == "__main__":
    setup()
