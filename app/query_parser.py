import os
import json
import re
import logging
from typing import List, Set, Optional
from app.models import ParsedQuery

logger = logging.getLogger(__name__)

_known_cities: Set[str] = set()
_known_neighborhoods: Set[str] = set()
_known_amenities: Set[str] = set()
_known_nearby_types: Set[str] = set()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
_gemini_model = None

if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini_model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction="""You are a real-estate search query parser. Given a user's natural-language property search query, extract structured filters as JSON.

RESPONSE FORMAT — return ONLY valid JSON, no markdown fences, no explanation:
{
  "budget_min": <number or null>,
  "budget_max": <number or null>,
  "bedrooms": <int or null>,
  "bathrooms": <int or null>,
  "property_type": <string or null>,
  "locations": [<strings>],
  "amenities": [<strings>],
  "preferences": [<strings>]
}

EXTRACTION RULES:

1. BUDGET: Interpret Indian currency shorthands: k=thousand, L/lac/lakh=100000, Cr/crore=10000000. Only extract as budget when the number refers to PRICE/COST. "40k sq ft" is an AREA, not a budget. "under 40k" with no area unit IS a budget.

2. NEGATION: If a location, amenity, or preference is NEGATED ("not on Pine Street", "no gym", "away from highway"), do NOT include it in the positive lists. Simply omit it entirely.

3. SEMANTIC MAPPING for amenities — map natural phrases to canonical amenity names:
   - "where my dog can live", "pet ok", "pets allowed" → "pet_friendly"
   - "place to work out", "exercise" → "gym"
   - "can park my car" → "parking"
   - "place to swim" → "swimming pool"
   - "connected to internet", "has wifi" → "wifi"
   - "air conditioned", "has AC" → "ac"
   - "fully furnished" → "furnished"
   - "has a garden", "green space" → "garden"
   - "safe", "gated" → "security"

4. PROPERTY TYPES: apartment, villa, studio, penthouse, loft, cottage, farmhouse, co-living, duplex. Map synonyms: flat→apartment, house/bungalow→villa.

5. PREFERENCES: Lifestyle/proximity phrases like "near school", "quiet area", "sea view", "family friendly", "near metro", "eco-friendly". Include them as-is in the preferences list.

6. LOCATIONS: City names and neighborhood names the user wants to live IN. Only include locations the user is POSITIVELY requesting (not negated).

7. CONTRADICTIONS: If budget_min > budget_max, set BOTH to null. If other filters contradict, prefer the most recent/specific one.

8. If a field has no value, use null for scalars and [] for lists.

KNOWN VALUES (from the dataset):
{context}

Return ONLY the JSON object.""",
        )
        logger.info("Gemini LLM query parser initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Gemini: {e}. Falling back to regex parser.")
        _gemini_model = None
else:
    logger.info("GEMINI_API_KEY not set — using regex fallback parser")


DEFAULT_AMENITIES = {
    "parking", "gym", "swimming pool", "pool", "garden", "security",
    "lift", "elevator", "power backup", "furnished", "ac",
    "air conditioning", "wi-fi", "wifi", "internet", "clubhouse",
    "concierge", "terrace", "balcony", "fireplace", "smart home",
    "home office", "co-working", "coworking", "laundry", "housekeeping",
    "pet friendly", "pet_friendly", "barbecue", "jogging track",
    "children play area", "play area", "indoor games", "tennis court",
    "meditation center", "solar panels", "rainwater harvesting",
    "garage", "public_transit", "public transit",
}

PREFERENCE_KEYWORDS = {
    "near school", "close to school", "good schools", "nearby school",
    "near hospital", "close to hospital",
    "near metro", "close to metro", "metro connectivity", "metro access",
    "near park", "close to park",
    "near beach", "close to beach", "beachside", "beach access",
    "near mall", "close to mall", "shopping",
    "near market", "close to market",
    "near temple", "near church", "near mosque",
    "near university", "near college",
    "near IT park", "close to IT park", "IT hub",
    "near transit", "close to transit", "transit hub",
    "near office", "close to office", "near tech park",
    "near shop", "close to shop", "nearby shop",
    "calm", "quiet", "peaceful", "serene", "tranquil",
    "vibrant", "lively", "bustling",
    "green", "eco-friendly", "nature", "scenic",
    "mountain view", "lake view", "sea view", "river view", "waterfront",
    "city centre", "city center", "central", "downtown",
    "family friendly", "kid friendly", "child friendly",
    "student friendly", "bachelor friendly",
    "pet friendly", "pet-friendly",
}

PROPERTY_TYPE_KEYWORDS = {
    "apartment": "apartment",
    "flat": "apartment",
    "villa": "villa",
    "house": "villa",
    "bungalow": "villa",
    "studio": "studio",
    "penthouse": "penthouse",
    "loft": "loft",
    "cottage": "cottage",
    "farmhouse": "farmhouse",
    "co-living": "co-living",
    "coliving": "co-living",
    "duplex": "duplex",
    "home": "apartment",
}


def register_known_values(
    cities: List[str],
    neighborhoods: List[str],
    amenities: List[str],
    nearby_types: List[str] | None = None,
):
    global _known_cities, _known_neighborhoods, _known_amenities, _known_nearby_types
    _known_cities = {c.lower() for c in cities}
    _known_neighborhoods = {n.lower() for n in neighborhoods}
    _known_amenities = DEFAULT_AMENITIES | {a.lower() for a in amenities}
    if nearby_types:
        _known_nearby_types = {t.lower() for t in nearby_types}
    logger.info(
        f"Registered {len(_known_cities)} cities, "
        f"{len(_known_neighborhoods)} neighborhoods, "
        f"{len(_known_amenities)} amenities, "
        f"{len(_known_nearby_types)} nearby place types"
    )


def parse_query(query: str) -> ParsedQuery:
    if _gemini_model:
        try:
            return _parse_with_gemini(query)
        except Exception as e:
            logger.warning(f"Gemini parsing failed: {e}. Falling back to regex.")
    return _parse_with_regex(query)


def _build_context() -> str:
    parts = []
    if _known_cities:
        parts.append(f"Cities: {', '.join(sorted(_known_cities))}")
    if _known_neighborhoods:
        parts.append(f"Neighborhoods: {', '.join(sorted(_known_neighborhoods))}")
    if _known_amenities:
        parts.append(f"Amenities: {', '.join(sorted(_known_amenities))}")
    if _known_nearby_types:
        parts.append(f"Nearby place types: {', '.join(sorted(_known_nearby_types))}")
    return "\n".join(parts) if parts else "No dataset context available."


def _parse_with_gemini(query: str) -> ParsedQuery:
    context = _build_context()
    prompt = _gemini_model.model._system_instruction
    if hasattr(prompt, 'parts'):
        pass

    user_prompt = f"Parse this property search query:\n\"{query}\"\n\nKnown values context:\n{context}"

    response = _gemini_model.generate_content(user_prompt)
    raw = response.text.strip()

    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

    data = json.loads(raw)

    budget_min = data.get("budget_min")
    budget_max = data.get("budget_max")
    if budget_min is not None and budget_max is not None and budget_min > budget_max:
        budget_min = None
        budget_max = None

    parsed = ParsedQuery(
        original_query=query,
        budget_min=budget_min,
        budget_max=budget_max,
        bedrooms=data.get("bedrooms"),
        bathrooms=data.get("bathrooms"),
        property_type=data.get("property_type"),
        locations=data.get("locations", []),
        amenities=data.get("amenities", []),
        preferences=data.get("preferences", []),
    )

    logger.info(f"[Gemini] Parsed query: {parsed.model_dump_json(exclude_none=True)}")
    return parsed


def _parse_with_regex(query: str) -> ParsedQuery:
    original = query
    q = query.lower().strip()

    budget_min = _extract_budget_min(q)
    budget_max = _extract_budget_max(q)
    bedrooms = _extract_bedrooms(q)
    bathrooms = _extract_bathrooms(q)
    property_type = _extract_property_type(q)
    locations = _extract_locations(q)
    amenities = _extract_amenities(q)
    preferences = _extract_preferences(q)

    parsed = ParsedQuery(
        original_query=original,
        budget_min=budget_min,
        budget_max=budget_max,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        property_type=property_type,
        locations=locations,
        amenities=amenities,
        preferences=preferences,
    )

    logger.info(f"[Regex] Parsed query: {parsed.model_dump_json(exclude_none=True)}")
    return parsed


def _normalize_amount(value_str: str, suffix: str = "") -> float:
    value_str = value_str.replace(",", "").strip()
    num = float(value_str)

    suffix = suffix.lower().strip()
    if suffix in ("k", "thousand"):
        return num * 1_000
    elif suffix in ("l", "lac", "lakh", "lakhs"):
        return num * 100_000
    elif suffix in ("cr", "crore", "crores"):
        return num * 10_000_000
    elif suffix in ("m", "million"):
        return num * 1_000_000
    return num


def _extract_budget_max(q: str) -> float | None:
    patterns = [
        r'(?:under|below|max|maximum|upto|up\s*to|within|budget|less\s*than|at\s*most)\s*(?:rs\.?|₹|inr)?\s*(\d+(?:\.\d+)?)\s*(k|thousand|l|lac|lakh|lakhs|cr|crore|crores|m|million)?',
        r'(?:rs\.?|₹|inr)?\s*(\d+(?:\.\d+)?)\s*(k|thousand|l|lac|lakh|lakhs|cr|crore|crores|m|million)?\s*(?:max|maximum|budget|or\s*less|or\s*below)',
        r'(?:rs\.?|₹|inr)?\s*\d+(?:\.\d+)?\s*(?:k|thousand|l|lac|lakh|lakhs|cr|crore|crores|m|million)?\s*(?:-|to)\s*(?:rs\.?|₹|inr)?\s*(\d+(?:\.\d+)?)\s*(k|thousand|l|lac|lakh|lakhs|cr|crore|crores|m|million)?',
    ]
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            try:
                return _normalize_amount(match.group(1), match.group(2) or "")
            except (ValueError, IndexError):
                continue
    return None


def _extract_budget_min(q: str) -> float | None:
    patterns = [
        r'(?:above|over|min|minimum|at\s*least|more\s*than|starting|from)\s*(?:rs\.?|₹|inr)?\s*(\d+(?:\.\d+)?)\s*(k|thousand|l|lac|lakh|lakhs|cr|crore|crores|m|million)?',
        r'(?:rs\.?|₹|inr)?\s*(\d+(?:\.\d+)?)\s*(k|thousand|l|lac|lakh|lakhs|cr|crore|crores|m|million)?\s*(?:-|to)\s*(?:rs\.?|₹|inr)?\s*\d+',
    ]
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            try:
                return _normalize_amount(match.group(1), match.group(2) or "")
            except (ValueError, IndexError):
                continue
    return None


def _extract_bedrooms(q: str) -> int | None:
    patterns = [
        r'(\d+)\s*(?:bed(?:room)?s?|bhk|br)\b',
        r'(\d+)\s*(?:rk|room)',
    ]
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            return int(match.group(1))
    if "studio" in q:
        return 1
    return None


def _extract_bathrooms(q: str) -> int | None:
    patterns = [
        r'(\d+)\s*(?:bath(?:room)?s?|ba)\b',
    ]
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            return int(match.group(1))
    return None


def _extract_property_type(q: str) -> str | None:
    for keyword, ptype in PROPERTY_TYPE_KEYWORDS.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', q):
            return ptype
    return None


def _extract_locations(q: str) -> List[str]:
    found = []
    for neighborhood in sorted(_known_neighborhoods, key=len, reverse=True):
        if neighborhood in q:
            found.append(neighborhood)
    for city in sorted(_known_cities, key=len, reverse=True):
        if re.search(r'\b' + re.escape(city) + r'\b', q):
            if city not in found:
                found.append(city)
    return found


def _extract_amenities(q: str) -> List[str]:
    found = []
    for amenity in sorted(_known_amenities, key=len, reverse=True):
        if amenity in q:
            found.append(amenity)
    return found


def _extract_preferences(q: str) -> List[str]:
    found = []
    for pref in PREFERENCE_KEYWORDS:
        if pref in q:
            found.append(pref)
    return found
