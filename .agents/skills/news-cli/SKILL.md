---
name: news-cli
description: "Unified news aggregation CLI — 9 sources, 25+ modules, JSON/programmatic output. Run newscli directly in exec."
metadata: { "openclaw": { "emoji": "📰" } }
---

# news-cli

Unified news aggregation CLI tool. Fetch news from 9 sources across 25+ modules with a single command.

## Source

- GitHub: `https://github.com/kzclaw/news-cli`
- PyPI: `pip install --user newscli-tool`（v1.1.2+ via OIDC trusted publishing）
- Install from source: `pip install --user -e git+https://github.com/kzclaw/news-cli.git`

## Usage

Run via `exec` tool — `newscli` if installed globally, or `python3 cli.py` from the news-cli directory.

### Flag Mode (machine-friendly)

```bash
newscli --source hackernews:topstories --limit 5 --json
newscli --source "github:trending?language=Python" --limit 5
newscli --source all --limit 5 --json
```

### Natural Language Mode (human-friendly)

```bash
# Basic
newscli get hackernews topstories
newscli get github trending 10 language python
newscli get huggingface daily
newscli get zaker hot 10
newscli get v2ex hot
newscli get reddit popular 5
newscli get devto trending 10 tag python
newscli get lobsters hottest
newscli get rss bensbites 5

# Category / search
newscli get zaker category technology 10
newscli get zaker search AI 10

# Node / subreddit
newscli get v2ex node python 10
newscli get reddit subreddit technology 10

# Multi-source (use , or & as separator)
newscli get "hackernews:topstories,github:trending" 5
newscli get "hackernews:topstories&github:trending" 5

# All sources
newscli get all 10

# Modifiers
newscli get hackernews topstories 5 json           # JSON output
newscli get hackernews topstories 5 noenrich      # skip URL enrichment
newscli get hackernews topstories 5 keyword AI    # filter by keyword
newscli get all 15 json noenrich                  # combine modifiers

# List modules
newscli list
newscli list sources
newscli list modules
newscli list hackernews
```

### Multi-source separator (v1.1.2+)

Both `--source` flag and NL `get` mode accept `,` or `&` as separators between source:module pairs. Multiple `--source` flags are also supported for programmatic use.

```bash
# Comma separator
newscli --source "hackernews:topstories,github:trending" --limit 5 --json

# Ampersand separator
newscli --source "hackernews:topstories&github:trending" --limit 5 --json

# Multiple --source flags (recommended for scripts)
newscli --source hackernews:topstories --source github:trending --limit 5 --json
```

## Available Sources & Modules

| Source | Modules | Special Params |
|--------|---------|----------------|
| hackernews | topstories, newest, ask, show, jobs | — |
| github | trending | language |
| huggingface | daily, trending | — |
| zaker | hot, category, search | category, keyword |
| v2ex | hot, latest, node | node |
| reddit | popular, hot | subreddit |
| devto | trending, latest | tag |
| lobsters | hottest, newest | — |
| rss | preset name or URL | url |

## Flag Reference

| Flag | Default | Description |
|------|---------|-------------|
| `--source` | `all` | `source:module` pairs, comma or `&` separated. Repeat flag for multiple sources. |
| `--limit, -n` | `10` | Max items per source |
| `--keyword, -k` | — | Filter by keyword (AND match) |
| `--params, -p` | — | JSON: `{"source": {"param": "value"}}` |
| `--json` | off | JSON output (machine-readable, NewsItem v1.1 schema) |
| `--enrich, -e` | on | Auto-fetch og:description for null summaries |
| `--dedup` | `70` | Cross-source dedup threshold 0-100 (0=disabled) |
| `--strict` | off | Hard-fail on schema validation issues |
| `--no-validate` | off | Skip NewsItem v1.1 schema validation |
| `--no-enrich` | off | Skip URL enrichment (shorthand) |

## Output Format

Default: text table (human-readable).
`json`: full NewsItem v1.1 schema (includes `extra.heat_int` numeric + `schema_validation` warnings field).

```json
{
  "ok": true,
  "schema": "NewsItem v1.1",
  "sources": { "hackernews:topstories": 10 },
  "items": [{
    "source": "Hacker News",
    "module": "topstories",
    "title": "...",
    "url": "https://...",
    "time": "2h ago",
    "summary": "...",
    "heat": "1023 points",
    "author": "username",
    "extra": {
      "hn_id": 123,
      "hn_url": "...",
      "descendants": 42,
      "heat_int": 1023
    }
  }],
  "total": 10,
  "errors": [],
  "schema_validation": {
    "warnings": [],
    "ok": true
  }
}
```

## Features

- **Enrichment** (default): summary=null items → curl og:description from original URL
- **Deduplication** (v1.1+): adjustable threshold via `--dedup 0-100` (default 70, 0=disabled)
- **Parallel fetch**: ThreadPoolExecutor, max 8 concurrent
- **Schema validation** (v1.1+): NewsItem v1.1 auto-detect + `schema_validation` warnings field (`--strict` to hard-fail)
- **Natural language DSL**: no AI, pure string parsing (~130 lines)
