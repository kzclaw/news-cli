# newscli

**一站式新闻聚合 CLI** — 一条命令拉取 9 大信息源。v1.1 新增跨源去重 + schema 验证。

```bash
newscli get hackernews topstories 5
newscli get github trending 10 language python
newscli get all 15 json
```

[!["Python 版本](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://pypi.org/project/newscli-tool/)
[!["PyPI 版本](https://img.shields.io/pypi/v/newscli-tool.svg)](https://pypi.org/project/newscli-tool/)
!["许可证](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

📄 [English version](README.md) · 📋 [NewsItem v1.1 Schema](docs/NewsItem-v1.1.md)

---

## v1.1.2 新特性

- **多源分隔符修复** — `--source` 现在同时支持 `,` 和 `&` 作为分隔符（之前只支持 `&`）
- `newscli --source "hackernews:topstories,github:trending"` 现在按文档正常工作

---

## v1.1 新特性

- **跨源去重（阈值可调）** — `--dedup 0-100`（默认 70，0=禁用）
- **NewsItem v1.1 schema 验证** — 自动检测 schema 问题，从字符串 `heat` 提取 `extra.heat_int`
- **`schema_validation` 字段** — JSON 输出多 1 个字段，警告替代静默失败
- **严格模式** — `--strict` 验证失败时 hard fail
- **完全向后兼容** — v1.0 脚本直接迁移无需改代码

---

## 安装

```bash
# 从 PyPI 安装（推荐）
pip install newscli-tool

# 从 TestPyPI 安装（开发版 / 测试版）
pip install --index-url https://test.pypi.org/simple/ newscli-tool

# 从 GitHub 安装（最新开发版）
pip install git+https://github.com/kzclaw/news-cli.git

# 一键安装脚本（任意机器，curl + python3 即可）
curl -sSL https://raw.githubusercontent.com/kzclaw/news-cli/main/install.sh | bash
```

安装完成后，`newscli` 在终端全局可用。

---

## 核心特性

| 特性 | 说明 |
|------|------|
| **9 个数据源** | Hacker News · GitHub Trending · Hugging Face · ZAKER · V2EX · Reddit · DEV.to · Lobsters · RSS |
| **25+ 子模块** | 每个源都有多种视图 — topstories / trending / ask / show / jobs / 按语言 / 按节点 / 按子版块… |
| **跨源去重（v1.1）** | `--dedup 0-100` 阈值，Jaccard 相似度，保留信息量更大的条目 |
| **Schema 验证（v1.1）** | heat 解析、URL 清理、时间检查 — 输出 `schema_validation` 字段 |
| **自然语言 DSL** | `get`、`list`、`看`、`拉` — 无需记忆任何 flags |
| **URL 内容补全** | 自动对 `summary = null` 的条目并发拉取 og:description |
| **JSON 输出** | `NewsItem v1.1` 标准化格式 — 始终 9 个字段，`null` = 源头就没有，不伪造 |

---

## 使用方式

### 自然语言模式

```
newscli get <源> <模块> [数量] [json] [noenrich]
```

**示例**

```bash
# 单源
newscli get hackernews topstories 5
newscli get github trending 10 language python
newscli get v2ex node python 10
newscli get reddit subreddit technology 10
newscli get huggingface daily 5

# 多源（用 & 分隔）
newscli get "hackernews:topstories&github:trending" 5

# 全源
newscli get all 15 json

# JSON 输出
newscli get hackernews topstories 5 json
newscli get all 3 json noenrich
```

### 经典 Flag 模式（v1.1 推荐）

```bash
# 基础
newscli --source hackernews:topstories --limit 5 --json

# 多源 + 跨源去重
newscli --source all --limit 5 --dedup 80 --json

# 严格模式（验证失败 hard fail）
newscli --source all --limit 5 --strict --json

# 禁用 schema 验证
newscli --source hackernews:topstories --limit 5 --no-validate

# 禁用 URL 内容补全
newscli --source hackernews:topstories --limit 5 --no-enrich
```

### Flag 速查（v1.1）

| Flag | 默认 | 说明 |
|------|------|------|
| `--source` | `all` | `source:module` 配对，逗号分隔 |
| `--limit, -n` | `10` | 每源最大条数 |
| `--keyword, -k` | — | 按关键词过滤（AND 匹配） |
| `--params, -p` | — | JSON 格式：`{"source": {"param": "value"}}` |
| `--json` | 关 | JSON 输出（程序友好） |
| `--enrich, -e` | 开 | 自动为 null summary 拉 og:description |
| `--no-enrich` | — | 禁用内容补全 |
| `--dedup` | `70` | **v1.1**：跨源去重阈值（0-100，0=禁用） |
| `--strict` | 关 | **v1.1**：验证失败时 hard fail |
| `--no-validate` | 开 | **v1.1**：禁用 schema 验证（默认开） |
| `--modules` | — | 列出所有可用源 / 模块 |

---

## 数据源 & 模块速查

| 数据源 | 支持的模块 |
|--------|-----------|
| `hackernews` | `topstories` · `newest` · `ask` · `show` · `jobs` |
| `github` | `trending`（language 参数） |
| `huggingface` | `daily` · `trending` |
| `zaker` | `hot` · `category` · `search` |
| `v2ex` | `hot` · `latest` · `node:<名称>` |
| `reddit` | `popular` · `hot` · `r/<子版块>` |
| `devto` | `trending` · `latest`（tag 参数） |
| `lobsters` | `hottest` · `newest` |
| `rss` | `<preset>`（12 个内置 preset）或 `rss --url <URL>` |

---

## 输出格式（NewsItem v1.1）

每条结果遵循 `NewsItem v1.1` 规范，详见 [完整 schema 文档](docs/NewsItem-v1.1.md)。`null` 表示「源头根本不提供」，从不伪造。

| 字段 | 类型 | 说明 |
|------|------|------|
| `source` | `str` | 数据源名（如 `Hacker News`） |
| `module` | `str` | 子模块（如 `topstories`） |
| `title` | `str` | 标题 |
| `url` | `str` | 原文链接 |
| `time` | `str\|null` | 人类可读时间（如 `'2h ago'`、`'2026-06-01T14:31:53Z'`） |
| `time_iso` | `str\|null` | **v1.1**：ISO 8601 UTC 时间（目前大部分源为 None） |
| `summary` | `str\|null` | 描述或 og:description |
| `heat` | `str\|null` | **v1.1**：人类可读热度（如 `'455 points'`）— 数字用 `extra.heat_int` |
| `author` | `str\|null` | 作者 / 发布者 |
| `extra` | `dict` | 源特有字段（如 `extra.stars`、`extra.upvotes`、`extra.descendants`） |
| `schema_validation`（顶层） | `list[str]` | **v1.1**：schema 验证的警告列表 |

**调用方最佳实践**：
```python
# 热度：优先用 extra 里的 int，回退到解析 heat 字符串
heat_int = item.get("extra", {}).get("stars") or \
           item.get("extra", {}).get("upvotes") or \
           item.get("extra", {}).get("descendants") or 0

# 时间：优先用 ISO，回退到人类可读
when = item.get("time_iso") or item.get("time") or "未知时间"
```

---

## 项目结构

```
newscli/
├── cli.py            # 双模式入口：flags + 自然语言 DSL
├── aggregator.py     # ThreadPoolExecutor 调度 + 去重（v1.1 阈值）
├── parser.py         # 自然语言 DSL 解析器（纯规则，无 AI）
├── enrich.py         # 并发 og:description 抓取
├── validate.py       # v1.1：schema 验证（heat、url、time）
└── sources/
    ├── base.py       # NewsSource 抽象类 + NewsItem 格式定义
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

## v1.0 → v1.1 迁移指南

v1.1 **完全向后兼容** — 所有 v1.0 命令行为完全相同。新功能：

- 去重阈值可调（v1.0 硬编码 70%，v1.1 默认 70% 但可调）
- JSON 输出新增 `schema_validation` 字段（v1.0 脚本忽略未知字段）
- heat 字段文档化为 `str`（v1.0 假设是 int — 现在用 `extra.heat_int` 拿数字）

---

## 环境要求

- Python 3.10+
- `requests` · `beautifulsoup4` · `lxml`（随包自动安装）

---

## 许可证

MIT · [kzclaw/news-cli](https://github.com/kzclaw/news-cli)
