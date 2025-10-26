#!/usr/bin/env python3
"""
Embedding Filter Service
========================

FastAPI service that provides Stage 3 embedding-based filtering.
Runs on Hetzner, called by GitHub Actions during daily digest generation.

Endpoints:
  POST /filter - Filter articles using embedding-based clustering
  GET /health - Health check
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any

# Import shared filter logic
from filter_logic import (
    simple_filter,
    embedding_based_blacklist_filter,
    benchmark_filters,
    BLACKLIST_KEYWORDS
)

app = FastAPI(title="News Embedding Filter Service", version="1.0.0")

# Load model on startup (cached) - for future embedding-based filtering
MODEL = None


def load_model():
    """Load embedding model on first request (lazy loading)"""
    global MODEL
    if MODEL is None:
        print("🔄 Loading embedding model...")
        try:
            from FlagEmbedding import BGEM3FlagModel
            MODEL = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
            print("✅ Model loaded: BAAI/bge-m3")
        except Exception as e:
            print(f"⚠️  Error loading model: {e}")
            MODEL = None
    return MODEL


class Article(BaseModel):
    """Article structure matching aggregated data format"""
    title: str
    content: str
    link: str
    source: str
    published: str
    content_length: int
    category: str


class FilterRequest(BaseModel):
    """Request to filter articles"""
    articles: List[Article]
    mode: str = "keyword"  # "keyword", "embedding", or "benchmark"
    threshold: float = 0.6  # Only for embedding mode


class FilterResponse(BaseModel):
    """Response with filtered articles"""
    filtered_articles: List[Article]
    stats: Dict[str, Any]


# Removed - now using shared filter_logic module


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model_loaded": MODEL is not None,
        "blacklist_keywords": len(BLACKLIST_KEYWORDS)
    }


@app.post("/filter", response_model=FilterResponse)
async def filter_articles(request: FilterRequest):
    """
    Filter articles using keyword or embedding-based blacklist.

    Modes:
    - "keyword": Fast keyword matching (default)
    - "embedding": Semantic similarity-based filtering
    - "benchmark": Run both and return comparison (uses embedding results)
    """
    if not request.articles:
        raise HTTPException(status_code=400, detail="No articles provided")

    # Convert Pydantic models to dicts
    articles_dict = [article.dict() for article in request.articles]

    # Route to appropriate filter based on mode
    if request.mode == "keyword":
        filtered_articles, stats = simple_filter(articles_dict)

    elif request.mode == "embedding":
        # Load model if needed
        model = load_model()
        if model is None:
            raise HTTPException(
                status_code=500,
                detail="Embedding model failed to load"
            )
        filtered_articles, stats = embedding_based_blacklist_filter(
            articles_dict,
            model,
            threshold=request.threshold
        )

    elif request.mode == "benchmark":
        # Load model if needed
        model = load_model()
        if model is None:
            raise HTTPException(
                status_code=500,
                detail="Embedding model failed to load"
            )
        # Run benchmark (logs comparison, returns embedding results)
        benchmark_results = benchmark_filters(articles_dict, model)
        filtered_articles, stats = embedding_based_blacklist_filter(
            articles_dict,
            model,
            threshold=request.threshold
        )
        # Add benchmark info to stats
        stats['benchmark'] = benchmark_results

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: {request.mode}. Use 'keyword', 'embedding', or 'benchmark'"
        )

    # Convert back to Pydantic models
    filtered_pydantic = [Article(**article) for article in filtered_articles]

    return FilterResponse(
        filtered_articles=filtered_pydantic,
        stats=stats
    )


@app.get("/")
async def root():
    """Root endpoint with service info"""
    return {
        "service": "News Embedding Filter",
        "version": "2.0.0",
        "endpoints": {
            "/health": "Health check",
            "/filter": "Filter articles (POST)",
        },
        "model": "BAAI/bge-m3 (lazy loaded)",
        "filter_modes": {
            "keyword": "Fast keyword matching (default)",
            "embedding": "Semantic similarity-based filtering",
            "benchmark": "Compare both approaches"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3007)
