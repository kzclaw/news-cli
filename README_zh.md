# newscli

**一站式新闻聚合 CLI** — 一条命令拉取 9 大信息源。

```bash
newscli get hackernews topstories 5
newscli get github trending 10 language python
newscli get all 15 json
```

[!["Python 版本"](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://pypi.org/project/newscli-tool/)
[!["PyPI 版本"](https://img.shields.io/pypi/v/newscli-tool.svg)](https://pypi.org/project/newscli-tool/)
[!["许可证"](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 安装

```bash
# 从 TestPyPI 安装（全球可访问）
pip install --index-url https://test.pypi.org/simple/ newscli-tool

# 从 GitHub 安装（最新版）
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
| **自然语言 DSL** | `get`、`list`、`看`、`拉` — 无需记忆任何 flags |
| **URL 内容补全** | 自动对 `summary = null` 的条目并发拉取 og:description |
| **跨源去重** | Jaccard 相似度 70% 阈值，保留信息量更大的条目 |
| **JSON 输出** | `NewsItem v1.0` 标准化格式 — 始终 9 个字段，`null` = 源头就没有，不伪造 |

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

# 多源并行（AND）
newscli get hackernews topstories 5 and github trending 10 and reddit subreddit programming 5

# 全源
newscli get all 15 json

# JSON 输出（程序调用）
newscli get hackernews topstories 5 json
newscli get all 3 json noenrich

# 查看可用源 / 模块
newscli list
newscli list github
newscli list v2ex
```

### 经典 Flag 模式

```bash
python3 -m newscli --source hackernews:topstories --limit 5 --json
python3 -m newscli --source "hackernews:topstories&github:trending" --limit 5
```

---

## 数据源 & 模块速查

| 数据源 | 支持的模块 |
|--------|-----------|
| `hackernews` | `topstories` · `new` · `ask` · `show` · `jobs` |
| `github` | `trending` · `trending-weekly` · `trending-monthly` · `language` 参数 |
| `huggingface` | `daily` · `weekly` · `monthly` |
| `zaker` | `hot` · `news` · `search` · `category` 参数 |
| `v2ex` | `hot` · `latest` · `node:<名称>` |
| `reddit` | `subreddit:<名称>` · `popular` · `hot` |
| `devto` | `latest` · `top` · `tags:<标签>` |
| `lobsters` | `newest` · `hot` · `top` · `upcoming` |
| `rss` | `feed:<URL>` — 任意 RSS/Atom 订阅源 |

---

## 输出格式

每条结果遵循 `NewsItem v1.0` 规范 — 字段为 `null` 表示「源头根本不提供这个」，从不伪造：

| 字段 | 类型 | 说明 |
|------|------|------|
| `source` | `str` | 数据源名（如 `hackernews`） |
| `module` | `str` | 子模块（如 `topstories`） |
| `title` | `str` | 标题 |
| `url` | `str` | 原文链接 |
| `author` | `str\|null` | 作者 / 发布者 |
| `published_at` | `datetime\|null` | 发布时间 |
| `summary` | `str\|null` | 描述或 og:description |
| `score` | `int\|null` | 分数 / 点数（有则提供） |
| `comments` | `int\|null` | 评论数（有则提供） |

---

## 项目结构

```
newscli/
├── cli.py          # 双模式入口：flags + 自然语言 DSL
├── aggregator.py   # ThreadPoolExecutor 并发调度 + 去重
├── parser.py       # 自然语言 DSL 解析器（纯规则，无 AI）
├── enrich.py       # 并发 og:description 抓取
└── sources/
    ├── base.py     # NewsSource 抽象类 + NewsItem 格式定义
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

## 环境要求

- Python 3.10+
- `requests` · `beautifulsoup4` · `lxml`（随包自动安装）

---

## 许可证

MIT · [kzclaw/news-cli](https://github.com/kzclaw/news-cli)