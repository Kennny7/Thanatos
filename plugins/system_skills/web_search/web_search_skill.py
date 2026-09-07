# Thanatos/plugins/system_skills/web_search/web_search_skill.py

import html
import logging
import re
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
import httpx

from plugins.base.skill_interface import BaseSkill
from shared.models.tool_definition import ToolDefinition
from shared.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


class WebSearchSkill(BaseSkill):
    """
    Skill for real-time web intelligence, live internet queries,
    and trending news aggregation using Google News RSS and multi-engine fallbacks.
    """

    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        }

    @property
    def skill_name(self) -> str:
        return "web_search"

    def get_tool_definitions(self) -> List[ToolDefinition]:
        return [
            ToolDefinition(
                name="search_web",
                description="Search the live internet for recent information, documentation, websites, or current events.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query (e.g. 'trending tech news', 'python release notes')",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results to return (default 5)",
                        },
                    },
                    "required": ["query"],
                },
            ),
            ToolDefinition(
                name="search_news",
                description="Search specifically for today's breaking news, trending headlines, and world events.",
                parameters={
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "News topic or category (e.g. 'technology', 'world', 'business', 'trending')",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of news articles (default 5)",
                        },
                    },
                    "required": ["topic"],
                },
            ),
        ]

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        if tool_name == "search_web":
            query = params.get("query", "").strip()
            limit = int(params.get("limit", 5))
            return await self._search_news_and_web(query, limit=limit, is_news=False)

        if tool_name == "search_news":
            topic = params.get("topic", "trending").strip()
            limit = int(params.get("limit", 5))
            return await self._search_news_and_web(topic, limit=limit, is_news=True)

        return ToolResult.error_result(tool_name=tool_name, error=f"Unknown tool '{tool_name}' in WebSearchSkill")

    async def _search_news_and_web(self, query: str, limit: int = 5, is_news: bool = True) -> ToolResult:
        if not query:
            query = "trending news"

        items = await self._fetch_google_news_rss(query, limit=limit)
        
        # Fallback to Wikipedia summary if it was a general term and no news returned
        if not items and not is_news:
            wiki_item = await self._fetch_wikipedia_summary(query)
            if wiki_item:
                items.append(wiki_item)

        if not items:
            return ToolResult.success_result(
                tool_name="search_news" if is_news else "search_web",
                content=f"No live results could be retrieved for query '{query}'. Please verify internet connection.",
            )

        header = "### Live Trending News & Headlines" if is_news else "### Live Web Search Results"
        md_lines = [f"{header} for `{query}`:\n"]
        for idx, it in enumerate(items[:limit], 1):
            title = it.get("title", "Untitled")
            link = it.get("link", "")
            pub = it.get("pub_date", "")
            source = it.get("source", "")
            meta_str = f" *({source} • {pub})*" if source or pub else ""
            if link:
                md_lines.append(f"{idx}. **[{title}]({link})**{meta_str}")
            else:
                md_lines.append(f"{idx}. **{title}**{meta_str}")
            if it.get("description"):
                clean_desc = re.sub(r"<[^>]+>", "", it["description"]).strip()
                if clean_desc and clean_desc != title:
                    md_lines.append(f"   {clean_desc[:250]}...")
            md_lines.append("")

        return ToolResult.success_result(
            tool_name="search_news" if is_news else "search_web",
            content="\n".join(md_lines),
        )

    async def _fetch_google_news_rss(self, query: str, limit: int = 5) -> List[Dict[str, str]]:
        """Fetch real-time news items from Google News RSS feed without API key."""
        encoded = urllib.parse.quote(query)
        if query.lower() in ("trending", "trending news", "top news", "news", "today"):
            url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
        else:
            url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"

        results: List[Dict[str, str]] = []
        try:
            async with httpx.AsyncClient(headers=self.headers, timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    root = ET.fromstring(resp.content)
                    items = root.findall(".//item")
                    for item in items[:limit]:
                        title_el = item.find("title")
                        link_el = item.find("link")
                        pub_el = item.find("pubDate")
                        source_el = item.find("source")
                        desc_el = item.find("description")

                        title = title_el.text if title_el is not None else ""
                        link = link_el.text if link_el is not None else ""
                        pub = pub_el.text if pub_el is not None else ""
                        source = source_el.text if source_el is not None else ""
                        desc = desc_el.text if desc_el is not None else ""

                        if title:
                            results.append({
                                "title": title,
                                "link": link,
                                "pub_date": pub[:16] if pub else "",
                                "source": source,
                                "description": desc,
                            })
        except Exception as e:
            logger.warning("Google News RSS fetch failed: %s", e)

        return results

    async def _fetch_wikipedia_summary(self, query: str) -> Optional[Dict[str, str]]:
        """Fetch quick encyclopedic definition/summary as fallback."""
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
            async with httpx.AsyncClient(headers=self.headers, timeout=5.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    title = data.get("title", query)
                    extract = data.get("extract", "")
                    content_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
                    if extract:
                        return {
                            "title": title,
                            "link": content_url,
                            "pub_date": "",
                            "source": "Wikipedia",
                            "description": extract,
                        }
        except Exception as e:
            logger.debug("Wikipedia summary failed: %s", e)
        return None
