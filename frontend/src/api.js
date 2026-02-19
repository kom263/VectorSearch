const API_BASE = import.meta.env.VITE_API_URL || "/api";

export async function searchProperties(query, topK = 10) {
    const response = await fetch(`${API_BASE}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, top_k: topK }),
    });
    if (!response.ok) throw new Error(`Server error: ${response.status}`);
    return response.json();
}

export async function getHealth() {
    const response = await fetch(`${API_BASE}/`);
    if (!response.ok) throw new Error(`Server error: ${response.status}`);
    return response.json();
}

export async function getProperties() {
    const response = await fetch(`${API_BASE}/properties`);
    if (!response.ok) throw new Error(`Server error: ${response.status}`);
    return response.json();
}
