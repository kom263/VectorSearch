# Intelligent Natural-Language Property Search API

An AI-powered property search system that understands free-text queries like *"I recently shifted to Pine Street and am looking for a property, and a nearby school is preferable"* and returns semantically relevant results using vector embeddings and hybrid search.

Built with **FastAPI**, **Qdrant** (vector database), and **Sentence-Transformers** (`all-MiniLM-L6-v2`).

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Requirements:** Python 3.10+

### 2. Start the Server

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

> First run downloads the `all-MiniLM-L6-v2` model (~80MB). Subsequent starts use the cached model.

### 3. Try It Out

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check:** [http://localhost:8000/](http://localhost:8000/)

### Docker (Alternative)

```bash
# Build the image (pre-downloads the ML model)
docker build -t property-search-api .

# Run the container
docker run -p 8000:8000 property-search-api
```

The API will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## Architecture

```
User Query (free text)
    |
    v
+----------------------+
|  NLP Query Parser    | --> Extracts: budget, bedrooms, location, amenities, preferences
+----------+-----------+
           |
           v
+----------------------+
| Sentence-Transformer | --> Embeds query into 384-dim vector
+----------+-----------+
           |
           v
+----------------------+
| Qdrant Vector Search | --> Retrieves top-50 candidates by cosine similarity
+----------+-----------+
           |
           v
+----------------------+
| Strict Filters       | --> Removes results violating budget / bedroom constraints
+----------+-----------+
           |
           v
+----------------------+
| Boost Scoring        | --> Location, amenity, proximity (<300m), preference boosts
+----------+-----------+
           |
           v
+----------------------+
| Re-rank & Explain    | --> Sorts by combined score, generates explanations
+----------+-----------+
           |
           v
    JSON Response (id, title, score, explanation, metadata, parsed_query)
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check & system status |
| `POST` | `/search` | **Main search** — accepts natural language queries |
| `GET` | `/properties` | List all properties in the database |
| `GET` | `/properties/{id}` | Get a single property by ID |
| `POST` | `/reindex` | Re-ingest data and rebuild vector index |

---

## Example Queries & Output

### Query 1: Location + School Preference

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "I recently shifted to Pine Street and am looking for a property, and a nearby school is preferable.", "top_k": 3}'
```

**Response:**

```json
{
  "query": "I recently shifted to Pine Street and am looking for a property, and a nearby school is preferable.",
  "parsed_query": {
    "original_query": "I recently shifted to Pine Street and am looking for a property, and a nearby school is preferable.",
    "locations": ["pine street"],
    "preferences": ["near school", "nearby school"],
    "amenities": [],
    "bedrooms": null,
    "budget_max": null
  },
  "total_results": 3,
  "results": [
    {
      "property_id": "prop_001",
      "title": "3BHK Apartment on Pine Street",
      "relevance_score": 0.9513,
      "vector_score": 0.6513,
      "explanation": "base similarity=0.65; Location match: pine street; nearby school: Pine Valley School (120m)",
      "metadata": {
        "price": 75000, "bedrooms": 3, "neighborhood": "Pine Street",
        "amenities": ["parking", "balcony"],
        "nearby_places": ["school: Pine Valley School (120m)", "park: Central Park (300m)"]
      }
    },
    {
      "property_id": "prop_002",
      "title": "2BHK near Pine Street Market",
      "relevance_score": 0.8944,
      "vector_score": 0.5944,
      "explanation": "base similarity=0.59; Location match: pine street; nearby school: St. Mark's School (220m)",
      "metadata": {
        "price": 45000, "bedrooms": 2, "neighborhood": "Pine Street Area",
        "amenities": ["parking"],
        "nearby_places": ["school: St. Mark's School (220m)", "shop: Daily Grocery (80m)"]
      }
    }
  ]
}
```

### Query 2: Budget + Bedrooms + Amenity

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "2 bedroom flat under 40k with parking", "top_k": 3}'
```

**Parsed as:** `bedrooms=2, budget_max=40000, property_type=apartment, amenities=[parking]`

### Query 3: Pure Semantic (No Structure)

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Looking for a calm neighbourhood with good schools"}'
```

**Parsed as:** `preferences=["calm", "good schools"]` — relies on semantic similarity + preference boosting.

### Query 4: Amenity + Preference

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Pet-friendly house with balcony"}'
```

**Parsed as:** `property_type=villa, amenities=[pet friendly, balcony]`

### Query 5: Cheap + Transit

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Cheap studio close to metro"}'
```

**Parsed as:** `bedrooms=1, preferences=[close to metro]`

---

## Response Format

```json
{
  "query": "original user query",
  "parsed_query": {
    "original_query": "...",
    "budget_min": null,
    "budget_max": 40000.0,
    "bedrooms": 2,
    "bathrooms": null,
    "property_type": "apartment",
    "locations": ["pine street"],
    "amenities": ["parking"],
    "preferences": ["near school"]
  },
  "total_results": 10,
  "results": [
    {
      "property_id": "prop_001",
      "title": "3BHK Apartment on Pine Street",
      "relevance_score": 0.9513,
      "vector_score": 0.6513,
      "explanation": "base similarity=0.65; Location match: pine street; nearby school: Pine Valley School (120m); amenities: parking",
      "metadata": {
        "price": 75000,
        "bedrooms": 3,
        "bathrooms": 2,
        "neighborhood": "Pine Street",
        "address": "12 Pine Street",
        "area_sqft": 1250,
        "amenities": ["parking", "balcony"],
        "nearby_places": ["school: Pine Valley School (120m)", "park: Central Park (300m)"]
      }
    }
  ]
}
```

---

## Write-Up

### 1. How the Query Parser Works

The query parser (`app/query_parser.py`) uses a **regex + keyword matching** approach to extract structured signals from free-text:

| Signal | Technique | Examples |
|--------|-----------|----------|
| **Budget** | Regex patterns matching price phrases | `under 40k`, `below 2 lakh`, `max 50000`, `20k-50k` |
| **Bedrooms** | Regex for `N bedroom/BHK/BR` patterns | `2 bedroom`, `3BHK`, `studio` (maps to 1) |
| **Property type** | Keyword dictionary mapping | `flat` -> `apartment`, `villa`, `studio`, `penthouse` |
| **Locations** | Matched against known neighborhoods/cities from dataset | `Pine Street`, `city centre` |
| **Amenities** | Matched against a curated set of 30+ amenity keywords | `parking`, `gym`, `pool`, `balcony`, `pet friendly` |
| **Preferences** | Matched against lifestyle/proximity signals | `near school`, `calm`, `sea view`, `pet friendly` |

**Key design:** At startup, the parser is populated with actual values from the dataset (neighborhoods, amenities, nearby place types). This makes it adaptive — it works with any dataset without code changes.

**Fallback behavior:** If no structured signals are found, the system still returns relevant results using pure semantic vector similarity.

### 2. Ranking / Boosting Strategy

The search pipeline uses a **hybrid retrieval + re-ranking** approach:

**Step 1: Vector Retrieval**
- The query is embedded using `all-MiniLM-L6-v2` (384-dim vectors).
- Qdrant retrieves the top 50 candidates by cosine similarity.

**Step 2: Strict Filtering**
- Candidates violating hard constraints are removed:
  - Price exceeds `budget_max` or is below `budget_min` → removed
  - Bedroom count doesn't match requested → removed

**Step 3: Boosting**
Remaining candidates receive additive score boosts:

| Boost | Weight | Condition |
|-------|--------|-----------|
| Location | +0.15 | Neighborhood/city/address matches query location |
| Amenity | +0.05 each | Property has requested amenity |
| Proximity | +0.10 | Nearby place of requested type within 300m |
| Proximity (far) | +0.025 | Nearby place of requested type beyond 300m |
| Preference | +0.05 | Query preference matches nearby places or description |
| Property type | +0.10 | Property type matches requested type |

**Step 4: Re-ranking**
Candidates are sorted by `combined_score = vector_score + total_boost`.

**Step 5: Explanation**
Each result includes a human-readable explanation showing the base similarity score and all boost reasons with details (e.g., distances).

### 3. Design Choices & Trade-offs

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| **In-memory Qdrant** | Zero setup — no Docker or external service needed | Data reloaded on each restart; not production-scale |
| **Lightweight regex parser** instead of LLM | Fast, deterministic, no API costs, no latency | Cannot handle complex rephrasing (e.g., "I need somewhere my dog can live") |
| **Additive boost scoring** | Simple, interpretable, easy to tune weights | Not as nuanced as learned-to-rank models |
| **Distance-aware proximity boost** | Directly uses `distance_m` from dataset for precise relevance | Requires structured `nearby_places` data in the dataset |
| **all-MiniLM-L6-v2** model | Good balance of quality vs speed; runs on CPU | Larger models (e.g., `all-mpnet-base-v2`) may give better semantic matching |
| **Flat text embedding** of all property fields | Ensures all property aspects are captured in one vector | Very long text may dilute signal; could use multi-vector approach instead |
| **Both structured + flat nearby_places** in payload | Flat text for query matching, structured for distance boosting | Slightly redundant storage |

---

## Project Structure

```
AI Assignment/
├── main.py                 # FastAPI application + endpoints
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker container setup
├── .dockerignore           # Docker build exclusions
├── test_api.py             # Comprehensive test script (38 checks)
├── data/
│   └── properties.json     # 32 sample property listings
└── app/
    ├── __init__.py
    ├── models.py           # Pydantic data models (Property, NearbyPlace, SearchResult)
    ├── embeddings.py       # Sentence-Transformer embedding service
    ├── query_parser.py     # NLP query parser (regex + keyword heuristics)
    ├── search.py           # Hybrid search engine with proximity boosting
    └── ingestion.py        # Data ingestion & Qdrant vector indexing
```

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Web Framework | FastAPI |
| Vector Database | Qdrant (in-memory) |
| Embeddings | Sentence-Transformers (`all-MiniLM-L6-v2`, 384-dim) |
| Data Validation | Pydantic v2 |
| NLP Parsing | Regex + heuristic keyword matching |
| Server | Uvicorn (ASGI) |

---

## Dataset

32 property listings with structured nearby places:

- **Price range:** Rs. 15,000 — Rs. 3,00,000/month
- **Bedrooms:** 1–5 BHK
- **Amenities:** parking, balcony, gym, pool, garden, pet_friendly, public_transit, terrace, garage
- **Nearby places:** schools, parks, shops, gyms, transit hubs, offices — each with name and distance in metres

---

## Query Parser Capabilities

| Feature | Example Input | Extracted |
|---------|---------------|-----------|
| Budget (max) | `"under 40k"`, `"below 50000"`, `"max 30k"` | `budget_max: 40000` |
| Budget (min) | `"above 20k"`, `"starting 1 lakh"` | `budget_min: 20000` |
| Budget (range) | `"20k to 50k"` | `budget_min: 20000, budget_max: 50000` |
| Bedrooms | `"2 bedroom"`, `"3BHK"`, `"studio"` | `bedrooms: 2` |
| Property Type | `"flat"`, `"villa"`, `"penthouse"`, `"house"` | `property_type: apartment` |
| Location | `"Pine Street"`, `"near market"` | `locations: ["pine street"]` |
| Amenities | `"with parking and gym"` | `amenities: ["parking", "gym"]` |
| Preferences | `"near school"`, `"calm"`, `"close to metro"` | `preferences: ["near school", "calm"]` |
