# newscli

**Unified news aggregation CLI** — pull from 9 sources in one command. Now with cross-source deduplication and schema validation.

```bash
newscli get hackernews topstories 5
newscli get github trending 10 language python
newscli get all 15 json
```

[!["Build Status](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://pypi.org/project/newscli-tool/)
[!["PyPI Version](https://img.shields.io/pypi/v/newscli-tool.svg)](https://pypi.org/project/newscli-tool/)
![License](https://img.shields.io/badge/license-MIT-green.svg)

📄 [中文版](README_zh.md) · 📋 [NewsItem v1.1 Schema](docs/NewsItem-v1.1.md)

---

## What's new in v1.1.2

- **Multi-source separator fix** — `--source` now accepts both `,` and `&` as separators (was `&` only)
- `newscli --source "hackernews:topstories,github:trending"` now works as documented

---

## What's new in v1.1

- **Cross-source deduplication with adjustable threshold** — `--dedup 0-100` (default 70, 0=disabled)
- **NewsItem v1.1 schema validation** — auto-detects schema issues, populates `extra.heat_int` from string `heat`
- **`schema_validation` field in JSON output** — warnings instead of silent failures
- **Strict mode** — `--strict` to hard-fail on validation errors
- Backward compatible — v1.0 scripts using `newscli` keep working

---

## Install

```bash
# From PyPI (recommended)
pip install newscli-tool

# From TestPyPI (dev/beta versions)
pip install --index-url https://test.pypi.org/simple/ newscli-tool

# From GitHub (latest)
pip install git+https://github.com/kzclaw/news-cli.git

# One-liner install
curl -sSL https://raw.githubusercontent.com/kzclaw/news-cli/main/install.sh | bash
```

After install, `newscli` is available in your terminal globally.

---

## Features

| Feature | Details |
|---------|---------|
| **9 sources** | Hacker News · GitHub Trending · Hugging Face · ZAKER · V2EX · Reddit · DEV.to · Lobsters · RSS |
| **25+ modules** | Each source has multiple views — topstories, trending, ask, show, job, by language, by node, by subreddit… |
| **Cross-source dedup (v1.1)** | `--dedup 0-100` threshold, Jaccard similarity, keeps richer item |
| **Schema validation (v1.1)** | Heat parsing, URL cleanup, time checks — `schema_validation` field output |
| **Natural language DSL** | `get`, `list`, `看`, `拉` — no flags to remember |
| **URL enrichment** | Auto-fetches og:description for items with `summary = null` |
| **JSON output** | `NewsItem v1.1` schema — 9 fields, `null` means "source doesn't have it" |

---

## Usage

### Natural language mode

```
newscli get <source> <module> [limit] [json] [noenrich]
```

```bash
# Single source
newscli get hackernews topstories 5
newscli get github trending 10 language python
newscli get v2ex node python 10
newscli get reddit subreddit technology 10
newscli get huggingface daily 5

# Multi-source (use & between sources)
newscli get "hackernews:topstories&github:trending" 5

# All sources
newscli get all 15 json

# JSON output
newscli get hackernews topstories 5 json
newscli get all 3 json noenrich
```

### Flag mode (v1.1 推荐)

```bash
# Basic
newscli --source hackernews:topstories --limit 5 --json

# Multi-source with dedup
newscli --source all --limit 5 --dedup 80 --json

# Strict validation (hard-fail on schema issues)
newscli --source all --limit 5 --strict --json

# Disable validation
newscli --source hackernews:topstories --limit 5 --no-validate

# Disable URL enrichment
newscli --source hackernews:topstories --limit 5 --no-enrich
```

### Flag reference (v1.1)

| Flag | Default | Description |
|------|---------|-------------|
| `--source` | `all` | `source:module` pairs, comma-separated |
| `--limit, -n` | `10` | Max items per source |
| `--keyword, -k` | — | Filter by keyword (AND match) |
| `--params, -p` | — | JSON: `{"source": {"param": "value"}}` |
| `--json` | off | JSON output (machine-readable) |
| `--enrich, -e` | on | Auto-fetch og:description for null summaries |
| `--no-enrich` | — | Disable enrichment |
| `--dedup` | `70` | **v1.1**: cross-source dedup threshold (0-100, 0=disabled) |
| `--strict` | off | **v1.1**: hard-fail on schema validation errors |
| `--no-validate` | on | **v1.1**: disable schema validation (default: enabled) |
| `--modules` | — | List all available sources & modules |

---

## Source & Module Reference

| Source | Modules |
|--------|---------|
| `hackernews` | `topstories` · `newest` · `ask` · `show` · `jobs` |
| `github` | `trending` (language param) |
| `huggingface` | `daily` · `trending` |
| `zaker` | `hot` · `category` · `search` |
| `v2ex` | `hot` · `latest` · `node:<name>` |
| `reddit` | `popular` · `hot` · `r/<subreddit>` |
| `devto` | `trending` · `latest` (tag param) |
| `lobsters` | `hottest` · `newest` |
| `rss` | `<preset>` (12 built-in) or `rss --url <url>` |

---

## Output Schema (NewsItem v1.1)

Every item follows `NewsItem v1.1` — see [full schema doc](docs/NewsItem-v1.1.md). Null means "source doesn't provide this", never faked.

| Field | Type | Description |
|-------|------|-------------|
| `source` | `str` | Source name (e.g. `Hacker News`) |
| `module` | `str` | Sub-module (e.g. `topstories`) |
| `title` | `str` | Item title |
| `url` | `str` | Link to item |
| `time` | `str\|null` | Human-readable time (e.g. `'2h ago'`, `'2026-06-01T14:31:53Z'`) |
| `time_iso` | `str\|null` | **v1.1**: ISO 8601 UTC time (most sources: None currently) |
| `summary` | `str\|null` | Description or og:description |
| `heat` | `str\|null` | **v1.1**: human-readable heat (`'455 points'`) — see `extra.heat_int` for int |
| `author` | `str\|null` | Author / submitter |
| `extra` | `dict` | Source-specific (e.g. `extra.stars`, `extra.upvotes`, `extra.descendants`) |
| `schema_validation` (top-level) | `list[str]` | **v1.1**: warnings from schema validation |

**Best practice for callers**:
```python
# Heat: prefer int from extra, fallback to parsing heat string
heat_int = item.get("extra", {}).get("stars") or \
           item.get("extra", {}).get("upvotes") or \
           item.get("extra", {}).get("descendants") or 0

# Time: prefer ISO, fallback to human-readable
when = item.get("time_iso") or item.get("time") or "unknown"
```

---

## Architecture

```
newscli/
├── cli.py            # Dual-mode entry: flags + NL DSL
├── aggregator.py     # ThreadPoolExecutor dispatcher + dedup (v1.1 threshold)
├── parser.py         # NL DSL parser (no AI — pure rules)
├── enrich.py         # Concurrent og:description fetcher
├── validate.py       # v1.1: schema validation (heat, url, time)
└── sources/
    ├── base.py       # NewsSource ABC + NewsItem schema
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

## v1.0 → v1.1 Migration

v1.1 is **fully backward compatible** — all v1.0 commands work identically. New features:

- Dedup is now configurable (was hard-coded 70% in v1.0; default 70% in v1.1)
- JSON output now includes `schema_validation` field (v1.0 scripts ignore unknown fields)
- Heat field is now documented as `str` (was assumed int in v1.0 — use `extra.heat_int` for int)

---

## Requirements

- Python 3.10+
- `requests` · `beautifulsoup4` · `lxml` (auto-installed)

---

## License

MIT · [kzclaw/news-cli](https://github.com/kzclaw/news-cli)
