import json
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
)

from app.models import Property, NearbyPlace
from app.embeddings import encode_batch, EMBEDDING_DIM
from app.query_parser import register_known_values

logger = logging.getLogger(__name__)

COLLECTION_NAME = "properties"
DATA_DIR = Path(__file__).parent.parent / "data"

_NAMESPACE_UUID = uuid.UUID("12345678-1234-5678-1234-567812345678")


def load_properties(filepath: Path | None = None) -> List[Property]:
    if filepath is None:
        filepath = DATA_DIR / "properties.json"

    logger.info(f"Loading properties from {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    properties = [Property(**item) for item in raw_data]
    logger.info(f"Loaded {len(properties)} properties")
    return properties


def flatten_nearby_places(nearby_places: List[NearbyPlace] | None) -> List[str]:
    if not nearby_places:
        return []
    result = []
    for place in nearby_places:
        dist = int(place.distance_m)
        result.append(f"{place.type}: {place.name} ({dist}m)")
    return result


def nearby_places_to_dicts(nearby_places: List[NearbyPlace] | None) -> List[Dict[str, Any]]:
    if not nearby_places:
        return []
    return [
        {"type": p.type, "name": p.name, "distance_m": p.distance_m}
        for p in nearby_places
    ]


def preprocess_property_text(prop: Property) -> str:
    parts = [
        prop.title,
        prop.description,
    ]

    location_parts = []
    if prop.address:
        location_parts.append(prop.address)
    location_parts.append(prop.neighborhood)
    if prop.city:
        location_parts.append(prop.city)
    parts.append(f"Located in {', '.join(location_parts)}")

    parts.append(f"{prop.bedrooms} bedrooms, {prop.bathrooms} bathrooms")
    if prop.property_type:
        parts.append(f"{prop.property_type} property")
    parts.append(f"Price: {prop.price}")
    parts.append(f"Area: {prop.area_sqft} sqft")

    if prop.amenities:
        parts.append(f"Amenities: {', '.join(prop.amenities)}")

    if prop.nearby_places:
        nearby_texts = []
        for place in prop.nearby_places:
            nearby_texts.append(f"{place.name} ({place.type}, {int(place.distance_m)}m away)")
        parts.append(f"Nearby: {', '.join(nearby_texts)}")

    return " . ".join(parts)


def create_collection(client: QdrantClient):
    collections = [c.name for c in client.get_collections().collections]

    if COLLECTION_NAME in collections:
        logger.info(f"Deleting existing collection: {COLLECTION_NAME}")
        client.delete_collection(COLLECTION_NAME)

    logger.info(f"Creating collection: {COLLECTION_NAME} (dim={EMBEDDING_DIM})")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=EMBEDDING_DIM,
            distance=Distance.COSINE,
        ),
    )


def ingest_properties(client: QdrantClient, properties: List[Property] | None = None) -> int:
    if properties is None:
        properties = load_properties()

    cities = list(set(p.city for p in properties if p.city))
    neighborhoods = list(set(p.neighborhood for p in properties))
    all_amenities = list(set(
        amenity for p in properties if p.amenities for amenity in p.amenities
    ))
    nearby_types = list(set(
        place.type for p in properties if p.nearby_places for place in p.nearby_places
    ))
    register_known_values(cities, neighborhoods, all_amenities, nearby_types)

    logger.info("Preprocessing property text for embedding...")
    texts = [preprocess_property_text(p) for p in properties]

    logger.info("Generating embeddings...")
    embeddings = encode_batch(texts)
    if not embeddings:
        raise ValueError("No embeddings generated — dataset may be empty.")
    logger.info(f"Generated {len(embeddings)} embeddings (dim={len(embeddings[0])})")

    actual_dim = len(embeddings[0])
    if actual_dim != EMBEDDING_DIM:
        raise ValueError(
            f"Embedding dimension mismatch: model outputs {actual_dim}, "
            f"but EMBEDDING_DIM is set to {EMBEDDING_DIM}"
        )

    create_collection(client)

    points = []
    for i, (prop, embedding) in enumerate(zip(properties, embeddings)):
        nearby_flat = flatten_nearby_places(prop.nearby_places)
        nearby_structured = nearby_places_to_dicts(prop.nearby_places)

        payload: Dict[str, Any] = {
            "id": prop.id,
            "title": prop.title,
            "description": prop.description,
            "price": prop.price,
            "bedrooms": prop.bedrooms,
            "bathrooms": prop.bathrooms,
            "property_type": prop.property_type or "",
            "city": prop.city or "",
            "neighborhood": prop.neighborhood,
            "address": prop.address or "",
            "area_sqft": prop.area_sqft,
            "amenities": prop.amenities or [],
            "nearby_places": nearby_flat,
            "nearby_places_raw": nearby_structured,
            "latitude": prop.latitude,
            "longitude": prop.longitude,
        }
        point_id = str(uuid.uuid5(_NAMESPACE_UUID, prop.id))
        points.append(
            PointStruct(id=point_id, vector=embedding, payload=payload)
        )

    logger.info(f"Upserting {len(points)} points into Qdrant...")
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    logger.info("Ingestion complete!")

    return len(points)
