"""
sources/zaker.py — ZAKER 新闻 Source

支持模块（modules）：
  hot         — 头条热点（默认）
  category    — 分类新闻（需传 app_id 参数）
  search      — 关键词搜索（需传 keyword 参数）

分类（category 模块的 app_id）：
  9: 娱乐   7: 汽车   8: 体育   13: 科技
  1: 国内   2: 国际   3: 军事   4: 财经   5: 互联网

接入方式：skills.myzaker.com API（无 key，免费）

参考：
  zaker-hot-news / zaker-category-news / zaker-news-search skills
"""

import requests
from .base import NewsSource, NewsItem, SourceError

_HOT_API = "https://skills.myzaker.com/api/v1/article/hot?v=1.0.3"
_CAT_API = "https://skills.myzaker.com/api/v1/article/category?v=1.0.6"
_SEARCH_API = "https://skills.myzaker.com/api/v1/article/search?v=1.0.6"
_TIMEOUT = (5, 15)

_ZAKER_CATEGORIES = {
    "entertainment": "9", "automotive": "7", "sports": "8",
    "technology": "13", "domestic": "1", "international": "2",
    "military": "3", "finance": "4", "internet": "5",
    "9": "娱乐", "7": "汽车", "8": "体育",
    "13": "科技", "1": "国内", "2": "国际",
    "3": "军事", "4": "财经", "5": "互联网",
}


class ZakerSource(NewsSource):
    name = "zaker"
    display_name = "ZAKER"
    modules = ["hot", "category", "search"]

    def fetch(
        self,
        module: str | None = None,
        limit: int = 10,
        keyword: str | None = None,
        category: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
    ) -> list[NewsItem]:
        mod = module or "hot"

        if mod == "hot":
            return self._fetch_hot(limit, keyword)
        elif mod == "category":
            return self._fetch_category(limit, keyword, category)
        elif mod == "search":
            return self._fetch_search(limit, keyword, start_time, end_time)
        else:
            raise SourceError(f"Unknown ZAKER module: {mod}")

    def _fetch_hot(self, limit: int, keyword: str | None) -> list[NewsItem]:
        try:
            resp = requests.get(_HOT_API, timeout=_TIMEOUT, verify=True)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise SourceError(f"ZAKER hot fetch failed: {e}") from e

        if data.get("stat") != 1:
            raise SourceError(f"ZAKER API error: {data.get('msg')}")

        raw_list: list[dict] = data.get("data", {}).get("list", [])
        return self._parse_list(raw_list, "hot", limit, keyword)

    def _fetch_category(
        self, limit: int, keyword: str | None, category: str | None
    ) -> list[NewsItem]:
        app_id = (_ZAKER_CATEGORIES.get(category, category) if category else "13")
        try:
            resp = requests.get(
                _CAT_API, params={"app_id": app_id}, timeout=_TIMEOUT, verify=True
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise SourceError(f"ZAKER category fetch failed: {e}") from e

        if data.get("stat") != 1:
            raise SourceError(f"ZAKER category API error: {data.get('msg')}")

        raw_list: list[dict] = data.get("data", {}).get("list", [])
        cat_name = _ZAKER_CATEGORIES.get(str(app_id), str(app_id))
        return self._parse_list(raw_list, f"category:{cat_name}", limit, keyword)

    def _fetch_search(
        self, limit: int, keyword: str | None,
        start_time: str | None = None, end_time: str | None = None
    ) -> list[NewsItem]:
        if not keyword:
            raise SourceError("ZAKER search requires keyword parameter")
        params = {"keyword": keyword}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        try:
            resp = requests.get(_SEARCH_API, params=params, timeout=_TIMEOUT, verify=True)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise SourceError(f"ZAKER search fetch failed: {e}") from e

        if data.get("stat") != 1:
            raise SourceError(f"ZAKER search API error: {data.get('msg')}")

        raw_list: list[dict] = data.get("data", {}).get("list", [])
        return self._parse_list(raw_list, "search", limit, keyword)

    def _parse_list(
        self, raw_list: list[dict], module: str, limit: int, keyword: str | None
    ) -> list[NewsItem]:
        items: list[NewsItem] = []
        for entry in raw_list:
            title = entry.get("title") or ""
            if not title:
                continue
            items.append(NewsItem(
                source="ZAKER",
                module=module,
                title=title,
                url=entry.get("url") or "",
                time=entry.get("publish_time") or None,
                summary=(entry.get("summary") or "")[:500] or None,
                heat=None,
                author=entry.get("author") or None,
                extra={}
            ))
        items = self.filter_by_keyword(items, keyword)
        return items[:limit]