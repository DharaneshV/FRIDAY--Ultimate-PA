"""
Web tools — search, fetch pages, and global news briefings.
"""

import httpx
import xml.etree.ElementTree as ET
import asyncio
import re
import time
import json
import urllib.parse
from datetime import datetime
from bs4 import BeautifulSoup
from friday.config import config

# Simple Cache for Search Results
_SEARCH_CACHE = {}
_CACHE_TTL = 300 # 5 minutes

SEED_FEEDS = [
    'https://feeds.bbci.co.uk/news/world/rss.xml',
    'https://www.cnbc.com/id/100727362/device/rss/rss.html',
    'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
    'https://www.aljazeera.com/xml/rss/all.xml'
]

async def fetch_and_parse_feed(client, url):
    try:
        response = await client.get(url, headers={'User-Agent': 'Friday-AI/1.0'}, timeout=5.0)
        if response.status_code != 200:
            return []
        root = ET.fromstring(response.content)
        source_name = url.split('.')[1].upper()
        feed_items = []
        items = root.findall(".//item")[:5]
        for item in items:
            title = item.findtext("title")
            description = item.findtext("description")
            link = item.findtext("link")
            if description:
                description = re.sub('<[^<]+?>', '', description).strip()
            feed_items.append({
                "source": source_name,
                "title": title,
                "summary": description[:200] + "..." if description else "",
                "link": link
            })
        return feed_items
    except Exception:
        return []

def duckduckgo_scrape(query, max_results):
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        res = httpx.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        results = []
        for d in soup.select("a.result__snippet")[:max_results]:
            results.append({"title": d.get_text()[:50]+'...', "content": d.get_text(), "url": d.get("href")})
        return json.dumps(results)
    except Exception as e:
        return json.dumps([{"error": f"Scrape extraction failed: {str(e)}"}])

def register(mcp):

    @mcp.tool()
    async def get_world_news(category: str = "world", count: int = 12) -> str:
        """
        Fetches the latest global headlines from major news outlets simultaneously.
        """
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            tasks = [fetch_and_parse_feed(client, url) for url in SEED_FEEDS]
            results_of_lists = await asyncio.gather(*tasks)
            all_articles = [item for sublist in results_of_lists for item in sublist]

        if not all_articles:
            return "The global news grid is unresponsive, sir. I'm unable to pull headlines."

        report = ["### GLOBAL NEWS BRIEFING (LIVE)\n"]
        for entry in all_articles[:count]:
            report.append(f"**[{entry['source']}]** {entry['title']}")
            report.append(f"{entry['summary']}")
            report.append(f"Link: {entry['link']}\n")

        return "\n".join(report)

    @mcp.tool()
    async def search_web(query: str, max_results: int = 5) -> str:
        """Search the web for a given query and return a summary of results. Uses cache."""
        cache_key = f"{query}_{max_results}"
        if cache_key in _SEARCH_CACHE:
            entry = _SEARCH_CACHE[cache_key]
            if time.time() - entry['time'] < _CACHE_TTL:
                return "[CACHED] " + entry['data']

        results_str = ""

        # Tavily
        if config.TAVILY_API_KEY:
            try:
                from tavily import TavilyClient
                tavily = TavilyClient(api_key=config.TAVILY_API_KEY)
                res = tavily.search(query=query, search_depth="basic", max_results=max_results)
                results_str = json.dumps(res.get("results", []))
            except Exception:
                pass 

        # Serper
        if not results_str and config.SERPER_API_KEY:
            try:
                headers = {'X-API-KEY': config.SERPER_API_KEY, 'Content-Type': 'application/json'}
                res = httpx.post("https://google.serper.dev/search", headers=headers, json={"q": query, "num": max_results})
                if res.status_code == 200:
                    data = res.json()
                    results_str = json.dumps(data.get("organic", []))
            except Exception:
                pass 

        # DuckDuckGo fallback
        if not results_str:
            results_str = duckduckgo_scrape(query, max_results)

        if not results_str:
            results_str = "Search failed across all providers."

        _SEARCH_CACHE[cache_key] = {"time": time.time(), "data": results_str}
        return results_str

    @mcp.tool()
    def clear_search_cache() -> str:
        """Clears the search results cache."""
        _SEARCH_CACHE.clear()
        return "Search cache cleared, boss."

    @mcp.tool()
    async def fetch_url(url: str) -> str:
        """Fetch the raw text content of a URL smoothly extracted (strips scripts/nav/style)."""
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    script.extract()
                
                text = soup.get_text(separator=' ', strip=True)
                text = re.sub(r'\s+', ' ', text).strip()
                return text[:4000] 
            except Exception as e:
                return f"Failed to fetch content from {url}: {e}"
    
    @mcp.tool()
    async def open_world_monitor(topic: str = "") -> str:
        """
        Opens the World Monitor dashboard (worldmonitor.app) in the system's web browser.
        Can deep-link or search a topic if provided.
        """
        import webbrowser
        url = "https://worldmonitor.app/"
        if topic:
            url += f"?search={urllib.parse.quote(topic)}"
        
        try:
            webbrowser.open(url)
            return "Displaying the World Monitor on your primary screen now, sir."
        except Exception as e:
            return f"I'm unable to initialize the visual monitor: {str(e)}"