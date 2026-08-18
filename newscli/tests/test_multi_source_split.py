"""
test_multi_source_split.py — v1.1.2 多源分隔符修复（KR3）

回归验证 `_parse_filter` 同时支持 `&` 与 `,` 作为多源分隔符。
修复前 `filter_str.split("&")` 只认 `&`，导致逗号分隔多源时
`hackernews:topstories,github:trending` 被当作单个 module 名而报错。
"""
import sys
from pathlib import Path

# 允许从任意 CWD 运行：把仓库根加入 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from newscli.aggregator import NewsAggregator  # noqa: E402


def _parse(source: str):
    return NewsAggregator._parse_filter(source)


def test_single_source():
    """单源 `hackernews:topstories` → 1 个 parsed 项"""
    items = _parse("hackernews:topstories")
    assert len(items) == 1, f"expected 1 item, got {len(items)}"
    assert items[0][0] == "hackernews"
    assert items[0][1] == "topstories"


def test_multi_source_comma():
    """多源逗号 `hackernews:topstories,github:trending` → 2 项（修复目标）"""
    items = _parse("hackernews:topstories,github:trending")
    assert len(items) == 2, f"expected 2 items (comma split), got {len(items)}"
    assert items[0][0] == "hackernews"
    assert items[1][0] == "github"
    assert items[1][1] == "trending"


def test_multi_source_ampersand():
    """多源 & `hackernews:topstories&github:trending` → 2 项（向后兼容）"""
    items = _parse("hackernews:topstories&github:trending")
    assert len(items) == 2, f"expected 2 items (ampersand split), got {len(items)}"
    assert items[0][0] == "hackernews"
    assert items[1][0] == "github"


def test_multi_source_comma_with_spaces():
    """含空格 `a:top, b:trend` → 2 项（strip 前后空格）"""
    items = _parse("a:top, b:trend")
    assert len(items) == 2, f"expected 2 items (comma + spaces), got {len(items)}"
    assert items[0] == ("a", "top", {})
    assert items[1] == ("b", "trend", {})