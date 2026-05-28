#!/usr/bin/env python3
"""
enrich.py — URL enrichment: fetch og:description / meta description via curl

对 summary=null 的 item 并发拉取原文 description，填充 summary 字段。
使用 curl（subprocess）绕过 Python requests 对某些站点的 TLS 超时问题。
"""

import concurrent.futures
import re
import subprocess
from dataclasses import dataclass


@dataclass
class EnrichResult:
    url: str
    description: str | None  # None = failed/not found
    error: str | None


def fetch_description(url: str, timeout: int = 8) -> EnrichResult:
    """
    用 curl 获取页面 meta og:description，失败返回 None。
    超时视为失败，不阻塞。
    """
    try:
        result = subprocess.run(
            [
                "curl", "-s", "-L", "--max-time", str(timeout),
                "-A", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "-H", "Accept: text/html,application/xhtml+xml,*/*",
                "-H", "Accept-Language: en-US,en;q=0.9",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=timeout + 1,  # process-level timeout slightly higher
        )
        html = result.stdout
        # og:description first (richer)
        m = _extract_description(html)
        return EnrichResult(url=url, description=m, error=None)
    except subprocess.TimeoutExpired:
        return EnrichResult(url=url, description=None, error="timeout")
    except Exception as e:
        return EnrichResult(url=url, description=None, error=str(e))


def _extract_description(html: str) -> str | None:
    """从 HTML 中提取 og:description 或 meta description"""
    patterns = [
        # og:description
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']',
        r'<meta[^>]+content=["\'](.*?)["\'][^>]+property=["\']og:description["\']',
        # meta description
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
        r'<meta[^>]+content=["\'](.*?)["\'][^>]+name=["\']description["\']',
    ]
    for pattern in patterns:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            text = m.group(1).strip()
            # Clean HTML entities
            text = text.replace("&amp;", "&").replace("&quot;", '"').replace("&#x27;", "'").replace("&lt;", "<").replace("&gt;", ">").replace("&#x2F;", "/").replace("&nbsp;", " ")
            if text:
                return text[:500]
    return None


def enrich_items(items: list[dict], max_workers: int = 8) -> list[dict]:
    """
    对所有 summary=null 的 item 并发拉取 description。

    Args:
        items: NewsItem.to_dict() 列表
        max_workers: 并发线程数

    Returns:
        同输入结构，summary 已填充的 item（不改变顺序）
    """
    # Build work: index → (item, url)
    null_items = [(i, items[i]) for i in range(len(items)) if items[i].get("summary") is None]

    if not null_items:
        return items

    urls_to_fetch = [(i, item["url"]) for i, item in null_items if item.get("url")]

    if not urls_to_fetch:
        return items

    results_map: dict[int, str | None] = {}  # index → description

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, len(urls_to_fetch))) as ex:
        futures = {ex.submit(fetch_description, url): idx for idx, url in urls_to_fetch}
        for fut in concurrent.futures.as_completed(futures):
            idx = futures[fut]
            try:
                res = fut.result()
                results_map[idx] = res.description
            except Exception:
                results_map[idx] = None

    # Merge back
    enriched = []
    for i, item in enumerate(items):
        if i in results_map and results_map[i]:
            item = {**item, "summary": results_map[i]}
        enriched.append(item)

    return enriched