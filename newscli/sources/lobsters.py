"""
sources/lobsters.py — Lobsters Source

支持模块（modules）：
  hottest     — 热门（默认）
  newest      — 最新

接入方式：Lobsters JSON API（无 key，免费）
  https://lobste.rs/hottest.json?limit=N
  https://lobste.rs/newest.json?limit=N

返回字段：title, url, short_id, score, comment_count, tags, submitted_by, created_at

参考：
  news-aggregator-skill 的 lobsters 相关抓取逻辑
  TRENDRADAR 的 lobsters 接入方案
"""

import requests
from .base import NewsSource, NewsItem, SourceError

_API = "https://lobste.rs"
_TIMEOUT = (5, 15)


class LobstersSource(NewsSource):
    name = "lobsters"
    display_name = "Lobsters"
    modules = ["hottest", "newest"]

    def fetch(
        self,
        module: str | None = None,
        limit: int = 10,
        keyword: str | None = None,
    ) -> list[NewsItem]:
        mod = module or "hottest"
        if mod == "newest":
            endpoint = f"{_API}/newest.json"
        else:
            endpoint = f"{_API}/hottest.json"

        try:
            resp = requests.get(endpoint, params={"limit": limit * 2}, timeout=_TIMEOUT, verify=True)
            resp.raise_for_status()
            stories: list[dict] = resp.json()
        except Exception as e:
            raise SourceError(f"Lobsters fetch failed: {e}") from e

        if not isinstance(stories, list):
            raise SourceError(f"Lobsters unexpected response: {stories}")

        items: list[NewsItem] = []
        for s in stories:
            title = s.get("title") or ""
            if not title:
                continue
            created = s.get("created_at") or ""

            items.append(NewsItem(
                source="Lobsters",
                module=mod,
                title=title,
                url=s.get("url") or "",
                time=created[:19] + "Z" if created else None,
                summary=None,
                heat=f"{s.get('score', 0)} points",
                author=s.get("submitter_user") or None,
                extra={
                    "short_id": s.get("short_id") or "",
                    "tags": s.get("tags", []),
                    "comment_count": s.get("comment_count", 0),
                    "lobsters_url": s.get("short_id") and f"https://lobste.rs/s/{s['short_id']}" or None,
                }
            ))
        items = self.filter_by_keyword(items, keyword)
        return items[:limit]