"""
aggregator.py — News Aggregator

统一调度多个 source，支持：
- 多 source 并行拉取（ThreadPoolExecutor）
- 每个 source 的 module 子模块指定
- source-specific 额外参数（category, language, node, subreddit 等）
- 统一 JSON 输出（完整 schema）
"""

import concurrent.futures
from dataclasses import asdict
from typing import Optional
from newscli.sources import REGISTRY, NewsItem, SourceError, rss as rss_module


class NewsAggregator:
    """多 source 统一聚合器"""

    def __init__(
        self,
        sources: list[str] | None = None,
        limit_per_source: int = 10,
    ):
        """
        Args:
            sources         : source 名称列表（如 ["hackernews", "github"]）
                              None = 所有注册 source（不含 rss）
            limit_per_source: 每个 source 最大拉取条数
        """
        self.sources = sources or list(REGISTRY.keys())
        self.limit_per_source = limit_per_source

    def fetch(
        self,
        source_filter: str | None = None,
        limit: int | None = None,
        keyword: str | None = None,
        params: dict | None = None,
        enrich: bool = True,  # 默认对 summary=null 的 item 拉取原文摘要
        dedup_threshold: int = 70,  # v1.1: 跨源去重阈值（0=禁用, 70=默认, 100=精确匹配）
        validate: bool = True,  # v1.1: heat/url/time 验证（默认开）
        strict: bool = False,  # v1.1: 严格模式，验证失败 hard fail
    ) -> dict:
        """
        并行拉取所有 source，返回统一格式。

        Args:
            source_filter : 逗号分隔的 source:module 对列表
                           如 "hackernews:topstories,github:trending,v2ex:latest"
            limit         : 全局返回上限（None = 所有）
            keyword       : 关键词过滤（所有 source 生效）
            params        : source-specific 参数 dict
                           格式：{"<source>": {"module": "...", "category": "..."}}

        Returns:
            {"ok": bool, "schema": str, "sources": {}, "items": [], "total": int, "errors": []}
            items 每项 = NewsItem.to_dict()，即所有字段（含 None）
        """
        parsed = self._parse_filter(source_filter)
        params = params or {}

        # results key = source:module（如 "hackernews:topstories"）
        results: dict[str, list[dict]] = {}
        errors: list[str] = []

        def _fetch_one(name: str, module: str | None, extra: dict):
            """执行单次 fetch，返回 (key, items_list, errors_list)"""
            # 唯一 key：不同 module 的同一 source 不会互相覆盖
            key = f"{name}:{module}" if module else name

            # RSS 特殊处理（不注册到 REGISTRY）
            if name == "rss":
                src = rss_module.RSSSource(
                    source_key=extra.get("source_key"),
                    feed_url=extra.get("url"),
                )
            else:
                src_cls = REGISTRY.get(name)
                if not src_cls:
                    return key, [], [f"Unknown source: {name}"]
                src = src_cls()

            # global keyword filter applied at source.fetch() call
            fetch_kwargs = {
                "module": module,
                "limit": self.limit_per_source,
                "keyword": keyword,   # may be None = no filtering
            }
            # per-source params override (from merged extra)
            for k in ("category", "language", "node", "subreddit",
                      "start_time", "end_time", "url"):
                if k in extra:
                    fetch_kwargs[k] = extra[k]
            # per-source keyword (params level) takes precedence over global
            if "keyword" in extra:
                fetch_kwargs["keyword"] = extra["keyword"]

            try:
                items = src.fetch(**fetch_kwargs)
                return key, [item.to_dict() for item in items], []
            except SourceError as e:
                return key, [], [str(e)]
            except Exception as e:
                return key, [], [f"{name} unexpected error: {e}"]

        # 构建 work items
        work: list[tuple] = []
        if parsed:
            for name, module, extra in parsed:
                # CLI params 覆盖 hard-coded extra
                sp = params.get(name, {})
                merged_extra = {**extra, **sp}
                work.append((name, module, merged_extra))
        else:
            for name in self.sources:
                sp = params.get(name, {})
                work.append((name, None, sp))

        # 并行执行
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(work), 8)) as ex:
            futures = {ex.submit(_fetch_one, *w): w for w in work}
            for fut in concurrent.futures.as_completed(futures):
                key, items, errs = fut.result()
                if items:
                    results[key] = items
                errors.extend(errs)

        # 合并所有 items（按 source:module 分别存储，输出时全部扁平化）
        all_items: list[dict] = []
        for key, items in results.items():
            all_items.extend(items)

        # v1.1: 跨 source 去重（阈值可调，0=禁用）
        schema_validation: list[str] = []
        if dedup_threshold > 0 and len(results) > 1:
            all_items = self._deduplicate(all_items, threshold=dedup_threshold)

        # v1.1: heat/url/time 验证
        if validate:
            from .validate import validate_items
            all_items, schema_validation = validate_items(all_items, strict=strict)

        # 可选：enrich — 对 summary=null 的 item 并发拉取原文 description
        if enrich:
            from .enrich import enrich_items
            all_items = enrich_items(all_items)

        if limit is not None:
            all_items = all_items[:limit]

        return {
            "ok": True,
            "schema": "NewsItem v1.1",
            "sources": {k: len(v) for k, v in results.items()},
            "items": all_items,
            "total": len(all_items),
            "errors": errors,
            "schema_validation": schema_validation,  # v1.1
        }

    @staticmethod
    def _deduplicate(items: list[dict], threshold: int = 70) -> list[dict]:
        """
        跨 source 去重。相似度阈值可调（默认 70%，0=禁用）。
        保留第一条出现的item，移除后续相似项（合并更丰富字段的版本）。

        v1.1 升级：
        - threshold 改成参数（不再硬编码 70%）
        - 类似度算法仍用 Jaccard（比 SequenceMatcher 简单，无新依赖）
        """
        if threshold <= 0:
            return items
        from urllib.parse import urlparse
        def normalize_title(t: str) -> str:
            """小写 + 去除标点 + strip()"""
            import re
            t = t.lower().strip()
            t = re.sub(r'[^\w\s]', ' ', t)
            t = re.sub(r'\s+', ' ', t).strip()
            return t

        def similarity(a: str, b: str) -> float:
            """简单词集合 Jaccard 相似度"""
            sa = set(a.split())
            sb = set(b.split())
            if not sa or not sb:
                return 0.0
            inter = len(sa & sb)
            union = len(sa | sb)
            return inter / union if union > 0 else 0.0

        def item_key(item: dict) -> str:
            domain = ""
            if item.get("url"):
                try:
                    domain = urlparse(item["url"]).netloc
                except Exception:
                    pass
            return f"{normalize_title(item['title'])}|{domain}"

        seen: list[dict] = []
        for item in items:
            norm = normalize_title(item.get("title", ""))
            if not norm:
                seen.append(item)
                continue
            dup_idx = None
            for i, s in enumerate(seen):
                s_norm = normalize_title(s.get("title", ""))
                # Different domain → different article, skip
                s_domain = urlparse(s.get("url", "")).netloc or ""
                item_domain = urlparse(item.get("url", "")).netloc or ""
                if s_domain and item_domain and s_domain != item_domain:
                    continue
                if similarity(norm, s_norm) >= threshold / 100.0:
                    dup_idx = i
                    break
            if dup_idx is not None:
                # 保留信息更丰富的那个（非 null 字段数量多的）
                existing = seen[dup_idx]
                existing_nulls = sum(1 for k, v in existing.items() if v is None and k != 'extra')
                item_nulls = sum(1 for k, v in item.items() if v is None and k != 'extra')
                if item_nulls < existing_nulls:
                    seen[dup_idx] = item
            else:
                seen.append(item)
        return seen

    @staticmethod
    def _parse_filter(filter_str: str | None) -> list[tuple]:
        """
        解析 'source:module,source2:module2' → [(name, module, extra_dict), ...]

        支持格式：
          hackernews:topstories        → ("hackernews", "topstories", {})
          v2ex:node:python             → ("v2ex", "node", {"node": "python"})
          rss:bensbites                → ("rss", "bensbites", {"source_key": "bensbites"})
          github:trending:language=Python → ("github", "trending", {"language": "Python"})
          zaker:category:category=technology → ("zaker", "category", {"category": "technology"})
          reddit:r/technology          → ("reddit", None, {"subreddit": "technology"})
        """
        if not filter_str:
            return []
        items = []
        for part in filter_str.split("&"):
            part = part.strip()
            if not part:
                continue
            name, rest = part.split(":", 1) if ":" in part else (part, "")
            name = name.strip()

            extra = {}
            tokens = rest.split(":") if rest else []
            module = None
            for token in tokens:
                if "=" in token:
                    k, v = token.split("=", 1)
                    extra[k.strip()] = v.strip()
                elif not module:
                    module = token

            # Reddit r/<subreddit> shorthand
            if name == "reddit" and module and module.startswith("r/"):
                extra["subreddit"] = module[2:]
                module = None

            # RSS source_key shorthand
            if name == "rss" and module and "=" not in module:
                extra["source_key"] = module

            items.append((name, module, extra))
        return items


def fetch_all(keyword: str | None = None, limit: int | None = None) -> dict:
    """快速入口：拉取所有注册 source"""
    agg = NewsAggregator()
    return agg.fetch(keyword=keyword, limit=limit)