"""
sources/devto.py — DEV.to Source

支持模块（modules）：
  trending    — 综合热门（默认）
  latest      — 最新

参数：
  tag         — 按标签过滤（如 "python", "ai", "javascript"）

接入方式：DEV.to public API（无 key，免费）
  https://dev.to/api/articles?per_page=N&top=1
  https://dev.to/api/articles?tag=<tag>&per_page=N

返回字段：title, description, url, positive_reactions_count, tag_list, user, published_timestamp

参考：
  news-aggregator-skill 的 devto 相关抓取逻辑
"""

import requests
from .base import NewsSource, NewsItem, SourceError

_API = "https://dev.to/api/articles"
_TIMEOUT = (5, 15)
_HEADERS = {"Accept": "application/json"}


class DevToSource(NewsSource):
    name = "devto"
    display_name = "DEV.to"
    modules = ["trending", "latest"]

    def fetch(
        self,
        module: str | None = None,
        limit: int = 10,
        keyword: str | None = None,
        tag: str | None = None,
    ) -> list[NewsItem]:
        mod = module or "trending"
        params = {
            "per_page": min(limit * 2, 30),
            "top": 1 if mod == "trending" else None,
        }
        if tag:
            params["tag"] = tag.strip()
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        try:
            resp = requests.get(_API, params=params, timeout=_TIMEOUT, verify=True, headers=_HEADERS)
            resp.raise_for_status()
            articles: list[dict] = resp.json()
        except Exception as e:
            raise SourceError(f"DEV.to fetch failed: {e}") from e

        if not isinstance(articles, list):
            raise SourceError(f"DEV.to unexpected response: {articles}")

        items: list[NewsItem] = []
        for a in articles:
            title = a.get("title") or ""
            if not title:
                continue
            user: dict = a.get("user") or {}
            pub_ts = a.get("published_timestamp") or ""

            items.append(NewsItem(
                source="DEV.to",
                module=f"trending:{tag}" if tag else mod,
                title=title,
                url=a.get("url") or a.get("canonical_url") or "",
                time=pub_ts[:19] + "Z" if pub_ts else None,
                summary=(a.get("description") or "")[:500] or None,
                heat=f"{a.get('positive_reactions_count', 0)} reactions",
                author=user.get("name") or user.get("username") or None,
                extra={
                    "tags": a.get("tag_list", []),
                    "reading_time_minutes": a.get("reading_time_minutes"),
                    "comments_count": a.get("comments_count", 0),
                    "cover_image": a.get("cover_image") or None,
                    "language": a.get("language") or None,
                }
            ))
        items = self.filter_by_keyword(items, keyword)
        return items[:limit]