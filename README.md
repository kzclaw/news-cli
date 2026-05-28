# newscli

**Unified news aggregation CLI** — pull from 9 sources in one command.

```bash
newscli get hackernews topstories 5
newscli get github trending 10 language python
newscli get all 15 json
```

[!["Build Status"](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://pypi.org/project/newscli-tool/)
[!["PyPI Version"](https://img.shields.io/pypi/v/newscli-tool.svg)](https://pypi.org/project/newscli-tool/)
[!["License"](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

📄 [中文版](README_zh.md)

---

## Install

```bash
# From PyPI (global, any machine)
pip install newscli-tool

# From TestPyPI (dev/beta versions)
pip install --index-url https://test.pypi.org/simple/ newscli-tool

# From GitHub (latest dev branch)
pip install git+https://github.com/kzclaw/news-cli.git

# One-liner (any machine with curl + python3)
curl -sSL https://raw.githubusercontent.com/kzclaw/news-cli/main/install.sh | bash
```

After install, `newscli` is available in your terminal globally.

---

## Features

| Feature | Details |
|---------|---------|
| **9 sources** | Hacker News · GitHub Trending · Hugging Face · ZAKER · V2EX · Reddit · DEV.to · Lobsters · RSS |
| **25+ modules** | Each source has multiple views — topstories, trending, ask, show, job, by language, by node, by subreddit… |
| **Natural language DSL** | `get`, `list`, `看`, `拉` — no flags to remember |
| **URL enrichment** | Auto-fetches og:description for every item with `summary = null` |
| **Deduplication** | Cross-source Jaccard similarity, 70% threshold, keeps richer item |
| **JSON output** | `NewsItem v1.0` schema — always 9 fields, `null` means "source doesn't have it" |

---

## Usage

### Natural language mode

```
newscli get <source> <module> [limit] [json] [noenrich]
```

**Examples**

```bash
# Single source
newscli get hackernews topstories 5
newscli get github trending 10 language python
newscli get v2ex node python 10
newscli get reddit subreddit technology 10
newscli get huggingface daily 5

# Multi-source (AND)
newscli get hackernews topstories 5 and github trending 10 and reddit subreddit programming 5

# All sources
newscli get all 15 json

# JSON output (machine-readable)
newscli get hackernews topstories 5 json
newscli get all 3 json noenrich

# List available sources / modules
newscli list
newscli list github
newscli list v2ex
```

### Flag mode

```bash
python3 -m newscli --source hackernews:topstories --limit 5 --json
python3 -m newscli --source "hackernews:topstories&github:trending" --limit 5
```

---

## Source & Module Reference

| Source | Modules |
|--------|---------|
| `hackernews` | `topstories` · `new` · `ask` · `show` · `jobs` |
| `github` | `trending` · `trending-weekly` · `trending-monthly` · language parameter |
| `huggingface` | `daily` · `weekly` · `monthly` |
| `zaker` | `hot` · `news` · `search` · category parameter |
| `v2ex` | `hot` · `latest` · `node:<name>` |
| `reddit` | `subreddit:<name>` · `popular` · `hot` |
| `devto` | `latest` · `top` · `tags:<tag>` |
| `lobsters` | `newest` · `hot` · `top` · `upcoming` |
| `rss` | `feed:<url>` — any RSS/Atom feed by URL |

---

## Output Schema

Every item follows `NewsItem v1.0` — null means "source doesn't provide this", never faked:

| Field | Type | Description |
|-------|------|-------------|
| `source` | `str` | Source name (e.g. `hackernews`) |
| `module` | `str` | Sub-module (e.g. `topstories`) |
| `title` | `str` | Item title |
| `url` | `str` | Link to item |
| `author` | `str\|null` | Author / submitter |
| `published_at` | `datetime\|null` | Publication time |
| `summary` | `str\|null` | Description or og:description |
| `score` | `int\|null` | Score / points (if available) |
| `comments` | `int\|null` | Comment count (if available) |

---

## Architecture

```
newscli/
├── cli.py          # Dual-mode entry: flags + NL DSL
├── aggregator.py   # ThreadPoolExecutor dispatcher + deduplication
├── parser.py       # NL DSL parser (no AI — pure rules)
├── enrich.py       # Concurrent og:description fetcher
└── sources/
    ├── base.py     # NewsSource ABC + NewsItem schema
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

## Requirements

- Python 3.10+
- `requests` · `beautifulsoup4` · `lxml` (installed automatically)

---

## License

MIT · [kzclaw/news-cli](https://github.com/kzclaw/news-cli)