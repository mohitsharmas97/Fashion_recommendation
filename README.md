# 🛍️ AI Fashion E-Commerce Platform
### Smart Outfit Recommendations powered by Google Gemini + ChromaDB

---

## 📁 Project Structure

```
fashion/
├── app.py               # Flask web server (main entry point)
├── setup_database.py    # ⚠️ Run ONCE to initialize databases
├── search.py            # AI search logic (Gemini + ChromaDB)
├── database.py          # SQLite helper
├── requirements.txt     # Python dependencies
├── fashion.csv          # ← Copy here from Kaggle dataset
│
├── templates/
│   ├── index.html       # Main page (search + results)
│   ├── product.html     # Product detail + outfit recommendations
│   └── setup_required.html
│
├── static/
│   ├── css/style.css    # Premium dark fashion UI
│   ├── js/main.js       # Frontend JavaScript
│   └── images/          # Placeholder images
│
├── fashion.db           # ← Created by setup_database.py
└── chroma_db/           # ← Created by setup_database.py
```

---

## 🚀 Setup Instructions (Step by Step)

### Step 1 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Copy the Dataset
Copy `fashion.csv` from your Kaggle dataset into this folder:
```
c:\Users\Mohit Sharma\Desktop\fashion\fashion.csv
```
*(Your notebook used it from: `/root/.cache/kagglehub/datasets/vikashrajluhaniwal/fashion-images/versions/1/data/fashion.csv`)*

### Step 3 — Get a Gemini API Key
1. Go to https://aistudio.google.com/app/apikey
2. Create a free API key

### Step 4 — Set the API Key
```bash
set GEMINI_API_KEY=your_api_key_here
```

### Step 5 — Run Database Setup (ONE TIME ONLY)
```bash
python setup_database.py
```
This will:
- Create `fashion.db` with all 2906 products + simulated prices
- Generate vector embeddings using Sentence Transformers
- Store vectors in ChromaDB

⏱️ Takes about 2-5 minutes on first run.

### Step 6 — Start the Web Server
```bash
python app.py
```

### Step 7 — Open in Browser
```
http://localhost:5000
```

---

## 🎯 Features

| Feature | Description |
|---------|-------------|
| 💬 **Text Search** | Natural language: "blue formal shirts under 2000" |
| 📷 **Image Search** | Upload a photo → find similar items |
| 🤖 **AI Fashion Advice** | Gemini explains why products match |
| 👗 **Outfit Recommendations** | AI suggests complementary items |
| 🔍 **Smart Filters** | Auto-extracts price, color, gender from query |
| 📱 **Responsive UI** | Works on mobile and desktop |

---

## 🛠️ Tech Stack

- **Frontend**: HTML, CSS (Dark Glassmorphism), JavaScript
- **Backend**: Flask (Python)
- **AI Search**: Google Gemini 1.5 Flash + Sentence Transformers (`all-MiniLM-L6-v2`)
- **Vector DB**: ChromaDB (semantic similarity search)
- **Database**: SQLite (product catalog)
- **Dataset**: Kaggle Fashion Product Images (2906 products)

---

## 💡 Example Queries

- `show me blue formal shirts under 2000`
- `suggest party wear for women, not too casual`
- `casual sneakers for men under 3000`
- `ethnic wear for girls`
- `sports shoes for boys`
- Upload an image of any clothing item → find similar products!

---

## ⚠️ Troubleshooting

**"Setup Required" page shows?**
→ Run `python setup_database.py` first

**Gemini API error?**
→ Make sure `GEMINI_API_KEY` is set. Get free key at https://aistudio.google.com/app/apikey

**fashion.csv not found?**
→ Copy it from your Kaggle dataset to the fashion/ folder

**ChromaDB error?**
→ Delete the `chroma_db/` folder and re-run `setup_database.py`
