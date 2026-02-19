import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import ScoredPoint

from app.models import ParsedQuery, SearchResult
from app.embeddings import encode_text

logger = logging.getLogger(__name__)

COLLECTION_NAME = "properties"
DEFAULT_TOP_K = 10
VECTOR_CANDIDATES = 50

LOCATION_BOOST = 0.15
AMENITY_BOOST = 0.05
PREFERENCE_BOOST = 0.05
PROPERTY_TYPE_BOOST = 0.10
PROXIMITY_BOOST = 0.10
PROXIMITY_THRESHOLD_M = 300


class PropertySearchEngine:

    def __init__(self, qdrant_client: QdrantClient):
        self.client = qdrant_client

    def search(self, parsed_query: ParsedQuery, top_k: int = DEFAULT_TOP_K) -> List[SearchResult]:
        query_vector = encode_text(parsed_query.original_query)

        candidates = self._vector_search(query_vector, limit=VECTOR_CANDIDATES)
        logger.info(f"Vector search returned {len(candidates)} candidates")

        if not candidates:
            return []

        filtered = self._apply_strict_filters(candidates, parsed_query)
        logger.info(f"After strict filters: {len(filtered)} candidates remain")

        scored = self._apply_boosts(filtered, parsed_query)

        scored.sort(key=lambda x: x["combined_score"], reverse=True)

        results = []
        for item in scored[:top_k]:
            result = self._build_result(item, parsed_query)
            results.append(result)

        return results

    def _vector_search(self, query_vector: List[float], limit: int) -> List[Dict[str, Any]]:
        try:
            hits: List[ScoredPoint] = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                limit=limit,
                with_payload=True,
            )
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return []

        candidates = []
        for hit in hits:
            payload = hit.payload or {}
            candidates.append({
                "id": payload.get("id", str(hit.id)),
                "vector_score": hit.score,
                "payload": payload,
            })
        return candidates

    def _apply_strict_filters(
        self, candidates: List[Dict], parsed_query: ParsedQuery
    ) -> List[Dict]:
        filtered = []

        for candidate in candidates:
            payload = candidate["payload"]
            price = payload.get("price", 0)
            bedrooms = payload.get("bedrooms", 0)

            if parsed_query.budget_max is not None and price > parsed_query.budget_max:
                continue
            if parsed_query.budget_min is not None and price < parsed_query.budget_min:
                continue

            if parsed_query.bedrooms is not None and bedrooms != parsed_query.bedrooms:
                continue

            if parsed_query.bathrooms is not None:
                bathrooms = payload.get("bathrooms", 0)
                if bathrooms < parsed_query.bathrooms:
                    continue

            filtered.append(candidate)

        return filtered

    def _apply_boosts(
        self, candidates: List[Dict], parsed_query: ParsedQuery
    ) -> List[Dict]:
        for candidate in candidates:
            payload = candidate["payload"]
            boost = 0.0
            boost_reasons = []

            if parsed_query.locations:
                city = (payload.get("city") or "").lower()
                neighborhood = (payload.get("neighborhood") or "").lower()
                address = (payload.get("address") or "").lower()
                for loc in parsed_query.locations:
                    if (loc in city or loc in neighborhood or loc in address
                            or city in loc or neighborhood in loc):
                        boost += LOCATION_BOOST
                        boost_reasons.append(f"Location match: {loc}")
                        break

            property_amenities = {a.lower() for a in payload.get("amenities", [])}
            matched_amenities = []
            for amenity in parsed_query.amenities:
                amenity_lower = amenity.lower()
                amenity_alt = amenity_lower.replace("_", " ")
                if amenity_lower in property_amenities or amenity_alt in property_amenities:
                    matched_amenities.append(amenity)
                else:
                    for pa in property_amenities:
                        if amenity_lower in pa or pa in amenity_lower:
                            matched_amenities.append(amenity)
                            break
            if matched_amenities:
                boost += AMENITY_BOOST * len(matched_amenities)
                boost_reasons.append(f"amenities: {', '.join(matched_amenities)}")

            nearby_raw = payload.get("nearby_places_raw", [])
            nearby_flat = {p.lower() for p in payload.get("nearby_places", [])}
            property_desc = payload.get("description", "").lower()
            matched_prefs = []
            proximity_details = []

            for pref in parsed_query.preferences:
                pref_lower = pref.lower()

                place_type = _extract_place_type(pref_lower)

                if place_type and nearby_raw:
                    matched_place = _find_nearby_by_type(nearby_raw, place_type)
                    if matched_place:
                        dist = matched_place["distance_m"]
                        name = matched_place["name"]
                        if dist <= PROXIMITY_THRESHOLD_M:
                            boost += PROXIMITY_BOOST
                            proximity_details.append(
                                f"nearby {place_type}: {name} ({int(dist)}m)"
                            )
                        else:
                            boost += PREFERENCE_BOOST * 0.5
                            proximity_details.append(
                                f"{place_type}: {name} ({int(dist)}m, outside {PROXIMITY_THRESHOLD_M}m)"
                            )
                        matched_prefs.append(pref)
                        continue

                if any(pref_lower in place or place in pref_lower for place in nearby_flat):
                    boost += PREFERENCE_BOOST
                    matched_prefs.append(pref)
                elif any(pref_lower in amenity for amenity in property_amenities):
                    boost += PREFERENCE_BOOST
                    matched_prefs.append(pref)
                elif pref_lower in property_desc:
                    boost += PREFERENCE_BOOST * 0.5
                    matched_prefs.append(pref)

            if proximity_details:
                boost_reasons.extend(proximity_details)
            if matched_prefs and not proximity_details:
                boost_reasons.append(f"preferences: {', '.join(matched_prefs)}")

            if parsed_query.property_type:
                prop_type = (payload.get("property_type") or "").lower()
                if prop_type and prop_type == parsed_query.property_type:
                    boost += PROPERTY_TYPE_BOOST
                    boost_reasons.append(f"property type: {parsed_query.property_type}")

            candidate["boost"] = boost
            candidate["boost_reasons"] = boost_reasons
            candidate["combined_score"] = candidate["vector_score"] + boost

        return candidates

    def _build_result(self, item: Dict, parsed_query: ParsedQuery) -> SearchResult:
        payload = item["payload"]
        explanation_parts = []

        vs = item["vector_score"]
        explanation_parts.append(f"base similarity={vs:.2f}")

        if parsed_query.budget_max is not None or parsed_query.budget_min is not None:
            explanation_parts.append(f"price Rs.{payload.get('price', 0):,.0f} within budget")
        if parsed_query.bedrooms is not None:
            explanation_parts.append(f"{payload.get('bedrooms', 0)} bedrooms as requested")

        explanation_parts.extend(item.get("boost_reasons", []))

        explanation = "; ".join(explanation_parts) if explanation_parts else "Matched via semantic similarity"

        metadata = {
            "price": payload.get("price"),
            "bedrooms": payload.get("bedrooms"),
            "bathrooms": payload.get("bathrooms"),
            "neighborhood": payload.get("neighborhood"),
            "address": payload.get("address"),
            "area_sqft": payload.get("area_sqft"),
            "amenities": payload.get("amenities", []),
            "nearby_places": payload.get("nearby_places", []),
        }
        if payload.get("property_type"):
            metadata["property_type"] = payload["property_type"]
        if payload.get("city"):
            metadata["city"] = payload["city"]

        return SearchResult(
            property_id=payload.get("id", ""),
            title=payload.get("title", ""),
            relevance_score=round(min(item["combined_score"], 1.0), 4),
            vector_score=round(item["vector_score"], 4),
            explanation=explanation,
            metadata=metadata,
        )


_PREF_TO_PLACE_TYPE = {
    "school": "school",
    "hospital": "hospital",
    "park": "park",
    "metro": "transit",
    "transit": "transit",
    "shop": "shop",
    "market": "shop",
    "mall": "shop",
    "gym": "gym",
    "office": "office",
    "tech park": "office",
    "it park": "office",
    "beach": "beach",
    "temple": "temple",
    "church": "church",
    "mosque": "mosque",
    "university": "university",
    "college": "university",
}


def _extract_place_type(pref: str) -> Optional[str]:
    for keyword, place_type in _PREF_TO_PLACE_TYPE.items():
        if keyword in pref:
            return place_type
    return None


def _find_nearby_by_type(nearby_raw: List[Dict], place_type: str) -> Optional[Dict]:
    best = None
    for place in nearby_raw:
        ptype = (place.get("type") or "").lower()
        if ptype == place_type or place_type in ptype or ptype in place_type:
            if best is None or place.get("distance_m", 9999) < best.get("distance_m", 9999):
                best = place
    return best
