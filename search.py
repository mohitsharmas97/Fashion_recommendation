"""
search.py - AI-powered search logic using ChromaDB + Gemini
"""

import os
import base64
import json
import re
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import google.genai as genai
from dotenv import load_dotenv
from database import get_products_by_ids

load_dotenv()


CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")

_gemini_client = None
_chroma_collection = None


def _get_gemini():
    global _gemini_client
    if _gemini_client is None:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client


def _generate(prompt: str) -> str:
    """Generate text with Gemini."""
    client = _get_gemini()
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
    )
    return response.text.strip()


def _generate_with_image(prompt: str, image_bytes: bytes) -> str:
    """Generate text with Gemini Vision."""
    import base64
    client = _get_gemini()
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=[
            prompt,
            genai.types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
        ],
    )
    return response.text.strip()


def _get_collection():
    global _chroma_collection
    if _chroma_collection is None:
        embedding_fn = SentenceTransformerEmbeddingFunction("all-MiniLM-L6-v2")
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        _chroma_collection = client.get_collection(
            name="fashion_products", embedding_function=embedding_fn
        )
    return _chroma_collection


def parse_query_with_gemini(query: str) -> dict:
    """
    Use Gemini to extract structured fashion filters from natural language.
    Returns a dict with keys: search_text, max_price, gender, color, usage, product_type
    """
    prompt = f"""You are a fashion search assistant. Extract search parameters from this query.
Return ONLY valid JSON (no markdown, no explanation).

Query: "{query}"

Return JSON with these keys (use null if not mentioned):
{{
  "search_text": "refined search phrase for semantic search",
  "max_price": <integer or null>,
  "min_price": <integer or null>,
  "gender": "<Men|Women|Boys|Girls|null>",
  "color": "<color name or null>",
  "usage": "<Casual|Formal|Sports|Ethnic|Party|Smart Casual|null>",
  "product_type": "<type like Shirts|Jeans|Tops|Shoes|etc or null>",
  "category": "<Apparel|Footwear|null>"
}}

Examples:
- "blue formal shirts under 2000" → search_text:"blue formal shirts", max_price:2000, color:"Blue"
- "suggest party wear, no baggy clothes" → search_text:"party wear fitted clothes"
- "casual sneakers for women" → search_text:"casual sneakers women", gender:"Women", usage:"Casual"
"""
    try:
        text = _generate(prompt)
        # Remove markdown code blocks if present
        text = re.sub(r"```json\s*|\s*```", "", text).strip()
        return json.loads(text)
    except Exception as e:
        print(f"Gemini parse error: {e}")
        return {"search_text": query, "max_price": None, "min_price": None,
                "gender": None, "color": None, "usage": None, 
                "product_type": None, "category": None}


def build_chroma_where(filters: dict) -> dict:
    """Build ChromaDB where clause from filters."""
    conditions = []

    if filters.get("gender"):
        conditions.append({"Gender": {"$eq": filters["gender"]}})
    if filters.get("color"):
        conditions.append({"Colour": {"$eq": filters["color"]}})
    if filters.get("usage"):
        conditions.append({"Usage": {"$eq": filters["usage"]}})
    if filters.get("product_type"):
        conditions.append({"ProductType": {"$eq": filters["product_type"]}})
    if filters.get("category"):
        conditions.append({"Category": {"$eq": filters["category"]}})
    if filters.get("max_price"):
        conditions.append({"Price": {"$lte": int(filters["max_price"])}})
    if filters.get("min_price"):
        conditions.append({"Price": {"$gte": int(filters["min_price"])}})

    if len(conditions) == 0:
        return {}
    elif len(conditions) == 1:
        return conditions[0]
    else:
        return {"$and": conditions}


def text_search(query: str, n_results: int = 12) -> dict:
    """
    Full AI text search pipeline:
    1. Parse query with Gemini → extract filters
    2. Run ChromaDB semantic similarity search
    3. Fetch product details from SQLite
    4. Generate fashion advice with Gemini
    """
    # Step 1: Parse query
    filters = parse_query_with_gemini(query)
    search_text = filters.get("search_text") or query

    # Step 2: ChromaDB search
    collection = _get_collection()
    where_clause = build_chroma_where(filters)

    try:
        if where_clause:
            results = collection.query(
                query_texts=[search_text],
                n_results=min(n_results, 50),
                where=where_clause,
            )
        else:
            results = collection.query(
                query_texts=[search_text],
                n_results=min(n_results, 50),
            )
    except Exception as e:
        # If where clause causes issues (no results), fall back to no filter
        print(f"ChromaDB query error: {e}, retrying without filters...")
        results = collection.query(
            query_texts=[search_text],
            n_results=min(n_results, 50),
        )

    # Step 3: Fetch product details
    if not results["ids"] or not results["ids"][0]:
        return {"products": [], "advice": "No products found matching your query.", "filters": filters}

    product_ids = results["ids"][0]
    products = get_products_by_ids(product_ids)

    # Step 4: Generate fashion advice
    advice = generate_fashion_advice(query, products[:4])

    return {
        "products": products,
        "advice": advice,
        "filters": filters,
        "search_text": search_text,
    }


def image_search(image_bytes: bytes, n_results: int = 12) -> dict:
    """
    Image-based search:
    1. Send image to Gemini Vision → extract fashion attributes
    2. Run ChromaDB semantic search
    3. Fetch product details
    """
    # Step 1: Analyze image with Gemini Vision
    analysis_prompt = """Analyze this clothing/fashion image and extract:
Return ONLY valid JSON (no markdown).
{
  "description": "detailed description of the clothing item",
  "product_type": "e.g. Shirts, Jeans, Tops, Sneakers, etc.",
  "color": "primary color",
  "style": "e.g. casual, formal, sporty",
  "gender": "Men, Women, Boys, Girls, or Unisex",
  "search_query": "best search query to find similar items"
}"""

    try:
        text = _generate_with_image(analysis_prompt, image_bytes)
        text = re.sub(r"```json\s*|\s*```", "", text).strip()
        analysis = json.loads(text)
    except Exception as e:
        print(f"Gemini Vision error: {e}")
        analysis = {
            "description": "clothing item",
            "search_query": "fashion clothing",
            "color": None,
            "gender": None,
        }

    # Step 2: ChromaDB search
    search_text = analysis.get("search_query", analysis.get("description", "fashion"))
    collection = _get_collection()

    filters = {
        "gender": analysis.get("gender") if analysis.get("gender") not in ["Unisex", None] else None,
        "color": analysis.get("color"),
        "max_price": None,
        "min_price": None,
        "usage": None,
        "product_type": None,
        "category": None,
    }
    where_clause = build_chroma_where(filters)

    try:
        if where_clause:
            results = collection.query(query_texts=[search_text], n_results=n_results, where=where_clause)
        else:
            results = collection.query(query_texts=[search_text], n_results=n_results)
    except Exception as e:
        results = collection.query(query_texts=[search_text], n_results=n_results)

    product_ids = results["ids"][0] if results["ids"] else []
    products = get_products_by_ids(product_ids)

    # Step 3: Generate advice
    advice = f"🔍 Found similar items to your uploaded image. I detected: **{analysis.get('description', 'a clothing item')}**. Here are the closest matches from our collection:"

    return {
        "products": products,
        "advice": advice,
        "analysis": analysis,
        "search_text": search_text,
    }


def get_outfit_recommendations(product_id: int) -> dict:
    """Get complementary outfit items for a given product."""
    from database import get_product_by_id
    
    product = get_product_by_id(product_id)
    if not product:
        return {"products": [], "advice": "Product not found."}

    # Build a complementary query
    if product["SubCategory"] in ["Topwear", "Topwear"]:
        complement = f"bottoms jeans trousers for {product['Gender']} {product['Usage']} {product['Colour']}"
    elif product["SubCategory"] in ["Bottomwear"]:
        complement = f"tops shirts for {product['Gender']} {product['Usage']}"
    elif product["SubCategory"] in ["Footwear", "Flip Flops", "Shoes"]:
        complement = f"casual {product['Usage']} outfit for {product['Gender']}"
    else:
        complement = f"{product['Usage']} fashion for {product['Gender']}"

    collection = _get_collection()
    # Exclude current product
    results = collection.query(
        query_texts=[complement],
        n_results=6,
        where={"Gender": {"$eq": product["Gender"]}},
    )
    
    # Filter out the current product itself
    product_ids = [pid for pid in (results["ids"][0] if results["ids"] else []) if pid != str(product_id)]
    products = get_products_by_ids(product_ids[:6])

    advice = generate_outfit_advice(product, products)

    return {"products": products, "advice": advice, "base_product": product}


def generate_fashion_advice(query: str, products: list) -> str:
    """Generate fashion advice using Gemini based on query and products."""
    if not products:
        return "I couldn't find products matching your query. Try different keywords!"

    product_list = "\n".join(
        [f"- {p['ProductTitle']} ({p['Colour']}, ₹{p['Price']})" for p in products[:4]]
    )

    prompt = f"""You are a friendly AI fashion stylist. A customer asked: "{query}"

Top matching products found:
{product_list}

Give a SHORT, enthusiastic fashion advice response (2-3 sentences max) explaining why these products match and any styling tips. Be conversational and helpful. Do NOT list the products again."""

    try:
        return _generate(prompt)
    except Exception as e:
        return f"Great picks! Here are {len(products)} items that match '{query}'. These selections are curated based on your preferences."


def generate_outfit_advice(base_product: dict, complement_products: list) -> str:
    """Generate outfit pairing advice."""
    if not complement_products:
        return "Complete your look with these complementary items!"

    prompt = f"""You are a fashion stylist. Someone is looking at:
"{base_product['ProductTitle']}" ({base_product['Colour']}, {base_product['Usage']})

Suggest how to style it with these complementary items (1-2 sentences, be specific and stylish):
{', '.join([p['ProductTitle'] for p in complement_products[:3]])}"""

    try:
        return _generate(prompt)
    except Exception as e:
        return "Complete your look with these perfectly matched items! Mix and match for a stylish outfit."
