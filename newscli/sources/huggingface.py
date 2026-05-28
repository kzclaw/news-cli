"""
sources/huggingface.py — HuggingFace Daily Papers Source

支持模块（modules）：
  daily        — 当日热门论文（默认）
  trending     — 近期热门（最近7天）

接入方式：HF API（无 key，免费）
  daily:  https://huggingface.co/api/daily_papers?date={YYYY-MM-DD}
  trending: https://huggingface.co/api/papers?sort=hot&limit=20

返回字段：title, summary, upvotes, paper_id, url

参考：
  daily-trends-workflow.md — curl https://huggingface.co/api/daily_papers?date=YYYY-MM-DD
"""

import datetime
import requests
from .base import NewsSource, NewsItem, SourceError

_HF_DAILY = "https://huggingface.co/api/daily_papers"
_HF_TRENDING = "https://huggingface.co/api/papers"
_TIMEOUT = (5, 15)


class HuggingFacePapersSource(NewsSource):
    name = "huggingface"
    display_name = "HuggingFace Papers"
    modules = ["daily", "trending"]

    def fetch(
        self,
        module: str | None = None,
        limit: int = 10,
        keyword: str | None = None,
    ) -> list[NewsItem]:
        mod = module or "daily"
        try:
            if mod == "daily":
                date = datetime.date.today().isoformat()
                resp = requests.get(
                    f"{_HF_DAILY}?date={date}",
                    timeout=_TIMEOUT,
                    verify=True,
                    headers={"Accept": "application/json"}
                )
            elif mod == "trending":
                resp = requests.get(
                    f"{_HF_TRENDING}?sort=hot&limit={limit * 2}",
                    timeout=_TIMEOUT,
                    verify=True,
                    headers={"Accept": "application/json"}
                )
            else:
                raise SourceError(f"Unknown HF module: {mod}")
            resp.raise_for_status()
            papers: list[dict] = resp.json()
        except Exception as e:
            raise SourceError(f"HF papers fetch failed ({mod}): {e}") from e

        if isinstance(papers, dict) and "papers" in papers:
            papers = papers["papers"]

        items: list[NewsItem] = []
        for p in papers:
            paper = p if isinstance(p, dict) else {}
            # Handle both direct paper dict and nested {paper: {...}} structure
            paper_data = paper.get("paper") if isinstance(p, dict) and "paper" in p else paper
            if not isinstance(paper_data, dict):
                continue
            paper_id = paper_data.get("id") or ""
            title = paper_data.get("title") or ""
            if not title:
                continue
            upvotes = paper_data.get("upvotes", 0)
            summary = (paper_data.get("summary") or "")[:500]
            url = paper_data.get("url") or (f"https://huggingface.co/papers/{paper_id}" if paper_id else "")

            items.append(NewsItem(
                source="HuggingFace",
                module=mod,
                title=title,
                url=url,
                time=None,
                summary=summary or None,
                heat=f"+{upvotes} upvotes" if upvotes else None,
                author=None,
                extra={
                    "paper_id": paper_id,
                    "upvotes": upvotes,
                }
            ))
        items = self.filter_by_keyword(items, keyword)
        return items[:limit]