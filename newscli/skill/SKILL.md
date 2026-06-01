---
skill_version: "1.1.1"
schema: "NewsItem v1.1"
last_updated: "2026-06-02"
---

# News CLI — 模块化新闻源聚合工具 v1.1.1

> Skill for the 戴大虾 AI assistant. Provides a unified CLI for fetching news from 9 sources with **cross-source deduplication** and **schema validation** (v1.1).

## v1.1 新增能力

- **跨源去重（`--dedup N`）** — 阈值 0-100，默认 70，0=禁用
- **Schema 验证** — heat 解析填入 `extra.heat_int`、url 空字符串改 None、time 检查
- **`schema_validation` 字段** — JSON 输出多 1 字段，警告替代静默失败
- **严格模式（`--strict`）** — 验证失败时 hard fail
- **完全向后兼容** — v1.0 脚本迁移无需改代码

## Output Schema（NewsItem v1.1 — 必看！）

每条结果都遵循 NewsItem v1.1 规范。`null` 表示「源头不提供」，**绝不伪造**：

```json
{
  "source": "Hacker News",          // 来源显示名（大写或品牌名）
  "module": "topstories",            // 子模块
  "title": "...",                   // 标题（必填）
  "url": "https://...",            // 原文链接；空字符串="" 应视为 null
  "time": "33m ago",               // 人类可读时间（**v1.0/v1.1 都可能是相对时间**）
  "time_iso": null,                // **v1.1 新约定字段**：ISO 8601 UTC；当前多数源为 None
  "summary": "...",                // 描述（enrich 后填入）
  "heat": "129 points",            // **v1.1 实际是字符串**（不是 int！）
  "author": "username",            // 作者
  "extra": {                        // v1.1 数字常在 extra
    "hn_id": 48358646,
    "hn_url": "...",
    "descendants": 20,             // HN 评论数（int）
    "stars": 10748,                 // GitHub stars（int）
    "upvotes": 23,                  // HF upvotes / Lobsters 投票（int）
    "heat_int": 129                 // **v1.1 自动填入** = heat 解析后的 int
  }
}
```

**顶层还有 1 个 v1.1 字段**：
```json
{
  "schema_validation": [             // v1.1 警告列表
    "github:trending item 0: heat parse failed, used extra.stars=10748"
  ]
}
```

## 调用方最佳实践（v1.1 必看）

```python
import json, subprocess

# 推荐：用 --json + --dedup 70 拿干净数据
r = subprocess.run(["newscli", "--source", "all", "--limit", "10", "--dedup", "70", "--json"],
                   capture_output=True, text=True)
data = json.loads(r.stdout)

# 1. 拿热度数字（**用 extra.heat_int，不要 parse heat 字符串**）
for item in data["items"]:
    heat_int = (
        item.get("extra", {}).get("heat_int") or
        item.get("extra", {}).get("stars") or
        item.get("extra", {}).get("upvotes") or
        item.get("extra", {}).get("descendants") or
        0
    )
    print(f"  {heat_int} ⭐ {item['title'][:60]}")

# 2. 拿时间（优先 ISO，回退人类可读）
for item in data["items"]:
    when = item.get("time_iso") or item.get("time") or "时间未知"
    print(f"  [{when}] {item['title'][:60]}")

# 3. URL 检查
for item in data["items"]:
    url = item.get("url")
    if not url or url == "":
        print(f"  ⚠️ {item['title'][:40]} no URL")
```

## CLI Flag 速查（v1.1）

| Flag | 默认 | 说明 |
|------|------|------|
| `--source` | `all` | `source:module` 配对，逗号分隔 |
| `--limit, -n` | `10` | 每源最大条数 |
| `--keyword, -k` | — | 按关键词过滤（AND 匹配） |
| `--params, -p` | — | JSON: `{"source": {"param": "value"}}` |
| `--json` | 关 | JSON 输出（程序友好） |
| `--enrich, -e` | 开 | 自动为 null summary 拉 og:description |
| `--no-enrich` | — | 禁用内容补全 |
| `--dedup` | `70` | **v1.1**：跨源去重阈值（0-100，0=禁用） |
| `--strict` | 关 | **v1.1**：验证失败时 hard fail |
| `--no-validate` | 开 | **v1.1**：禁用 schema 验证 |
| `--modules` | — | 列出所有可用源 / 模块 |

## 自然语言 DSL（v1.1 也支持！）

```bash
# v1.1 NL 用法：get + limit + dedup + strict + json
newscli get all 10 dedup 80 strict json
newscli get hackernews topstories 5 dedup 50 json
newscli get github trending 10 dedup 70 json
newscli get "hackernews:topstories&github:trending" 5 dedup 80 json
```

v1.1 NL 关键字：`dedup` / `strict` / `novalidate`（`--no-validate` 的简写）

## 数据源 & 模块

| Source | Modules |
|--------|---------|
| `hackernews` | `topstories` · `newest` · `ask` · `show` · `jobs` |
| `github` | `trending`（language 参数） |
| `huggingface` | `daily` · `trending` |
| `zaker` | `hot` · `category` · `search` |
| `v2ex` | `hot` · `latest` · `node:<name>` |
| `reddit` | `popular` · `hot` · `r/<subreddit>` |
| `devto` | `trending` · `latest`（tag 参数） |
| `lobsters` | `hottest` · `newest` |
| `rss` | 12 内置 preset 或 `rss --url <url>` |

## Install

```bash
# CLI 装
pip install newscli-tool

# 这个 skill 自动检测（如果未装）— v1.1 新增
newscli get all 3 dedup 70 json
# 首次跑会提示是否装 skill

# 显式装
newscli-skill-install
```

## Architecture

```
newscli/
├── cli.py            # Dual-mode: flags + NL DSL
├── aggregator.py     # ThreadPoolExecutor + dedup (v1.1)
├── parser.py         # NL DSL parser (v1.1: dedup/strict tokens)
├── enrich.py         # Concurrent og:description fetcher
├── validate.py       # v1.1: schema validation
├── newscli_skill.py  # v1.1: OpenClaw skill install/update/check
└── sources/
    ├── base.py
    ├── hackernews.py
    ├── github.py
    ├── huggingface.py
    ├── zaker.py
    ├── v2ex.py
    ├── reddit.py
    ├── devto.py
    ├── lobsters.py
    └── rss.py
```

---

*Schema doc created 2026-06-02 for newscli v1.1.1 — by 戴大虾🍤*
*Full schema reference: [NewsItem-v1.1.md](https://github.com/kzclaw/news-cli/blob/main/newscli/skill/SKILL.md)*
