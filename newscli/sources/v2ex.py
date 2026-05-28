"""
sources/v2ex.py — V2EX Source

支持模块（modules）：
  hot     — 热门话题（默认）
  latest  — 最新话题
  <node>  — 指定节点（如 "programming", "python"）

接入方式：v2ex.com 官方 REST API（无 key，免费）
  hot:    https://www.v2ex.com/api/topics/hot.json
  latest: https://www.v2ex.com/api/topics/latest.json
  node:   https://www.v2ex.com/api/topics/show.json?node_name=<node>

返回字段：[{id, title, url, content, username, replies, created, member, node}]

参考：
  news-aggregator-skill 的 fetch_v2ex()
"""

import requests
from .base import NewsSource, NewsItem, SourceError, relative_time

_API = "https://www.v2ex.com/api"
_TIMEOUT = (5, 15)


class V2EXSource(NewsSource):
    name = "v2ex"
    display_name = "V2EX"
    modules = ["hot", "latest"]

    def fetch(
        self,
        module: str | None = None,
        limit: int = 10,
        keyword: str | None = None,
        node: str | None = None,
    ) -> list[NewsItem]:
        mod = module or "hot"

        if node:
            return self._fetch_node(node, limit, keyword)
        if mod == "hot":
            endpoint = f"{_API}/topics/hot.json"
        elif mod == "latest":
            endpoint = f"{_API}/topics/latest.json"
        else:
            raise SourceError(f"Unknown V2EX module: {mod}")

        try:
            resp = requests.get(endpoint, timeout=_TIMEOUT, verify=True)
            resp.raise_for_status()
            topics: list[dict] = resp.json()
        except Exception as e:
            raise SourceError(f"V2EX {mod} fetch failed: {e}") from e

        items: list[NewsItem] = []
        for t in topics:
            title = t.get("title") or ""
            if not title:
                continue
            member: dict = t.get("member") or {}
            node_info: dict = t.get("node") or {}
            unix_ts = t.get("created", 0)

            items.append(NewsItem(
                source="V2EX",
                module=mod,
                title=title,
                url=t.get("url") or "",
                time=relative_time(unix_ts) if unix_ts else None,
                summary=None,
                heat=f"{t.get('replies', 0)} replies",
                author=member.get("username") or None,
                extra={
                    "username": member.get("username") or "",
                    "node": node_info.get("name") if isinstance(node_info, dict) else "",
                    "v2ex_id": t.get("id"),
                }
            ))
        items = self.filter_by_keyword(items, keyword)
        return items[:limit]

    def _fetch_node(self, node: str, limit: int, keyword: str | None) -> list[NewsItem]:
        try:
            resp = requests.get(
                f"{_API}/topics/show.json",
                params={"node_name": node},
                timeout=_TIMEOUT,
                verify=True
            )
            resp.raise_for_status()
            topics: list[dict] = resp.json()
        except Exception as e:
            raise SourceError(f"V2EX node={node} fetch failed: {e}") from e

        items: list[NewsItem] = []
        for t in topics:
            title = t.get("title") or ""
            if not title:
                continue
            member: dict = t.get("member") or {}
            unix_ts = t.get("created", 0)

            items.append(NewsItem(
                source="V2EX",
                module=f"node:{node}",
                title=title,
                url=t.get("url") or "",
                time=relative_time(unix_ts) if unix_ts else None,
                summary=None,
                heat=f"{t.get('replies', 0)} replies",
                author=member.get("username") or None,
                extra={
                    "username": member.get("username") or "",
                    "node": node,
                    "v2ex_id": t.get("id"),
                }
            ))
        items = self.filter_by_keyword(items, keyword)
        return items[:limit]