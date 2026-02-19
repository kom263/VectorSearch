from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class NearbyPlace(BaseModel):
    type: str
    name: str
    distance_m: float


class Property(BaseModel):
    id: str
    title: str
    description: str
    address: Optional[str] = None
    neighborhood: str
    latitude: float
    longitude: float
    price: float
    bedrooms: int
    bathrooms: int
    area_sqft: int
    amenities: List[str] = []
    nearby_places: List[NearbyPlace] = []
    property_type: Optional[str] = None
    city: Optional[str] = None


class ParsedQuery(BaseModel):
    original_query: str
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    property_type: Optional[str] = None
    locations: List[str] = []
    amenities: List[str] = []
    preferences: List[str] = []
    unmatched_tokens: List[str] = []


class SearchResult(BaseModel):
    property_id: str
    title: str
    relevance_score: float = Field(..., description="Combined similarity + boost score (0-1)")
    vector_score: float = Field(..., description="Raw cosine similarity from Qdrant")
    explanation: str = Field(..., description="Human-readable explanation of why this result ranked here")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    parsed_query: ParsedQuery
    total_results: int
    results: List[SearchResult]


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language search query")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of results to return")


class HealthResponse(BaseModel):
    status: str
    total_properties: int
    index_ready: bool
