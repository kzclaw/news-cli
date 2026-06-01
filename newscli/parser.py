#!/usr/bin/env python3
"""
parser.py — Natural Language DSL parser for news-cli

设计原则：
- 独立模块：可单独 import 测试，可在任何 Python 代码中复用
- 与 aggregator 完全解耦：parser 只输出结构化 dict
- 可扩展：新语法、新 token 只改这里
- 兼容现有 cli.py：两种入口共存

返回格式 ParseResult：
{
    "command": "list" | "fetch",
    "list_target": str,
    "fetch": {
        "source_filter": str,   # aggregator 格式 "source:module&source2:module2"
        "limit": int,
        "output": "text" | "json",
        "enrich": bool,
        "keyword": str | None,
        "params": dict,
        "_clauses": list[dict], # 内部用：各 clause 详情
    }
}
"""

from dataclasses import dataclass, field
from typing import Literal, Optional

# ──────────────────────────────────────────────
# Registry
# ──────────────────────────────────────────────

ALL_SOURCES = {
    "hackernews": {"modules": ["topstories", "newest", "ask", "show", "jobs"], "params": []},
    "github":     {"modules": ["trending"],                                        "params": ["language"]},
    "huggingface":{"modules": ["daily", "trending"],                              "params": []},
    "zaker":      {"modules": ["hot", "category", "search"],                      "params": ["category", "keyword"]},
    "v2ex":       {"modules": ["hot", "latest", "node"],                           "params": ["node"]},
    "reddit":     {"modules": ["popular", "hot"],                                  "params": ["subreddit"]},
    "devto":      {"modules": ["trending", "latest"],                             "params": ["tag"]},
    "lobsters":   {"modules": ["hottest", "newest"],                              "params": []},
    "rss":        {"modules": [],                                                  "params": ["url"]},
}

CONNECTORS  = {"&", "and"}
FIXED_TOKENS = {"json", "noenrich", "no", "enrich", "all",
                "list", "lists", "ls", "get", "fetch", "看", "拉", "找", "search",
                # v1.1 新增
                "dedup", "strict", "novalidate", "noenrich"}
LIST_VERBS  = {"list", "lists", "ls"}
FETCH_VERBS = {"get", "fetch", "看", "拉", "找", "search"}


# ──────────────────────────────────────────────
# ParseResult
# ──────────────────────────────────────────────

@dataclass
class ParseResult:
    command:    Literal["list", "fetch"] = "fetch"
    list_target: str = "sources"
    fetch:      dict = field(default_factory=dict)
    # v1.1: ParseResult.fetch 现在多 3 字段：dedup / strict / validate


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────

def parseNL(raw: str) -> ParseResult:
    """解析自然语言输入，纯字符串分词，无 AI。"""
    raw = raw.strip()
    if not raw:
        raise ParseError("空输入")

    tokens = _tokenize(raw)
    first  = tokens[0].lower()

    if first in LIST_VERBS:
        return _parse_list(tokens)
    elif first in FETCH_VERBS:
        return _parse_fetch(tokens)
    else:
        raise ParseError(f"未知命令：{first}，支持：get / list")


# ──────────────────────────────────────────────
# Tokenizer
# ──────────────────────────────────────────────

def _tokenize(raw: str) -> list[str]:
    """按 whitespace 拆分，& / and 保持为独立 token。"""
    import re
    # 保护引号
    quoted = {}
    def _shield(m):
        key = f"\x00Q{len(quoted)}\x00"
        quoted[key] = m.group(0)
        return key
    raw = re.sub(r"'(?:[^']|\\')*'|\"(?:[^\"\\]|\\.)*\"", _shield, raw)
    tokens = []
    for t in raw.split():
        t = t.strip()
        if t:
            tokens.append(quoted.get(t.strip('"').strip("'"), t))
    return tokens


# ──────────────────────────────────────────────
# List
# ──────────────────────────────────────────────

def _parse_list(tokens: list[str]) -> ParseResult:
    rest = [t.lower() for t in tokens[1:]]
    if not rest:
        return ParseResult(command="list", list_target="sources")
    first = rest[0]
    if first in ("source", "sources", "all"):
        return ParseResult(command="list", list_target="sources")
    if first in ("module", "modules"):
        return ParseResult(command="list", list_target="modules")
    if first in ALL_SOURCES:
        return ParseResult(command="list", list_target=first)
    raise ParseError(f"list {first}：list / list sources / list modules / list <源名>")


# ──────────────────────────────────────────────
# Fetch — 主入口
# ──────────────────────────────────────────────

def _parse_fetch(tokens: list[str]) -> ParseResult:
    rest = tokens[1:]
    if not rest:
        raise ParseError("get 后需要指定源，例如：get hackernews topstories")

    # ── 按 connector 分 clause ──
    raw_segments: list[str] = []
    current: list[str] = []
    for t in rest:
        if t.lower() in CONNECTORS:
            if current:
                raw_segments.append(" ".join(current))
                current = []
        else:
            current.append(t)
    if current:
        raw_segments.append(" ".join(current))

    # ── 逐 clause 解析 ──
    clause_token_lists = [_tokenize(seg) for seg in raw_segments]
    parsed = [_parse_clause(ct) for ct in clause_token_lists]

    source_filter = "&".join(p["source_filter"] for p in parsed)
    first = parsed[0]

    return ParseResult(
        command="fetch",
        fetch={
            "source_filter": source_filter,
            "limit":   first["limit"],
            "output":  first["output"],
            "enrich":  first["enrich"],
            "keyword": first["keyword"],
            "params":  first["params"],
            # v1.1 flags（取首个 clause 的；如想合并所有 clause 可改）
            "dedup":   first.get("dedup"),
            "strict":  first.get("strict", False),
            "validate": first.get("validate", True),
            "_clauses": parsed,
        },
    )


# ──────────────────────────────────────────────
# Clause 解析
# ──────────────────────────────────────────────

def _parse_clause(tokens: list[str]) -> dict:
    """tokens[0]=verb, tokens[1]=source, tokens[2+]=module/modifiers"""
    if not tokens:
        raise ParseError("空 clause")

    src, mod, extra = _extract_source_and_module(tokens)
    # 剩余 tokens 去 parse modifiers
    # rest = tokens 在 source+module 解析时已经消费掉了 extra，剩下的全是 modifiers
    rest = extra.pop("_rest", [])
    mods = _parse_modifiers(rest)
    merged_extra = {**extra, **mods["extra"]}
    source_filter = _build_filter(src, mod, merged_extra)

    return {
        "source_filter": source_filter,
        "limit":   mods["limit"],
        "output":  mods["output"],
        "enrich":  mods["enrich"],
        "keyword": mods["keyword"],
        "params":  merged_extra,
        # v1.1: 跨 clause 共享的 flag
        "dedup":   mods.get("dedup"),
        "strict":  mods.get("strict", False),
        "validate": mods.get("validate", True),
    }


def _extract_source_and_module(tokens: list[str]) -> tuple:
    """
    解析 source + module + extra。
    返回 (source, module, extra_dict)，extra_dict 里会把剩余的 rest 放 _rest。
    """
    rest = list(tokens)
    first = rest[0].lower()
    rest = rest[1:]

    if first == "all":
        return ("all", "", {"_rest": rest})

    if first == "rss":
        if not rest:
            raise ParseError("rss 需要 preset 名或 URL")
        second = rest[0]
        if "://" in second or second.endswith((".xml", ".rss", ".atom", ".json")):
            return ("rss", "", {"url": second, "_rest": rest[1:]})
        return ("rss", second, {"_rest": rest[1:]})

    if first == "reddit":
        if not rest:
            return ("reddit", "", {"_rest": []})
        second = rest[0].lower()
        if second == "subreddit":
            name = rest[1] if len(rest) > 1 else ""
            return ("reddit", "", {"subreddit": name, "_rest": rest[2:]})
        if second.startswith("r/"):
            name = second[2:]
            return ("reddit", "", {"subreddit": name, "_rest": rest[1:]})
        if second in ("popular", "hot"):
            return ("reddit", second, {"_rest": rest[1:]})
        return ("reddit", second, {"_rest": rest[1:]})

    if first == "v2ex":
        if not rest:
            return ("v2ex", "", {"_rest": []})
        second = rest[0].lower()
        if second == "node":
            name = rest[1] if len(rest) > 1 else ""
            return ("v2ex", "node", {"node": name, "_rest": rest[2:]})
        if second in ("hot", "latest"):
            return ("v2ex", second, {"_rest": rest[1:]})
        return ("v2ex", second, {"_rest": rest[1:]})

    if first == "devto":
        if not rest:
            return ("devto", "", {"_rest": []})
        second = rest[0].lower()
        if second in ("trending", "latest"):
            rest = rest[1:]
            if rest and rest[0].lower() == "tag":
                tag = rest[1] if len(rest) > 1 else ""
                return ("devto", second, {"tag": tag, "_rest": rest[2:]})
            return ("devto", second, {"_rest": rest})
        if second == "tag":
            tag = rest[1] if len(rest) > 1 else ""
            return ("devto", "trending", {"tag": tag, "_rest": rest[2:]})
        return ("devto", second, {"_rest": rest[1:]})

    if first == "zaker":
        if not rest:
            return ("zaker", "", {"_rest": []})
        second = rest[0].lower()
        if second == "category":
            name = rest[1] if len(rest) > 1 else ""
            return ("zaker", "category", {"category": name, "_rest": rest[2:]})
        if second == "search":
            kw = rest[1] if len(rest) > 1 else ""
            return ("zaker", "search", {"keyword": kw, "_rest": rest[2:]})
        return ("zaker", second, {"_rest": rest[1:]})

    # ── normal source ──
    if first not in ALL_SOURCES:
        raise ParseError(f"未知源：{first}，支持：{', '.join(ALL_SOURCES)}")
    if not rest:
        return (first, "", {"_rest": []})
    module = rest[0].lower()
    rest = rest[1:]
    if ALL_SOURCES[first]["modules"] and module not in ALL_SOURCES[first]["modules"]:
        raise ParseError(f"{first} 不支持模块：{module}，可用：{', '.join(ALL_SOURCES[first]['modules'])}")
    return (first, module, {"_rest": rest})


def _build_filter(source: str, module: str, extra: dict) -> str:
    """组合为 aggregator 格式的 filter 字符串。"""
    if source == "all":
        return "all"
    if source == "rss":
        if module:
            return f"rss:{module}"
        url = extra.get("url", "")
        return f"rss:{url}" if url else "rss:"
    if module:
        return f"{source}:{module}"
    if source == "v2ex" and "node" in extra:
        return f"v2ex:node:{extra['node']}"
    if source == "reddit" and "subreddit" in extra:
        return f"reddit:r/{extra['subreddit']}"
    return f"{source}:"


# ──────────────────────────────────────────────
# Modifiers
# ──────────────────────────────────────────────

def _parse_modifiers(tokens: list[str]) -> tuple:
    """
    解析 limit / output / enrich / keyword / extra / v1.1 flags。
    返回 (limit, output, enrich, keyword, extra_dict, v1.1_flags)
    v1.1_flags = {"dedup": int|None, "strict": bool, "validate": bool}
    """
    limit   = 10
    output  = "text"
    enrich  = True
    keyword: Optional[str] = None
    extra: dict = {}
    # v1.1 新增
    dedup: Optional[int] = None      # 显式给定时覆盖默认 70
    strict: bool = False
    validate: bool = True

    PARAM_KEYS = {"node", "subreddit", "tag", "category", "language", "since", "url"}
    i = 0
    while i < len(tokens):
        t = tokens[i]
        t_lower = t.lower()

        if t.isdigit():
            # v1.1: 数字可能是 dedup 阈值（紧跟在 dedup 后面）
            if i > 0 and tokens[i-1].lower() == "dedup":
                dedup = int(t); i += 1; continue
            limit = int(t); i += 1; continue

        if t_lower == "json":
            output = "json"; i += 1; continue

        if t_lower == "noenrich":
            enrich = False; i += 1; continue
        if t_lower == "no" and i + 1 < len(tokens) and tokens[i + 1].lower() == "enrich":
            enrich = False; i += 2; continue

        if t_lower == "keyword" or t_lower.startswith("keyword="):
            keyword = t.split("=", 1)[1] if "=" in t else (tokens[i + 1] if i + 1 < len(tokens) else "")
            i += 2 if "=" not in t else 1; continue

        if t_lower == "has":
            i += 1; continue

        if "=" in t:
            k, v = t.split("=", 1)
            extra[k.lower()] = v; i += 1; continue

        if t_lower in PARAM_KEYS:
            extra[t_lower] = tokens[i + 1] if i + 1 < len(tokens) else ""
            i += 2; continue

        # 未知 alpha token → 当作 keyword（排除已知的）
        if t and t[0].isalpha():
            if (keyword is None
                    and t_lower not in ALL_SOURCES
                    and t_lower not in CONNECTORS | FIXED_TOKENS):
                keyword = t
                i += 1; continue

        # v1.1: strict / novalidate 关键字
        if t_lower == "strict":
            strict = True; i += 1; continue
        if t_lower == "novalidate" or t_lower == "no-validate":
            validate = False; i += 1; continue
        # v1.1: dedup 单独出现（无值，标志位）
        if t_lower == "dedup":
            i += 1; continue  # 数字紧跟在下一轮处理

        i += 1

    return {
        "limit":    limit,
        "output":   output,
        "enrich":   enrich,
        "keyword":  keyword,
        "extra":    extra,
        "dedup":    dedup,        # v1.1
        "strict":   strict,       # v1.1
        "validate": validate,     # v1.1
    }


# ──────────────────────────────────────────────
# Exceptions
# ──────────────────────────────────────────────

class ParseError(Exception):
    pass


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def list_sources() -> str:
    lines = ["支持的源（可用 list <源名> 查看模块）："]
    for name, info in ALL_SOURCES.items():
        modules = info["modules"]
        params  = info["params"]
        mod_str = ", ".join(modules) if modules else "无固定模块（preset / URL）"
        par_str = f" | 参数：{', '.join(params)}" if params else ""
        lines.append(f"  {name}: {mod_str}{par_str}")
    return "\n".join(lines)


def list_source_modules(source: str) -> str:
    if source not in ALL_SOURCES:
        return f"未知源：{source}"
    modules = ALL_SOURCES[source]["modules"]
    if not modules:
        return f"{source} 无固定模块（preset / URL）"
    return f"{source} 模块：{', '.join(modules)}"