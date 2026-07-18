"""
Web Search Layer
=================
Implements the web search tool using DuckDuckGo to fetch recent/external
information not present in the graph or document vector DB.
"""
import logging
from typing import Any
try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

def web_search(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """
    Search the web for current information, returning titles, snippets, 
    URLs, and published dates if available.
    """
    if DDGS is None:
        return [{"error": "duckduckgo-search (or ddgs) package is not installed. Please pip install it to enable web search."}]
    
    if not query or not query.strip():
        return []
        
    try:
        results = []
        with DDGS() as ddgs:
            # We use text search and extract available fields. 
            # Using backend='lite' to avoid rate-limits/blocks from DuckDuckGo's main API.
            search_gen = ddgs.text(query, backend='lite', max_results=max_results)
            for r in search_gen:
                results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", ""),
                    "published_date": r.get("date", "Unknown")
                })
        return results
    except Exception as e:
        logging.error(f"Web search failed for query '{query}': {e}")
        return [{"error": f"Search failed: {str(e)}"}]
