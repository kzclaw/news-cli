#!/usr/bin/env python3
"""
validate.py — NewsItem v1.1 schema 验证

验证规则：
- heat 是字符串：默认 warn + continue；--strict 硬失败
- heat 可解析：用正则 (\d+(?:,\d+)*) 提取
- extra 兜底：找 extra.stars/descendants/upvotes
- time 不为 None（如果 source 应该有）
- url 非空字符串
"""
import re
from typing import Optional


# heat 字符串提取模式
HEAT_NUMERIC_RE = re.compile(r"(\d+(?:,\d+)*(?:\.\d+)?)")

# source → extra 字段兜底优先级
EXTRA_INT_FIELDS = ["stars", "descendants", "upvotes", "score"]


def parse_heat_int(heat_str: str | None) -> int | None:
    """
    从 heat 字符串解析出 int。
    例子：
      '10,748 stars' → 10748
      '455 points' → 455
      '1.5w 阅读' → 15000 (中文 w = 万)
      '11 reactions' → 11
    失败返回 None。
    """
    if not heat_str or not isinstance(heat_str, str):
        return None
    # 清理：去掉 "stars"/"points"/"upvotes"/"reactions" 等后缀
    s = heat_str.strip()
    # 尝试正则
    m = HEAT_NUMERIC_RE.search(s)
    if not m:
        return None
    num_str = m.group(1).replace(",", "")
    try:
        # 处理中文单位 "1.5w" = 15000
        if s.lower().endswith("w") or "w 阅读" in s or "w " in s.lower():
            return int(float(num_str) * 10000)
        return int(float(num_str))
    except (ValueError, TypeError):
        return None


def find_extra_int(item: dict) -> int | None:
    """
    从 extra 字段里找数字（stars/descendants/upvotes/score 优先级）
    """
    extra = item.get("extra") or {}
    for k in EXTRA_INT_FIELDS:
        v = extra.get(k)
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            try:
                return int(v.replace(",", ""))
            except (ValueError, TypeError):
                continue
    return None


def validate_item(item: dict, source: str | None = None) -> tuple[dict, list[str]]:
    """
    验证单个 item。
    返回 (修正后的 item, warnings 列表)。
    默认 warn 模式；--strict 由调用方根据 warnings 决定 hard fail。
    """
    warnings: list[str] = []
    src = source or item.get("source") or "unknown"

    # 1. heat 验证
    heat = item.get("heat")
    if heat is not None and not isinstance(heat, str):
        warnings.append(
            f"{src} item '{item.get('title', '?')[:40]}': heat 不是字符串（{type(heat).__name__}）"
        )
    elif heat:
        # 尝试解析
        parsed = parse_heat_int(heat)
        if parsed is None:
            # 字符串解析失败 → 查 extra
            extra_int = find_extra_int(item)
            if extra_int is not None:
                warnings.append(
                    f"{src} item '{item.get('title', '?')[:40]}': heat 解析失败（'{heat}'），使用 extra={extra_int}"
                )
            else:
                warnings.append(
                    f"{src} item '{item.get('title', '?')[:40]}': heat 解析失败且无 extra 兜底（'{heat}'）"
                )
        else:
            # 解析成功，把解析值放 extra（如果有位置）
            extra = item.get("extra") or {}
            if "heat_int" not in extra:
                extra["heat_int"] = parsed
                item["extra"] = extra

    # 2. time 不为 None（如果 source 应该有时间）
    if src in ("Hacker News", "V2EX", "DEV.to", "Lobsters", "ZAKER") and item.get("time") is None:
        warnings.append(
            f"{src} item '{item.get('title', '?')[:40]}': time 为 None（应该有时间）"
        )

    # 3. url 校验（非空字符串）
    url = item.get("url")
    if url == "":
        warnings.append(
            f"{src} item '{item.get('title', '?')[:40]}': url 是空字符串（应改为 None）"
        )
        # 修复：空字符串 → None
        item["url"] = None

    return item, warnings


def validate_items(items: list[dict], strict: bool = False) -> tuple[list[dict], list[str]]:
    """
    验证所有 items。
    strict=True 时遇到任何 warning 就 raise。
    返回 (validated_items, all_warnings)。
    """
    all_warnings: list[str] = []
    validated: list[dict] = []

    for item in items:
        v_item, warnings = validate_item(item)
        validated.append(v_item)
        all_warnings.extend(warnings)

    if strict and all_warnings:
        from newscli.sources import SourceError
        raise SourceError(
            f"Strict validation failed: {len(all_warnings)} warnings\n" +
            "\n".join(all_warnings[:5])
        )

    return validated, all_warnings
