"""
sources/hackernews.py — Hacker News Source

支持模块（modules）：
  topstories  — 首页热门（默认）
  newest      — 最新
  ask         — Ask HN
  show        — Show HN
  jobs        — 招聘

接入方式：Firebase API（无 key，免费）
  topstories.json / newstories.json / askstories.json / showstories.json / jobstories.json
  → item/{id}.json → 获取每个 story 详情
"""

import requests
from .base import NewsSource, NewsItem, SourceError, relative_time

HN_FB = "https://hacker-news.firebaseio.com/v0"
_TIMEOUT = (5, 15)

_HN_MODULES = {
    "topstories": HN_FB + "/topstories.json",
    "newest": HN_FB + "/newstories.json",
    "ask": HN_FB + "/askstories.json",
    "show": HN_FB + "/showstories.json",
    "jobs": HN_FB + "/jobstories.json",
}


class HackerNewsSource(NewsSource):
    name = "hackernews"
    display_name = "Hacker News"
    modules = ["topstories", "newest", "ask", "show", "jobs"]

    def fetch(
        self,
        module: str | None = None,
        limit: int = 10,
        keyword: str | None = None,
    ) -> list[NewsItem]:
        mod = module or "topstories"
        if mod not in _HN_MODULES:
            raise SourceError(f"Unknown HN module: {mod}. Valid: {list(_HN_MODULES.keys())}")

        url = _HN_MODULES[mod]
        try:
            ids = requests.get(url, timeout=_TIMEOUT, verify=True).json()
            if not isinstance(ids, list):
                raise SourceError(f"Unexpected HN stories response for {mod}")
            ids = ids[:limit * 3]
        except SourceError:
            raise
        except Exception as e:
            raise SourceError(f"HN {mod} fetch failed: {e}") from e

        items: list[NewsItem] = []
        for raw_id in ids:
            if len(items) >= limit * 2:
                break
            try:
                story = requests.get(
                    f"{HN_FB}/item/{raw_id}.json", timeout=_TIMEOUT, verify=True
                ).json()
            except Exception:
                continue
            if not story or story.get("deleted") or story.get("dead"):
                continue
            if story.get("type") not in ("story", "job") and not (mod == "jobs"):
                continue

            title = story.get("title") or ""
            url = story.get("url") or f"{HN_FB}/item/{raw_id}.html"
            unix_ts = story.get("time", 0)
            score = story.get("score", 0)

            items.append(NewsItem(
                source="Hacker News",
                module=mod,
                title=title,
                url=url,
                time=relative_time(unix_ts) if unix_ts else None,
                summary=None,
                heat=f"{score} points" if score else None,
                author=story.get("by") or None,
                extra={
                    "hn_id": raw_id,
                    "hn_url": f"https://news.ycombinator.com/item?id={raw_id}",
                    "descendants": story.get("descendants", 0),
                }
            ))

        items = self.filter_by_keyword(items, keyword)
        return items[:limit]