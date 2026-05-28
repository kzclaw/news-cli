"""
sources/__init__.py — News Source 注册表

统一导出所有 source，按名称注册。
aggregator / CLI 通过这里按名查找 source。
"""

from .base import NewsSource, NewsItem, SourceError
from . import (
    hackernews, github, huggingface, zaker, v2ex, reddit, rss, devto, lobsters
)

# 名称 → source 类 注册表（用于 CLI 按名加载）
# rss 是特殊处理：需单独初始化（带 preset key 或 url），不出现在默认 all 列表
REGISTRY: dict[str, type[NewsSource]] = {
    src.name: src
    for src in [
        hackernews.HackerNewsSource,
        github.GitHubTrendingSource,
        huggingface.HuggingFacePapersSource,
        zaker.ZakerSource,
        v2ex.V2EXSource,
        reddit.RedditSource,
        devto.DevToSource,
        lobsters.LobstersSource,
    ]
}

__all__ = ["NewsSource", "NewsItem", "SourceError", "REGISTRY"]