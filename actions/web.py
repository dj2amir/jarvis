"""
Web Actions — search and fetch web content.

Tools:
  - web_search: Search the web using DuckDuckGo
  - get_time: Get current date and time
"""

import requests
import json
from datetime import datetime

TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web and return results (max 5)",
        "parameters": {
            "query": "What to search for"
        },
    },
    {
        "name": "get_time",
        "description": "Get current date and time",
        "parameters": {},
    },
]


def execute(name: str, **kwargs):
    if name == "web_search":
        return _web_search(kwargs.get("query", ""))
    elif name == "get_time":
        return _get_time()
    return None


def _web_search(query: str) -> str:
    if not query:
        return "No search query provided."
    try:
        # Use DuckDuckGo Instant Answer API (no key needed)
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}
        resp = requests.get(url, params=params, timeout=8)
        data = resp.json()

        results = []
        # Abstract
        if data.get("AbstractText"):
            results.append(f"📖 {data['AbstractText'][:300]}")
        # Related topics
        for topic in data.get("RelatedTopics", [])[:3]:
            if isinstance(topic, dict) and topic.get("Text"):
                results.append(f"• {topic['Text'][:200]}")

        if not results:
            return f"No results found for '{query}'."
        return "\n".join(results)
    except Exception as e:
        return f"Search failed: {e}"


def _get_time() -> str:
    now = datetime.now()
    return now.strftime("%A, %B %d, %Y at %I:%M %p")
