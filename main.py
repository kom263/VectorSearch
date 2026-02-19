import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import QdrantClient

from app.models import (
    SearchRequest,
    SearchResponse,
    SearchResult,
    HealthResponse,
    Property,
)
from app.ingestion import ingest_properties, load_properties
from app.query_parser import parse_query
from app.search import PropertySearchEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

qdrant_client: QdrantClient | None = None
search_engine: PropertySearchEngine | None = None
properties_cache: list[Property] = []
index_ready: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    global qdrant_client, search_engine, properties_cache, index_ready

    logger.info("=" * 60)
    logger.info("  Starting Property Search API")
    logger.info("=" * 60)

    logger.info("Initializing Qdrant client (in-memory mode)...")
    qdrant_client = QdrantClient(":memory:")

    properties_cache = load_properties()
    count = ingest_properties(qdrant_client, properties_cache)
    logger.info(f"Indexed {count} properties into Qdrant")

    search_engine = PropertySearchEngine(qdrant_client)
    index_ready = True

    logger.info("=" * 60)
    logger.info("  API is ready! Visit http://localhost:8000/docs")
    logger.info("=" * 60)

    yield

    logger.info("Shutting down Property Search API...")
    if qdrant_client:
        qdrant_client.close()


app = FastAPI(
    title="🏠 Intelligent Property Search API",
    description=(
        "Search properties using natural language queries. "
        "Powered by Sentence-Transformers and Qdrant vector database."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse, tags=["System"])
async def health_check():
    return HealthResponse(
        status="healthy" if index_ready else "initializing",
        total_properties=len(properties_cache),
        index_ready=index_ready,
    )


@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search_properties(request: SearchRequest):
    if not index_ready or search_engine is None:
        raise HTTPException(status_code=503, detail="Search index is not ready yet")

    logger.info(f"Search query: '{request.query}'")

    try:
        parsed_query = parse_query(request.query)
        results = search_engine.search(parsed_query, top_k=request.top_k)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

    return SearchResponse(
        query=request.query,
        parsed_query=parsed_query,
        total_results=len(results),
        results=results,
    )


@app.get("/properties", response_model=list[Property], tags=["Properties"])
async def list_properties():
    return properties_cache


@app.get("/properties/{property_id}", response_model=Property, tags=["Properties"])
async def get_property(property_id: str):
    for prop in properties_cache:
        if prop.id == property_id:
            return prop
    raise HTTPException(status_code=404, detail=f"Property '{property_id}' not found")


@app.post("/reindex", tags=["System"])
async def reindex():
    global properties_cache, index_ready

    if qdrant_client is None:
        raise HTTPException(status_code=503, detail="Qdrant client not initialized")

    index_ready = False
    try:
        properties_cache = load_properties()
        count = ingest_properties(qdrant_client, properties_cache)
        index_ready = True
        return {"status": "success", "properties_indexed": count}
    except Exception as e:
        logger.error(f"Reindex failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
