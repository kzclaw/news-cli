"""
sources/reddit.py — Reddit Source

支持模块（modules）：
  popular      — r/popular 热门（默认）
  hot          — 综合热门
  <subreddit>  — 指定 subreddit（如 "technology", "science", "worldnews"）

接入方式：Reddit JSON API（无 key，但需要 User-Agent）
  https://www.reddit.com/r/popular.json?limit=<n>
  https://www.reddit.com/r/<subreddit>/hot.json?limit=<n>

返回字段：title, subreddit, author, url, score, num_comments, created_utc, selftext, is_self

参考：
  TRENDRADAR 的 Reddit 接入方案（Reddit JSON API 免费）
"""

import requests
from .base import NewsSource, NewsItem, SourceError, parse_reddit_time

_REDDIT_BASE = "https://www.reddit.com"
_TIMEOUT = (5, 15)
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NewsCLI/1.0)"}


class RedditSource(NewsSource):
    name = "reddit"
    display_name = "Reddit"
    modules = ["popular", "hot"]

    def fetch(
        self,
        module: str | None = None,
        limit: int = 10,
        keyword: str | None = None,
        subreddit: str | None = None,
    ) -> list[NewsItem]:
        # Determine which subreddit to query
        if subreddit:
            sub = subreddit
            mod = f"r/{sub}"
        else:
            mod = module or "popular"
            sub = "popular" if mod == "popular" else mod

        try:
            resp = requests.get(
                f"{_REDDIT_BASE}/r/{sub}/hot.json",
                params={"limit": limit * 2},
                timeout=_TIMEOUT,
                verify=True,
                headers=_HEADERS
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise SourceError(f"Reddit r/{sub} fetch failed: {e}") from e

        posts = data.get("data", {}).get("children", [])
        items: list[NewsItem] = []
        for post_wrapper in posts:
            post = post_wrapper.get("data", {})
            title = post.get("title") or ""
            if not title:
                continue
            url = post.get("url") or post.get("permalink") or ""
            if url and not url.startswith("http"):
                url = f"https://reddit.com{url}"
            utc_ts = post.get("created_utc", 0)
            score = post.get("score", 0)
            selftext = post.get("selftext") or ""
            is_self = post.get("is_self", False)

            items.append(NewsItem(
                source="Reddit",
                module=mod,
                title=title,
                url=url,
                time=parse_reddit_time(utc_ts) if utc_ts else None,
                summary=selftext[:500] if selftext else None,
                heat=f"{score} upvotes",
                author=post.get("author") or None,
                extra={
                    "subreddit": post.get("subreddit") or sub,
                    "num_comments": post.get("num_comments", 0),
                    "domain": post.get("domain") or "",
                    "is_self": is_self,
                    "permalink": f"https://reddit.com{post.get('permalink', '')}",
                }
            ))
        items = self.filter_by_keyword(items, keyword)
        return items[:limit]