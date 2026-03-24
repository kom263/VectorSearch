"""FastAPI application entry point.

Production features:
- Structured logging with timestamps
- Rate limiting middleware for API protection
- CORS for React frontend
- Auto-created SQLite tables
"""

import time
import logging
from collections import defaultdict
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.database import engine, Base
from app.routers import candidates, pipeline, dashboard

# ── Logging Configuration ────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Create all tables
Base.metadata.create_all(bind=engine)
logger.info("Database tables created/verified")


# ── Rate Limiting Middleware ─────────────────────────────────────

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiter.
    Limits requests per IP to prevent abuse, especially on LLM-calling endpoints.
    """
    def __init__(self, app, max_requests: int = 30, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)  # IP -> [timestamps]

    async def dispatch(self, request: Request, call_next):
        # Only rate-limit write endpoints (POST)
        if request.method == "POST":
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()

            # Clean old entries
            self.requests[client_ip] = [
                t for t in self.requests[client_ip]
                if now - t < self.window_seconds
            ]

            if len(self.requests[client_ip]) >= self.max_requests:
                logger.warning("Rate limit exceeded for IP: %s", client_ip)
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds}s."
                )

            self.requests[client_ip].append(now)

        return await call_next(request)


# ── Request Logging Middleware ───────────────────────────────────

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests with timing."""
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = (time.time() - start) * 1000  # ms

        logger.info(
            "%s %s → %d (%.1fms)",
            request.method, request.url.path, response.status_code, duration
        )
        return response


# ── FastAPI App ──────────────────────────────────────────────────

app = FastAPI(
    title="AI Hiring Pipeline",
    description="AI-powered backend for automated candidate screening, "
                "pipeline management, and recruiter dashboard.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware (order matters: first added = outermost)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=30, window_seconds=60)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(candidates.router)
app.include_router(pipeline.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "name": "AI Hiring Pipeline",
        "version": "1.0.0",
        "docs": "/docs"
    }
