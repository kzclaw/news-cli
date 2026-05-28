"""
sources/github.py — GitHub Trending Source

支持模块（modules）：
  trending    — 每日热门（默认）
  trending/weekly — 周热门（暂无API支持，记录占位）

参数（fetch beyond module）：
  language    — 过滤编程语言（如 "Python", "JavaScript"），通过 query param 传递

接入方式：gitrends-api.vercel.app（无 key，免费 JSON API）
返回格式：list[{position, name, description, language, stars, forks, url}]

参考：
  daily-trends-workflow.md — curl https://gitrends-api.vercel.app/trending
"""

import requests
from .base import NewsSource, NewsItem, SourceError

_API_BASE = "https://gitrends-api.vercel.app/trending"
_TIMEOUT = (5, 15)


class GitHubTrendingSource(NewsSource):
    name = "github"
    display_name = "GitHub Trending"
    modules = ["trending"]

    def fetch(
        self,
        module: str | None = None,
        limit: int = 10,
        keyword: str | None = None,
        language: str | None = None,
    ) -> list[NewsItem]:
        params = {}
        if language:
            params["lang"] = language.strip()
        try:
            resp = requests.get(_API_BASE, params=params, timeout=_TIMEOUT, verify=True)
            resp.raise_for_status()
            data: list[dict] = resp.json()
        except Exception as e:
            raise SourceError(f"GitHub trending fetch failed: {e}") from e

        items: list[NewsItem] = []
        for entry in data:
            name = entry.get("name") or ""
            if not name:
                continue
            desc = entry.get("description") or ""
            stars_str = entry.get("stars", "0")
            # stars might be "64,799" or 64799
            try:
                stars_int = int(str(stars_str).replace(",", ""))
            except Exception:
                stars_int = 0

            items.append(NewsItem(
                source="GitHub",
                module="trending",
                title=f"{name} — {desc}" if desc else name,
                url=entry.get("url") or f"https://github.com/{name}",
                time=entry.get("today_stars") or None,
                summary=desc or None,
                heat=f"{stars_int:,} stars",
                author=name.split("/")[0] if "/" in name else name,
                extra={
                    "repo": name,
                    "language": entry.get("language") or "",
                    "stars": stars_int,
                    "forks": entry.get("forks", 0),
                }
            ))
        items = self.filter_by_keyword(items, keyword)
        return items[:limit]