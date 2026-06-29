"""Tests for SearchTool."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from debate.models.messages import Citation
from debate.tools.search_tool import SearchTool


class TestSearchTool:
    def test_returns_citations(self):
        tool = SearchTool()
        mock_results = [
            {"href": "https://example.com/1", "body": "AI helps doctors.", "title": "MedNews"},
            {"href": "https://example.com/2", "body": "AI improves crops.", "title": "AgriNews"},
        ]
        with patch("debate.tools.search_tool.DDGS") as MockDDGS:
            instance = MockDDGS.return_value.__enter__.return_value
            instance.text.return_value = mock_results
            results = tool.search("AI benefits", max_results=2)

        assert len(results) == 2
        assert isinstance(results[0], Citation)
        assert results[0].url == "https://example.com/1"

    def test_returns_empty_on_failure(self):
        tool = SearchTool()
        with patch("debate.tools.search_tool.DDGS", side_effect=Exception("network error")):
            results = tool.search("test query")
        assert results == []

    def test_handle_tool_call(self):
        tool = SearchTool()
        with patch.object(tool, "search", return_value=[
            Citation(url="https://x.com", snippet="snippet", source="X")
        ]) as mock_search:
            results = tool.handle_tool_call({"query": "test", "max_results": 2})
        mock_search.assert_called_once_with("test", 2)
        assert len(results) == 1
