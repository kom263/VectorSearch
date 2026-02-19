import re
import logging
from typing import List, Set
from app.models import ParsedQuery

logger = logging.getLogger(__name__)

_known_cities: Set[str] = set()
_known_neighborhoods: Set[str] = set()
_known_amenities: Set[str] = set()
_known_nearby_types: Set[str] = set()

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

    logger.info(f"Parsed query: {parsed.model_dump_json(exclude_none=True)}")
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
