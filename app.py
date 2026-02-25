"""
app.py - Main Flask application for AI Fashion E-Commerce Platform
"""

import os
import sys
from dotenv import load_dotenv

# Auto-load .env file (contains GEMINI_API_KEY)
load_dotenv()

# Force UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
)
from database import get_product_by_id, get_featured_products, get_categories
from search import text_search, image_search, get_outfit_recommendations

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fashion-ai-secret-2024")

# ── Check setup ──────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "fashion.db")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")


def is_setup_complete():
    return os.path.exists(DB_PATH) and os.path.exists(CHROMA_PATH)


# ── Routes ───────────────────────────────────────────────────

@app.route("/")
def index():
    if not is_setup_complete():
        return render_template("setup_required.html")

    featured = get_featured_products(12)
    categories = get_categories()
    return render_template("index.html", featured=featured, categories=categories)


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = get_product_by_id(product_id)
    if not product:
        return redirect(url_for("index"))

    outfit_data = get_outfit_recommendations(product_id)
    return render_template(
        "product.html",
        product=product,
        outfit_products=outfit_data.get("products", []),
        outfit_advice=outfit_data.get("advice", ""),
    )


# ── API Endpoints ────────────────────────────────────────────

@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.get_json()
    query = data.get("query", "").strip()

    if not query:
        return jsonify({"error": "Query is required"}), 400

    # Add to conversation history
    if "conversation" not in session:
        session["conversation"] = []

    session["conversation"].append({"role": "user", "text": query})

    result = text_search(query, n_results=12)

    session["conversation"].append({
        "role": "assistant",
        "text": result.get("advice", ""),
    })
    session.modified = True

    return jsonify({
        "products": result["products"],
        "advice": result.get("advice", ""),
        "filters": result.get("filters", {}),
        "count": len(result["products"]),
    })


@app.route("/api/image-search", methods=["POST"])
def api_image_search():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]
    if not file.filename:
        return jsonify({"error": "No image selected"}), 400

    image_bytes = file.read()
    result = image_search(image_bytes, n_results=12)

    return jsonify({
        "products": result["products"],
        "advice": result.get("advice", ""),
        "analysis": result.get("analysis", {}),
        "count": len(result["products"]),
    })


@app.route("/api/recommend/<int:product_id>")
def api_recommend(product_id):
    result = get_outfit_recommendations(product_id)
    return jsonify({
        "products": result.get("products", []),
        "advice": result.get("advice", ""),
    })


@app.route("/api/featured")
def api_featured():
    products = get_featured_products(12)
    return jsonify({"products": products})


@app.route("/api/conversation/clear", methods=["POST"])
def clear_conversation():
    session.pop("conversation", None)
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    if not is_setup_complete():
        print("\n[!] Database not set up yet!")
        print("    Please run:  python setup_database.py\n")
    else:
        print("\n[*] Fashion AI Platform starting...")
        print("    Open: http://localhost:5000\n")
    app.run(debug=True, port=5000)
