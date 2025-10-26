# Data Directory

3-stage processing pipeline for news aggregation with daily fetching and weekly filtering.

## Structure

```
data/
├── raw/
│   └── daily/           # Stage 1: Daily RSS snapshots
│       ├── 2025-10-20.json
│       ├── 2025-10-21.json
│       └── ...
├── aggregated/          # Stage 2: Weekly aggregated + deduplicated
│   └── 2025-W43.json
└── filtered/            # Stage 3: Claude filtered digests
    └── digest_2025-W43_v1.json
```

## Workflow

### Stage 1: Daily Fetch (GitHub Actions daily cron)

```bash
uv run python daily_fetch.py
```

- Fetches all configured RSS feeds (no date filtering)
- Saves daily snapshot to `data/raw/daily/YYYY-MM-DD.json`
- ~5 seconds, no Claude API calls
- **Run**: Daily via GitHub Actions

### Stage 2: Aggregate (Sunday, before filtering)

```bash
uv run python stage2_aggregate.py
```

- Loads last 7 daily dumps ad-hoc (no need to specify files)
- Deduplicates by URL (primary) or title+source (fallback)
- Saves to `data/aggregated/YYYY-Www.json`
- ~1 second, no Claude API calls
- **Run**: Sunday via GitHub Actions (before Stage 3)

### Stage 3: Filter with Claude (Sunday, after aggregation)

```bash
# Use latest aggregated data
uv run python stage3_filter.py

# Use specific aggregated data
uv run python stage3_filter.py data/aggregated/2025-W43.json

# Use specific data + prompt version
uv run python stage3_filter.py data/aggregated/2025-W43.json v2
```

- Filters aggregated articles using Claude
- Saves digest to `data/filtered/`
- ~70 seconds for Claude filtering
- **Run**: Sunday via GitHub Actions (after Stage 2)

## Benefits

- **Full week coverage**: Daily fetching captures all articles (not just last 2 days)
- **Deduplication**: 85%+ duplicate removal (articles appear in RSS for multiple days)
- **3-stage separation**: Fetch → Aggregate → Filter
- **Fast iteration**: Aggregate once, filter many times with different prompts
- **Prompt engineering**: Test different Claude prompts without re-aggregating
- **Cost efficient**: Daily fetch = fast/free, Claude only runs weekly
- **Reproducible**: Same aggregate produces consistent filtered results
- **Versioned**: Track different prompt versions
