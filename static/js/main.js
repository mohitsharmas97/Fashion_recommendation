/* ===================================================
   main.js – FashionAI Frontend Logic
   =================================================== */

let selectedImageFile = null;

// ── Tab switching ───────────────────────────────────
function switchTab(tab) {
    document.getElementById('panel-text').classList.toggle('hidden', tab !== 'text');
    document.getElementById('panel-image').classList.toggle('hidden', tab !== 'image');
    document.getElementById('tab-text').classList.toggle('active', tab === 'text');
    document.getElementById('tab-image').classList.toggle('active', tab === 'image');
}

// ── Set query from chip ─────────────────────────────
function setQuery(text) {
    document.getElementById('text-query').value = text;
    switchTab('text');
    document.getElementById('search-section').scrollIntoView({ behavior: 'smooth' });
    setTimeout(() => doTextSearch(), 300);
}

// ── Text search ─────────────────────────────────────
async function doTextSearch() {
    const query = document.getElementById('text-query').value.trim();
    if (!query) return;

    showLoading(true);
    showResultsSection();

    try {
        const res = await fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query }),
        });
        const data = await res.json();
        renderResults(data);
    } catch (err) {
        showError('Search failed. Please try again.');
    } finally {
        showLoading(false);
    }
}

// ── Image drop / select ─────────────────────────────
function handleDrop(event) {
    event.preventDefault();
    document.getElementById('drop-zone').classList.remove('drag-over');
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        setImageFile(file);
    }
}

function handleImageSelect(event) {
    const file = event.target.files[0];
    if (file) setImageFile(file);
}

function setImageFile(file) {
    selectedImageFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        const preview = document.getElementById('preview-img');
        const inner = document.getElementById('drop-zone-inner');
        preview.src = e.target.result;
        preview.classList.remove('hidden');
        inner.classList.add('hidden');
    };
    reader.readAsDataURL(file);
    document.getElementById('image-search-btn').disabled = false;
}

// ── Image search ────────────────────────────────────
async function doImageSearch() {
    if (!selectedImageFile) return;

    showLoading(true);
    showResultsSection();

    const formData = new FormData();
    formData.append('image', selectedImageFile);

    try {
        const res = await fetch('/api/image-search', { method: 'POST', body: formData });
        const data = await res.json();
        renderResults(data);
    } catch (err) {
        showError('Image search failed. Please try again.');
    } finally {
        showLoading(false);
    }
}

// ── Render results ──────────────────────────────────
function renderResults(data) {
    // AI advice
    const adviceEl = document.getElementById('ai-advice-text');
    if (data.advice) {
        adviceEl.innerHTML = formatAdvice(data.advice);
        document.getElementById('ai-advice').style.display = 'flex';
    } else {
        document.getElementById('ai-advice').style.display = 'none';
    }

    // Count
    const count = data.products ? data.products.length : 0;
    document.getElementById('results-count').textContent =
        count > 0 ? `${count} products found` : 'No products found';

    // Product grid
    const grid = document.getElementById('product-grid');
    grid.innerHTML = '';

    if (!data.products || data.products.length === 0) {
        grid.innerHTML = `
      <div style="grid-column:1/-1;text-align:center;padding:40px;color:#555568">
        <div style="font-size:2rem;margin-bottom:12px">🔍</div>
        <p>No products found. Try different keywords!</p>
      </div>`;
        return;
    }

    data.products.forEach((product, idx) => {
        const card = createProductCard(product, idx);
        grid.appendChild(card);
    });
}

// ── Product card DOM ────────────────────────────────
function createProductCard(p, delay = 0) {
    const card = document.createElement('div');
    card.className = 'product-card';
    card.style.animationDelay = `${delay * 0.05}s`;
    card.onclick = () => (window.location = `/product/${p.ProductId}`);

    const price = p.Price ? `₹${p.Price.toLocaleString('en-IN')}` : '₹999';
    const rating = p.Rating || '4.2';
    const imgUrl = p.ImageURL || '';

    card.innerHTML = `
    <div class="product-image-wrap">
      <img
        src="${escHtml(imgUrl)}"
        alt="${escHtml(p.ProductTitle)}"
        class="product-img"
        loading="lazy"
        onerror="this.src='/static/images/placeholder.svg'"
      />
      <div class="product-badge">${escHtml(p.Usage || '')}</div>
      <div class="product-overlay">
        <button class="overlay-btn" onclick="event.stopPropagation();window.location='/product/${p.ProductId}'">View Details</button>
      </div>
    </div>
    <div class="product-info">
      <p class="product-type">${escHtml(p.ProductType || '')} · ${escHtml(p.Colour || '')}</p>
      <h3 class="product-title">${escHtml(truncate(p.ProductTitle, 52))}</h3>
      <div class="product-footer">
        <span class="product-price">${price}</span>
        <span class="product-rating">⭐ ${rating}</span>
      </div>
    </div>`;
    return card;
}

// ── UI helpers ──────────────────────────────────────
function showLoading(show) {
    const spinner = document.getElementById('spinner');
    if (spinner) spinner.classList.toggle('hidden', !show);
}

function showResultsSection() {
    const sec = document.getElementById('results-section');
    sec.style.display = 'block';
    sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function showError(msg) {
    document.getElementById('ai-advice-text').textContent = msg;
    document.getElementById('ai-advice').style.display = 'flex';
    document.getElementById('product-grid').innerHTML = '';
    document.getElementById('results-count').textContent = '';
}

function formatAdvice(text) {
    // Bold **text**
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
}

function truncate(str, n) {
    if (!str) return '';
    return str.length > n ? str.slice(0, n) + '…' : str;
}

function escHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

// ── Enter key support ───────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('text-query');
    if (input) {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') doTextSearch();
        });
    }
});
