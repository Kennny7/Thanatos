# Thanatos\services\web\scraper.py

"""
Async web scraper using Playwright.
- Fetch and summarise a URL (first 4000 chars of cleaned text).
- Search DuckDuckGo HTML (no API key) and return top 5 results.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SearchResult:
    title: str
    snippet: str


# ---------------------------------------------------------------------------
# Readability‑like JavaScript helpers (injected into the page)
# ---------------------------------------------------------------------------

_CLEAN_TEXT_SCRIPT = """
() => {
    // Remove non‑content elements
    const selectors = [
        'script', 'style', 'noscript', 'iframe', 'svg',
        'nav', 'footer', 'header', 'aside',
        '[role="navigation"]', '[role="banner"]', '[role="contentinfo"]'
    ];
    for (const sel of selectors) {
        document.querySelectorAll(sel).forEach(el => el.remove());
    }

    // Try to focus on <article> or <main> if they exist
    const main = document.querySelector('article, main, [role="main"]');
    const root = main || document.body;

    // Get innerText and collapse whitespace
    let text = root.innerText || '';
    text = text.replace(/\\n{3,}/g, '\\n\\n');   // collapse multiple blank lines
    text = text.replace(/[ \\t]{2,}/g, ' ');      // collapse spaces/tabs
    return text.trim();
}
"""

# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class WebScraper:
    """
    Async web scraper that:
      - fetches a URL and returns a cleaned text summary,
      - performs DuckDuckGo searches without an API key.
    """

    DEFAULT_TIMEOUT = 30_000          # milliseconds
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    DDG_HTML_URL = "https://html.duckduckgo.com/html/"

    # ------------------------------------------------------------------
    def __init__(
        self,
        headless: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Args:
            headless: Run browser without a visible window.
            timeout:  Default navigation / action timeout in ms.
            user_agent: Override the default User‑Agent string.
        """
        self.headless = headless
        self.timeout = timeout
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self._playwright = None
        self._browser = None

    # ------------------------------------------------------------------
    async def _ensure_browser(self) -> None:
        """Launch Playwright and the browser if not already running."""
        if self._browser is not None:
            return

        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox"],   # needed in many Docker environments
            )
        except Exception as exc:
            raise RuntimeError(
                "Failed to launch browser. Is 'playwright install chromium' done?"
            ) from exc

    # ------------------------------------------------------------------
    async def _teardown_browser(self) -> None:
        """Gracefully close the browser and stop Playwright."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    # ------------------------------------------------------------------
    async def _new_page(self):
        """Create a new page with configured timeout and user agent."""
        context = await self._browser.new_context(
            user_agent=self.user_agent,
            viewport={"width": 1280, "height": 720},
        )
        page = await context.new_page()
        page.set_default_timeout(self.timeout)
        return context, page

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def fetch_and_summarize(self, url: str) -> str:
        """
        Fetch the given URL, extract readable text, and return the first
        4000 characters.

        Args:
            url: Fully qualified URL (e.g. https://example.com).

        Returns:
            Cleaned, truncated text (max 4000 chars).

        Raises:
            ValueError: If the URL is invalid.
            RuntimeError: On browser launch failure.
            TimeoutError: If the page takes too long to load.
        """
        if not url.startswith(("http://", "https://")):
            raise ValueError("Invalid URL – must start with http:// or https://")

        await self._ensure_browser()
        context, page = await self._new_page()

        try:
            logger.info("Navigating to %s", url)
            response = await page.goto(url, wait_until="domcontentloaded")
            if not response or not response.ok:
                raise RuntimeError(
                    f"Failed to load page (status {response.status if response else 'unknown'})"
                )

            # Wait for the network to become mostly idle
            try:
                await page.wait_for_load_state("networkidle")
            except PlaywrightTimeoutError:
                logger.warning("Network did not reach idle state within timeout – proceeding anyway")

            # Extract and clean text
            text = await page.evaluate(_CLEAN_TEXT_SCRIPT)
            truncated = text[:4000]
            logger.info("Extracted %d characters, returning %d", len(text), len(truncated))
            return truncated

        except PlaywrightTimeoutError as exc:
            raise TimeoutError(f"Navigation timed out for {url}") from exc
        finally:
            await context.close()

    # ------------------------------------------------------------------
    async def search_web(self, query: str) -> list[SearchResult]:
        """
        Perform a DuckDuckGo search and return the top 5 results.

        Args:
            query: The search string.

        Returns:
            A list of up to 5 SearchResult objects (title + snippet).

        Raises:
            RuntimeError: On browser launch failure.
            TimeoutError: If the search page times out.
        """
        await self._ensure_browser()
        context, page = await self._new_page()

        search_url = f"{self.DDG_HTML_URL}?q={query}"
        results: list[SearchResult] = []

        try:
            logger.info("Searching DuckDuckGo for: %s", query)
            await page.goto(search_url, wait_until="domcontentloaded")

            # Wait for at least one result to appear
            try:
                await page.wait_for_selector(".result__title", timeout=self.timeout)
            except PlaywrightTimeoutError:
                logger.warning("No search results found within timeout")
                return results

            # Extract all result blocks
            result_elements = await page.query_selector_all(".result")
            for el in result_elements[:5]:
                title_el = await el.query_selector(".result__title")
                snippet_el = await el.query_selector(".result__snippet")
                if title_el:
                    title = (await title_el.inner_text()).strip()
                    snippet = ""
                    if snippet_el:
                        snippet = (await snippet_el.inner_text()).strip()
                    results.append(SearchResult(title=title, snippet=snippet))

            return results

        except PlaywrightTimeoutError as exc:
            raise TimeoutError(f"DuckDuckGo search timed out for '{query}'") from exc
        finally:
            await context.close()

    # ------------------------------------------------------------------
    # Context manager support (optional convenience)
    # ------------------------------------------------------------------
    async def __aenter__(self):
        await self._ensure_browser()
        return self

    async def __aexit__(self, *args):
        await self._teardown_browser()