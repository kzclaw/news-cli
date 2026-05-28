#!/usr/bin/env python3
"""
cli.py — News CLI 入口

两种接口共存：
  1. flag 模式（--source / --limit / --json）— 机器友好
  2. 自然语言模式（get hackernews topstories 5 json）— 人类友好

用法（flag）：
    python cli.py --source hackernews:topstories --limit 5
    python cli.py --source all --json

用法（自然语言）：
    python cli.py get hackernews topstories
    python cli.py get hackernews topstories 5 json
    python cli.py get hackernews topstories 5 and github trending 10
    python cli.py get all 10 json noenrich
    python cli.py list
    python cli.py list hackernews
"""

import argparse
import json
import sys
from .aggregator import NewsAggregator
from .sources import REGISTRY, rss as rss_module
from .parser import parseNL, ParseError, list_sources, list_source_modules


# ─── 输出格式器 ─────────────────────────────────────────────────

def _render_text(items: list[dict]) -> str:
    """人类可读文本输出 — None 字段不显示"""
    if not items:
        return "📰 无内容"
    lines = [f"📰 共 {len(items)} 条"]
    lines.append("─" * 50)
    for i, item in enumerate(items, 1):
        # source + module badge
        module = item.get("module") or ""
        source = item.get("source") or "?"
        badge = f"[{source}]" if not module else f"[{source}/{module}]"
        heat = item.get("heat") or ""
        time = item.get("time") or ""
        meta = " | ".join(x for x in [heat, time] if x)
        lines.append(f"\n[{i}] {badge} {meta}")
        lines.append(f"    {item.get('title', '')}")
        url = item.get("url")
        if url:
            lines.append(f"    🔗 {url}")
        summary = item.get("summary")
        if summary:
            lines.append(f"    📝 {summary[:150]}{'...' if len(summary) > 150 else ''}")
        author = item.get("author")
        if author:
            lines.append(f"    👤 {author}")
    return "\n".join(lines)


def _json_output(result: dict) -> str:
    """JSON 输出 — 完整 schema，包含 None"""
    return json.dumps(result, indent=2, ensure_ascii=False)


# ─── CLI 参数解析 ───────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="news",
        description="模块化新闻聚合 CLI — 支持 HN/GitHub/HuggingFace/ZAKER/V2EX/Reddit/RSS",
    )
    p.add_argument(
        "--source", "-s", default="all",
        help="source:module 格式，逗号分隔多源\n"
             "  hackernews:topstories|newest|ask|show|jobs\n"
             "  github:trending\n"
             "  huggingface:daily|trending\n"
             "  zaker:hot|category|search\n"
             "  v2ex:hot|latest|node:<name>\n"
             "  reddit:popular|hot|r/<subreddit>\n"
             "  rss:<preset>|custom\n"
             "  all = 所有注册 source（不含 rss）"
    )
    p.add_argument("--limit", "-n", type=int, default=10, help="每 source 最大条数")
    p.add_argument(
        "--keyword", "-k", default=None,
        help="关键词过滤（逗号分隔多词，AND 匹配）"
    )
    p.add_argument(
        "--params", "-p", default=None,
        help="source-specific 参数，JSON 格式\n"
             '  如: {"zaker": {"category": "technology"}, "github": {"language": "Python"}}'
    )
    p.add_argument("--json", action="store_true", help="JSON 输出（供 agent 解析）")
    p.add_argument(
        "--enrich", "-e", action="store_true", default=True,
        help="对 summary=null 的 item 并发拉取原文 og:description（curl，8s 超时，默认开启）"
    )
    p.add_argument(
        "--no-enrich", dest="enrich", action="store_false",
        help="禁用 --enrich，不拉取原文摘要"
    )
    p.add_argument(
        "--modules", action="store_true",
        help="列出所有 source 的可用 module"
    )
    return p


def _parse_params(params_str: str | None) -> dict:
    """解析 --params JSON 字符串"""
    if not params_str:
        return {}
    try:
        return json.loads(params_str)
    except Exception:
        return {}


# ─── 主入口 ─────────────────────────────────────────────────────

def main() -> None:
    # ── 自然语言模式检测 ──
    # 如果没有任何 flag，且 positional args 以 list/get/fetch/看/拉/找 开头，走 NL parser
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        raw = " ".join(sys.argv[1:])
        try:
            result = _run_nl(raw)
            sys.exit(0 if result["ok"] else 1)
        except ParseError as e:
            print(f"❗ 语法错误：{e}")
            print(f"提示：get hackernews topstories 5  /  list hackernews")
            sys.exit(1)
        except Exception as e:
            print(f"❗ 执行出错：{e}")
            sys.exit(1)

    # ── Flag 模式（原有行为）──
    parser = _build_parser()
    args = parser.parse_args()

    if args.modules:
        _print_modules()
        return

    source_filter = None
    if args.source != "all":
        source_filter = args.source

    params = _parse_params(args.params)
    agg = NewsAggregator(limit_per_source=args.limit)
    result = agg.fetch(
        source_filter=source_filter,
        limit=None,
        keyword=args.keyword,
        params=params,
        enrich=args.enrich,
    )

    if args.json:
        print(_json_output(result))
    else:
        print(_render_text(result["items"]))
        if result["errors"]:
            print(f"\n⚠️ {len(result['errors'])} 个 source 出错：")
            for e in result["errors"]:
                print(f"  - {e}")


def _run_nl(raw: str) -> dict:
    """运行自然语言命令。"""
    result = parseNL(raw)

    if result.command == "list":
        if result.list_target == "sources":
            print(list_sources())
        elif result.list_target == "modules":
            # 列出所有源的所有模块
            for src in REGISTRY.keys():
                print(list_source_modules(src))
                print()
        else:
            print(list_source_modules(result.list_target))
        return {"ok": True, "items": []}

    # ── fetch 模式 ──
    f = result.fetch
    source_filter = f["source_filter"] if f["source_filter"] != "all" else None

    agg = NewsAggregator(limit_per_source=f["limit"])
    agg_result = agg.fetch(
        source_filter=source_filter,
        limit=None,
        keyword=f["keyword"],
        params=f["params"],
        enrich=f["enrich"],
    )

    if f["output"] == "json":
        print(_json_output(agg_result))
    else:
        print(_render_text(agg_result["items"]))
        if agg_result["errors"]:
            print(f"\n⚠️ {len(agg_result['errors'])} 个 source 出错：")
            for e in agg_result["errors"]:
                print(f"  - {e}")

    return agg_result


def _print_modules() -> None:
    """打印所有 source 及其支持的 module"""
    all_sources = dict(REGISTRY)
    all_sources["rss"] = rss_module.RSSSource

    print(f"{'Source':<15} {'Display Name':<25} {'Modules'}")
    print("─" * 80)

    # RSS presets
    for key, info in sorted(rss_module.PRESET_SOURCES.items()):
        print(f"{'rss:'+key:<15} {info['name']:<25} (RSS preset)")

    print()
    for name, cls in sorted(all_sources.items()):
        if name == "rss":
            continue
        modules = ", ".join(cls.modules) if cls.modules else "(all)"
        print(f"{name:<15} {cls.display_name:<25} {modules}")


if __name__ == "__main__":
    main()