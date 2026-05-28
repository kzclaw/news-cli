"""
sources/rss.py — 通用 RSS/Atom Source

支持模块（modules）：
  <preset_key>  — 内置预设源（如 "bensbites", "paulgraham", "lexfridman"）
  custom        — 自定义 RSS URL（通过 url 参数指定）

内置预设 RSS 源（可扩展）：
  AI Newsletters:  bensbites, latentspace_ainews, chinai, memia, interconnects
  Podcasts:       lexfridman, latentspace, 80000hours
  Essays:         paulgraham, waitbutwhy, jamesclear, farnamstreet, dan_koe

接入方式：requests + 内置 html.parser（无第三方依赖，无 Playwright）
"""

import warnings
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import requests
from .base import NewsSource, NewsItem, SourceError

_TIMEOUT = (10, 20)
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NewsCLI/1.0)",
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
}

# Suppress XMLParsedAsHTMLWarning (Ben's Bites sends Atom as text/html)
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

PRESET_SOURCES: dict[str, dict] = {
    # AI Newsletters
    "bensbites": {"name": "Ben's Bites", "url": "https://www.bensbites.com/feed"},
    "latentspace_ainews": {"name": "Latent Space AINews", "url": "https://www.latent.space/feed"},
    "chinai": {"name": "ChinAI", "url": "https://chinai.substack.com/feed"},
    "memia": {"name": "Memia", "url": "https://memia.substack.com/feed"},
    "interconnects": {"name": "Interconnects", "url": "https://www.interconnects.ai/feed"},
    # Podcasts
    "lexfridman": {"name": "Lex Fridman Podcast", "url": "https://lexfridman.com/feed/podcast"},
    "80000hours": {"name": "800,000 Hours", "url": "https://feeds.transistor.fm/80-000-hours-podcast"},
    "latentspace": {"name": "Latent Space", "url": "https://latent.space/feed"},
    # Essays
    "paulgraham": {"name": "Paul Graham Essays", "url": "http://www.aaronsw.com/2002/feeds/pgessays.rss"},
    "waitbutwhy": {"name": "Wait But Why", "url": "https://waitbutwhy.com/feed"},
    "jamesclear": {"name": "James Clear", "url": "https://jamesclear.com/feed"},
    "farnamstreet": {"name": "Farnam Street", "url": "https://fs.blog/feed"},
    "dan_koe": {"name": "Dan Koe", "url": "https://dankoe.com/feed"},
}


class RSSSource(NewsSource):
    name = "rss"
    display_name = "RSS"
    modules = list(PRESET_SOURCES.keys()) + ["custom"]

    def __init__(self, feed_url: str | None = None, source_key: str | None = None):
        self.feed_url = feed_url
        self.source_key = source_key
        self._display_name = "RSS"
        self._module = "custom"

        if source_key and source_key in PRESET_SOURCES:
            self.feed_url = PRESET_SOURCES[source_key]["url"]
            self._display_name = PRESET_SOURCES[source_key]["name"]
            self._module = source_key

    def fetch(
        self,
        module: str | None = None,
        limit: int = 10,
        keyword: str | None = None,
        url: str | None = None,
    ) -> list[NewsItem]:
        target_url = url or self.feed_url
        mod = self._module  # default from __init__

        # CLI can pass preset name as module to override
        if module and module in PRESET_SOURCES:
            target_url = PRESET_SOURCES[module]["url"]
            self._display_name = PRESET_SOURCES[module]["name"]
            mod = module
        elif module:
            mod = module

        if not target_url:
            raise SourceError(
                "No RSS URL provided. Use --source rss:<preset> or --source rss --url <url>"
            )

        try:
            resp = requests.get(target_url, timeout=_TIMEOUT, verify=True, headers=_HEADERS)
            resp.raise_for_status()
        except Exception as e:
            raise SourceError(f"RSS fetch failed for {target_url}: {e}") from e

        return self._parse(resp.text, mod, limit, keyword)

    def _parse(
        self, content: str, module: str, limit: int, keyword: str | None
    ) -> list[NewsItem]:
        soup = BeautifulSoup(content, "html.parser")
        items: list[NewsItem] = []

        # Try Atom (entry) then RSS (item)
        entries = soup.find_all(["entry", "item"])
        if not entries:
            entries = []

        for entry in entries:
            title_tag = entry.find("title")
            title = (title_tag.get_text(strip=True) if title_tag else "") or ""
            if "<![CDATA[" in title:
                # Extract content from <![CDATA[...]]> wrapper
                start = title.find("<![CDATA[")
                end = title.find("]]>")
                if start != -1 and end != -1:
                    title = title[start + 9:end]
            if not title:
                continue

            # Link resolution
            link_tag = entry.find("link")
            if link_tag:
                href = link_tag.get("href") or link_tag.get_text(strip=True)
            else:
                guid = entry.find("guid")
                href = (guid.get_text(strip=True) if guid else "") or ""

            # Time
            time_tag = entry.find(["published", "pubDate", "updated", "dc:date"])
            time_str = (time_tag.get_text(strip=True) if time_tag else "") or None

            # Summary
            desc_tag = entry.find(["summary", "description", "content"])
            summary = (desc_tag.get_text(strip=True) if desc_tag else "")[:500] or None

            # Author
            author_tag = entry.find(["author", "dc:creator"])
            author = (author_tag.get_text(strip=True) if author_tag else "") or None

            items.append(NewsItem(
                source=self._display_name,
                module=module,
                title=title,
                url=href,
                time=time_str,
                summary=summary,
                heat=None,
                author=author,
                extra={}
            ))
            if len(items) >= limit * 2:
                break

        items = self.filter_by_keyword(items, keyword)
        return items[:limit]