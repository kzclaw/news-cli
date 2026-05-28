"""
sources/base.py — News Source 抽象基类 + 统一输出规范

【统一 NewsItem Schema — 所有 source 必须遵守】
每个 source 的 fetch() 返回的每条 item 必须包含以下全部字段：
  source, module, title, url, time, summary, heat, author
  extra (source-specific supplemental data)
  如果 source 不提供某字段 → 填 None（不省略 key）

【字段规范】
  source  : str，来源平台名（如 "Hacker News"）
  module  : str，模块/子频道名（如 "topstories", "newest", "technology"）
  title   : str，文章标题（必填，不能为空）
  url     : str，原文链接（必填，不能为空）
  time    : str | None，时间（统一 ISO8601 或自然语言）
  summary : str | None，摘要/简介（无摘要则 None）
  heat    : str | None，热度指标（如 "928 points"，无则 None）
  author  : str | None，作者/发布者（无则 None）
  extra   : dict，source-specific 补充数据（始终为 dict）
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


@dataclass
class NewsItem:
    """
    统一新闻条目格式 — 所有 source 所有 module 必须返回此格式。

    字段说明：
    - source : 来源平台名，如 "Hacker News" / "GitHub" / "ZAKER"
    - module : 模块/子频道名，如 "topstories" / "trending" / "hot" / "technology"
    - title  : 文章标题（唯一必填字段，不能为空字符串）
    - url    : 原文链接（唯一必填字段，不能为空字符串）
    - time   : 发布时间，格式优先 ISO8601（2026-05-28T19:25:00+08:00），
               无法转换时用自然语言（"15h ago" / "2d ago"），无时间则 None
    - summary: 文章摘要/简介，不超过 500 字符，无则 None
    - heat   : 热度字符串，如 "928 points" / "64k stars" / "229 replies"
               无热度指标则 None（不要填 "N/A" 或空字符串）
    - author : 作者/发布者名称，无则 None
    - extra  : source-specific 补充数据（如 HN 有 hn_id/hn_url，
               GitHub 有 repo/language/stars，ZAKER 有 category 等）
               始终为 dict，字段名 camelCase 或 snake_case 均可
    """
    source: str
    module: str           # e.g. "topstories" / "hot" / "technology" / "search"
    title: str
    url: str
    time: Optional[str] = None
    summary: Optional[str] = None
    heat: Optional[str] = None
    author: Optional[str] = None
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """输出时转换为 dict，None 字段保留（不省略）"""
        return {
            "source": self.source,
            "module": self.module,
            "title": self.title,
            "url": self.url,
            "time": self.time,
            "summary": self.summary,
            "heat": self.heat,
            "author": self.author,
            "extra": self.extra,
        }

    def display_dict(self) -> dict:
        """
        用于人类可读输出（CLI text 模式）。
        None 字段不显示（从输出中移除），区别于 to_dict。
        """
        d = self.to_dict()
        return {k: v for k, v in d.items() if v is not None and v != {}}


class NewsSource(ABC):
    """
    News Source 抽象基类。

    实现规范：
    1. 类属性 name       ：CLI 参数名（如 "hackernews"）
    2. 类属性 display_name：显示名称（如 "Hacker News"）
    3. 类属性 modules     ：list[str]，支持的所有 module 名
    4. 方法 fetch(module, limit, keyword) -> list[NewsItem]
       - module: 子模块名，如 "topstories" / "hot" / "technology"
       - limit: 最大返回条数
       - keyword: 关键词过滤（可选，None = 不过滤）
    5. 网络请求必须带 timeout（connect 5s / read 15s）
    6. 异常必须显式捕获，转换为 SourceError 后再向上报
    """

    name: str = ""
    display_name: str = ""
    modules: list[str] = []  # e.g. ["hot", "newest", "ask", "show"]

    @abstractmethod
    def fetch(
        self,
        module: str | None = None,
        limit: int = 10,
        keyword: str | None = None,
    ) -> list[NewsItem]:
        """
        拉取新闻。

        Args:
            module  : 子模块名，默认 self.modules[0]
            limit   : 最大返回条数
            keyword : 关键词过滤（可选，None 表示不过滤）

        Returns:
            list[NewsItem]: 按热度/时间排序的新闻列表

        Raises:
            SourceError: 网络或解析错误（不裸抛）
        """
        ...

    def filter_by_keyword(
        self,
        items: list[NewsItem],
        keyword: Optional[str],
    ) -> list[NewsItem]:
        """关键词过滤（默认实现：标题匹配）"""
        if not keyword:
            return items
        import re
        keywords = [k.strip() for k in keyword.split(',') if k.strip()]
        pattern = '|'.join([r'\b' + re.escape(k) + r'\b' for k in keywords])
        regex = re.compile(pattern, re.IGNORECASE)
        return [item for item in items if regex.search(item.title)]

    def module_default(self) -> str:
        """默认 module（第一个）"""
        return self.modules[0] if self.modules else ""


class SourceError(Exception):
    """Source 层网络/解析异常，不向上裸传"""
    pass


# ─── 时间解析工具 ────────────────────────────────────────────────

def parse_hn_time(unix_ts: int) -> str:
    """Hacker News Unix timestamp → ISO8601 + 自然语言"""
    if not unix_ts:
        return None
    dt = datetime.fromtimestamp(unix_ts, tz=timezone.utc)
    return dt.isoformat()


def parse_reddit_time(utc_ts: float) -> str:
    """Reddit UTC timestamp → ISO8601"""
    if not utc_ts:
        return None
    dt = datetime.fromtimestamp(utc_ts, tz=timezone.utc)
    return dt.isoformat()


def relative_time(unix_ts: int | float) -> str:
    """Unix timestamp → 自然语言相对时间（"15h ago"）"""
    if not unix_ts:
        return None
    delta = datetime.now(timezone.utc) - datetime.fromtimestamp(unix_ts, tz=timezone.utc)
    h = int(delta.total_seconds() // 3600)
    if h < 1:
        return f"{int(delta.total_seconds() // 60)}m ago"
    if h < 24:
        return f"{h}h ago"
    return f"{h // 24}d ago"


def iso_now() -> str:
    """当前 UTC 时间 ISO8601"""
    return datetime.now(timezone.utc).isoformat()