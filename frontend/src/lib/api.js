const API_BASE = '/api';

async function fetchJSON(url) {
  const res = await fetch(`${API_BASE}${url}`);
  if (!res.ok) {
    if (res.status === 404) return null;
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}

export async function search(query) {
  return fetchJSON(`/search?q=${encodeURIComponent(query)}`);
}

export async function getCategories(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return fetchJSON(`/categories${qs ? `?${qs}` : ''}`);
}

export async function getCategory(slug) {
  return fetchJSON(`/categories/${slug}`);
}

export async function getSealTypes() {
  return fetchJSON(`/seal-types`);
}

export async function getArticles() {
  return fetchJSON(`/articles`);
}

export async function getArticle(slug) {
  return fetchJSON(`/articles/${slug}`);
}

export async function submitReport(data) {
  const res = await fetch(`${API_BASE}/reports`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Error: ${res.status}`);
  }
  return res.json();
}
