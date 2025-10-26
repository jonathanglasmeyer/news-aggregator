# News Aggregation Bot - Technical Reference

Automated daily news digest system: Fetches 9 RSS feeds (German + international + tech), filters via keyword blacklist + Claude AI, delivers curated digest to Discord. Runs entirely in GitHub Actions (€0/year).

## Architecture

### Current Pipeline (5 Stages)

**Execution:** Daily at 7:00 AM UTC (8:00 AM German time MEZ) via GitHub Actions

```
┌─────────────────────────────────────────────────────┐
│  GitHub Actions (Daily Cron: 0 7 * * *)             │
└──────┬──────────────────────────────────────────────┘
       │
       │ Stage 1: Fetch RSS Feeds
       │
┌──────▼──────────────────────────┐
│  daily_fetch.py                 │
│  - Direct RSS parsing           │
│  - feedparser library           │
│  - 9 RSS sources                │
│  - Output: raw JSON (~300-500)  │
└──────┬──────────────────────────┘
       │
       │ Stage 2: Aggregate Articles
       │
┌──────▼──────────────────────────┐
│  stage2_aggregate.py            │
│  - Normalize article format     │
│  - Extract metadata             │
│  - Output: aggregated JSON      │
└──────┬──────────────────────────┘
       │
       │ Stage 2.5: Deduplicate
       │
┌──────▼──────────────────────────┐
│  stage2_5_deduplicate.py        │
│  - Check last 7 days            │
│  - URL-based deduplication      │
│  - Filters ~80% duplicates      │
└──────┬──────────────────────────┘
       │
       │ Stage 3: Keyword Blacklist Filter
       │
┌──────▼──────────────────────────┐
│  stage3_keyword_filter.py       │
│  - Local keyword matching       │
│  - 128 blacklist keywords       │
│  - Fast exact-match filtering   │
│  - Output: ~270 articles        │
└──────┬──────────────────────────┘
       │
       │ Stage 4: Claude AI Filter
       │
┌──────▼──────────────────────────┐
│  stage4_filter.py               │
│  - Claude Agent SDK             │
│  - Sonnet 4.5 model             │
│  - 3-tier categorization:       │
│    * MUST-KNOW (world events)   │
│    * INTERESSANT (tech/AI)      │
│    * NICE-TO-KNOW (grouped)     │
│  - Compact bullet formatting    │
│  - Output: ~15-20 final items   │
└──────┬──────────────────────────┘
       │
       │ Stage 5: Post to Discord
       │
┌──────▼──────────────────────────┐
│  stage5_discord_webhook.py      │
│  - Format for Discord           │
│  - Smart chunking (<2000 chars) │
│  - Section-aware zero-width sep │
│  - Compact NICE-TO-KNOW bullets │
│  - Posts 10-15 messages         │
└─────────────────────────────────┘
```

### Data Flow

```
RSS Feeds (raw)           → data/raw/daily/YYYY-MM-DD.json
  ↓ aggregate
Aggregated Articles       → data/aggregated/YYYYMMDD_HHMMSS.json
  ↓ deduplicate (7 days)
Deduplicated              → data/deduplicated/YYYYMMDD_HHMMSS.json
  ↓ keyword filter (local, 128 keywords)
Keyword-Filtered          → data/filtered_keywords/YYYYMMDD_HHMMSS.json
  ↓ claude filter (AI categorization)
Final Digest              → data/filtered/digest_YYYYMMDD_HHMMSS_v4.md
  ↓ post to discord
Discord Channel           → Webhook posts (10-15 messages)
```

## Technical Considerations

### Claude Agent SDK
- **Authentication**: OAuth token via `claude setup-token`
- **Model**: claude-sonnet-4.5-20251022
- **Token expiry**: ~1 year (requires renewal)
- **Environment**: `CLAUDE_CODE_OAUTH_TOKEN`
- **Processing time**: ~3-4 minutes for 250-280 articles

### Discord Webhook
- **Format**: Markdown with automatic chunking
- **Limit**: 2000 chars per message
- **Rate limit**: 1 request/second

### GitHub Actions Secrets
1. `CLAUDE_CODE_OAUTH_TOKEN` - Claude AI access (OAuth token from `claude setup-token`)
2. `DISCORD_WEBHOOK_URL` - Discord webhook URL

## Resources

### Documentation
- **Claude Agent SDK**: https://github.com/anthropics/claude-code
- **Discord Webhooks**: https://discord.com/developers/docs/resources/webhook
- **feedparser (Python)**: https://feedparser.readthedocs.io/
- **GitHub Actions**: https://docs.github.com/en/actions

### Key Files
- **Pipeline orchestration**: `.github/workflows/daily-digest.yml`
- **Stage scripts**: `src/pipeline/stage1_fetch.py`, `stage2_aggregate.py`, `stage2_5_deduplicate.py`, `stage3_keyword_filter.py`, `stage4_filter.py`, `stage5_discord_webhook.py`
- **Filter logic**: `src/services/filter_logic.py` (128 blacklist keywords)
- **Feed configuration**: `src/feeds.py` (9 RSS sources)
