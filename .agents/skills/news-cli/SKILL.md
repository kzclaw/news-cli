---
name: news-cli
description: "Unified news aggregation CLI — 9 sources, 25+ modules, natural language DSL. Run newscli directly in exec."
metadata: { "openclaw": { "emoji": "📰" } }
---

# news-cli

Unified news aggregation CLI tool. Fetch news from 9 sources across 25+ modules with a single command.

## Source

- GitHub: `https://github.com/kzclaw/news-cli`
- Install: `pip install --user -e git+https://github.com/kzclaw/news-cli.git`

## Usage

Run via `exec` tool — `python3 cli.py` from the news-cli directory, or `newscli` if installed globally.

### Flag Mode (machine-friendly)

```bash
python3 cli.py --source hackernews:topstories --limit 5 --json
python3 cli.py --source "github:trending?language=Python" --limit 5
python3 cli.py --source all --limit 5 --json
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

# Multi-source parallel fetch
newscli get hackernews topstories 5 and github trending 10 and huggingface daily 5

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

## Output Format

Default: text table (human-readable).
`json`: full NewsItem v1.0 schema.

```json
{
  "ok": true,
  "schema": "NewsItem v1.0",
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
    "extra": { "hn_id": 123, "hn_url": "...", "descendants": 42 }
  }],
  "total": 10,
  "errors": []
}
```

## Features

- **Enrichment** (default): summary=null items → curl og:description from original URL
- **Deduplication**: 70% title similarity threshold across multi-source fetch
- **Parallel fetch**: ThreadPoolExecutor, max 8 concurrent
- **Natural language DSL**: no AI, pure string parsing (~130 lines)