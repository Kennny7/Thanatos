# Web Microservice

## Overview
The `web` microservice provides internet search capabilities, DOM parsing, structured content extraction, and automated web interaction.

## Key Modules
- `search.py`: Web querying across search engines and RSS news streams.
- `scraper.py`: Asynchronous web page scraper with rate-limiting and browser session management.
- `parser.py`: HTML sanitization, text extraction, and Markdown conversion.

## Standalone Testing
Ensure dependencies are installed:
```bash
uv sync
```

To test web scraping and parsing functions:
```bash
uv run python -c "from services.web.search import WebSearchEngine; s = WebSearchEngine(); print('Web engine operational')"
```
