"""Search API router.
Endpoint: GET /search?q=…

Calls the real multi-platform aggregator and normalises results into a
flat shape that the front-end expects:
  {
    "title": str,
    "source": str,
    "url": str,
    "content": str,          # snippet / message content
    "price": float | None,   # from google_shopping metrics
    "reviewCount": int | None,
    "sentiment": str | None, # positive / neutral / negative
  }
"""
import os
from fastapi import APIRouter, Request, Query, HTTPException
from starlette.responses import JSONResponse
from typing import List, Dict, Any

from data_ingestion_service.search.orchestrator import aggregate_search

router = APIRouter()


def _normalise(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert adapter output (varies per platform) into a flat dict the UI understands."""
    out = []
    for r in raw:
        metrics = r.get("metrics") or {}

        # Price — only google_shopping supplies this reliably
        price = metrics.get("price")
        try:
            price = float(price) if price is not None else None
        except (ValueError, TypeError):
            price = None

        # Review count
        review_count = metrics.get("reviews") or metrics.get("reviewCount")
        try:
            review_count = int(review_count) if review_count not in (None, "") else None
        except (ValueError, TypeError):
            review_count = None

        # Content / snippet
        content = (
            r.get("content")
            or r.get("snippet")
            or r.get("description")
            or ""
        )

        # Sentiment — use the value if present, else None (front-end shows nothing)
        sentiment = r.get("sentiment") or None

        out.append({
            "title":       r.get("title") or content[:80] or "Signal",
            "source":      r.get("source", "unknown"),
            "url":         r.get("url") or "",
            "content":     content,
            "price":       price,
            "reviewCount": review_count,
            "sentiment":   sentiment,
            "metadata":    {},
        })
    return out


@router.get("/search")
async def search_endpoint(request: Request, q: str = Query(..., min_length=1)):
    """Run real API aggregation and return normalised results."""
    try:
        raw = await aggregate_search(q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    normalised = _normalise(raw.get("results", []))
    insights   = raw.get("insights", {})

    # Re-compute average price from normalised results (only items with a price)
    price_vals = [r["price"] for r in normalised if r["price"] is not None]
    insights["average_price"] = (
        round(sum(price_vals) / len(price_vals), 2) if price_vals else None
    )

    return JSONResponse(content={"results": normalised, "insights": insights})


@router.post("/search")
async def search_endpoint_post(request: Request, q: str = Query(..., min_length=1)):
    return await search_endpoint(request, q)
