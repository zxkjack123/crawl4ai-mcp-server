"""Simple FastAPI bridge exposing crawl4ai MCP tools as HTTP endpoints."""

from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import importlib

try:  # pragma: no cover - attempt absolute import when package context is available
    index = importlib.import_module("src.index")
except ModuleNotFoundError:  # pragma: no cover - fallback for direct execution
    index = importlib.import_module("index")

app = FastAPI(title="Crawl4AI HTTP Bridge", version="0.6.0")


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query string")
    num_results: int = Field(10, ge=1, le=50)
    engine: str = Field(
        "auto",
        description="Engine to use (auto, brave, google, duckduckgo, searxng, all)",
    )


class ReadRequest(BaseModel):
    url: str = Field(..., description="URL to crawl")
    format: str = Field("markdown_with_citations", description="Desired output format")


@app.on_event("startup")
async def _startup() -> None:
    # Warm-up search manager to reduce first-request latency.
    await index.initialize_search_manager()


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Return overall health/readiness information."""
    status_json = await index.system_status(check_type="all")
    return json.loads(status_json)


@app.post("/search")
async def search_endpoint(payload: SearchRequest) -> Dict[str, Any]:
    """Perform a search via the existing MCP search tool."""
    results_json = await index.search(
        payload.query, payload.num_results, payload.engine
    )
    data = json.loads(results_json)
    if isinstance(data, dict) and data.get("error"):
        raise HTTPException(status_code=400, detail=data["error"])
    return {"results": data, "count": len(data)}


@app.post("/read_url")
async def read_url_endpoint(payload: ReadRequest) -> Dict[str, Any]:
    """Crawl a URL and return markdown or other requested format."""
    content = await index.read_url(payload.url, payload.format)
    try:
        maybe_error = json.loads(content)
        if isinstance(maybe_error, dict) and "error" in maybe_error:
            raise HTTPException(status_code=400, detail=maybe_error["error"])
    except json.JSONDecodeError:
        maybe_error = None
    return {
        "url": payload.url,
        "format": payload.format,
        "content": content,
        "error": maybe_error.get("error") if maybe_error else None,
    }


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("src.rest_server:app", host="0.0.0.0", port=8000, reload=False)
