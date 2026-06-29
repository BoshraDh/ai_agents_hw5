"""DuckDuckGo internet search tool — registered as Anthropic tool_use."""

from __future__ import annotations

from debate.models.messages import Citation


SEARCH_TOOL_DEFINITION = {
    "name": "search_web",
    "description": (
        "Search the internet for recent information on a topic. "
        "Returns a list of results with titles, URLs, and snippets. "
        "Use this to find citations for your argument."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "The search query. Be specific — include the debate topic "
                    "and the specific claim you want to support or refute."
                ),
            },
            "max_results": {
                "type": "integer",
                "description": "Number of results to return. Default: 3. Max: 5.",
                "default": 3,
            },
        },
        "required": ["query"],
    },
}


class SearchTool:
    """Wraps DuckDuckGo search and converts results to Citation objects."""

    def search(self, query: str, max_results: int = 3) -> list[Citation]:
        """Search DuckDuckGo and return up to max_results Citation objects."""
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=min(max_results, 5)))
            return [
                Citation(
                    url=r.get("href", ""),
                    snippet=r.get("body", "")[:300],
                    source=r.get("title", ""),
                )
                for r in results
                if r.get("href")
            ]
        except Exception:
            return []

    def handle_tool_call(self, tool_input: dict) -> list[Citation]:
        """Handle an Anthropic tool_use call for search_web."""
        query = tool_input.get("query", "")
        max_results = int(tool_input.get("max_results", 3))
        return self.search(query, max_results)
