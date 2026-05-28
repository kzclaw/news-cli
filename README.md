# newscli

**Unified news aggregation CLI** — pull from 9 sources in one command.

```
newscli get hackernews topstories 5
newscli get github trending 10 language python
newscli get all 15 json
```

## Features

- **9 sources**: Hacker News · GitHub Trending · Hugging Face · ZAKER · V2EX · Reddit · DEV.to · Lobsters · RSS
- **25+ modules** — each source has multiple views (topstories, ask, show, job...)
- **Natural language DSL** — `get`, `list`, `看`, `拉` — no flags to remember
- **URL enrichment** — auto-fetches og:description for every item
- **Deduplication** — cross-source, Jaccard similarity, keeps richer item
- **JSON output** — `NewsItem v1.0` schema, always 9 fields

## Requirements

- Python 3.10+
- `requests`, `beautifulsoup4`, `lxml` (installed automatically)

## Install

### One-liner (any OS)

```bash
curl -sSL https://raw.githubusercontent.com/kzclaw/news-cli/main/install.sh | bash
```

### pip

```bash
pip install --user -e git+https://github.com/kzclaw/news-cli.git
```

### pipx (recommended)

```bash
pipx install git+https://github.com/kzclaw/news-cli.git
```

## Usage

### Natural language mode

```bash
newscli get hackernews topstories 5
newscli get github trending 10 language python
newscli get v2ex node python 10
newscli get reddit subreddit technology 10
newscli get hackernews topstories 5 and github trending 10 and huggingface daily 5
newscli get all 15 json
newscli list
newscli list github
```

### Flag mode

```bash
python3 cli.py --source hackernews:topstories --limit 5 --json
python3 cli.py --source "hackernews:topstories&github:trending" --limit 5
```

### JSON output

Add `json` at the end of any command:

```bash
newscli get hackernews topstories 5 json
```

## Source & Module reference

| Source | Modules |
|--------|---------|
| `hackernews` | `topstories`, `new`, `ask`, `show`, `jobs` |
| `github` | `trending`, `trending-weekly`, `trending-monthly` |
| `huggingface` | `daily`, `weekly`, `monthly` |
| `zaker` | `hot`, `news` |
| `v2ex` | `latest`, `hot`, `node:<name>` |
| `reddit` | `subreddit:<name>` |
| `devto` | `latest`, `top`, `tags:<tag>` |
| `lobsters` | `newest`, `hot`, `top`, `upcoming` |
| `rss` | `feed:<url>` |

## Architecture

```
newscli/
  cli.py          — dual-mode entry (flags + NL DSL)
  aggregator.py   — ThreadPoolExecutor dispatcher
  parser.py      — NL DSL parser
  enrich.py      — concurrent og:description fetcher
  sources/
    base.py      — NewsSource base class + NewsItem schema
    hackernews.py / github.py / ...
```

## NewsItem Schema

Every item follows `NewsItem v1.0`:

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

## License

MIT