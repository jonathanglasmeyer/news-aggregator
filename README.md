# News Aggregation Bot

Automated daily news digest system that fetches German/international news feeds, filters content using Claude AI, and delivers curated summaries to Discord.

**Status:** ✅ Production - Running daily at 8:00 AM German time

## Overview

- 🔄 **Fully automated** via GitHub Actions (no manual intervention)
- 📰 **15+ RSS sources** (German + international news)
- 🤖 **AI-powered filtering** with Claude Sonnet 4.5
- 📊 **Smart deduplication** (~80% duplicate removal)
- 💬 **Discord delivery** with clean, formatted messages
- 📈 **Final output:** ~15-20 curated articles per day

## Pipeline

```
RSS Feeds (350 articles)
  → Deduplication (→57 articles, 80% filtered)
  → Keyword Filter (→50 articles)
  → Claude AI (→15-20 articles)
  → Discord Webhook
```

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) for package management
- Claude Pro subscription (for Agent SDK)

### Setup

```bash
# Install dependencies
uv pip install -r requirements.txt

# Setup Claude authentication
claude setup-token

# Test RSS fetch locally
uv run python daily_fetch.py

# Test full pipeline
uv run python src/pipeline/stage2_aggregate.py data/raw/daily/YYYY-MM-DD.json
uv run python src/pipeline/stage2_5_deduplicate.py data/aggregated/YYYYMMDD_HHMMSS.json
uv run python src/pipeline/stage3_keyword_filter.py data/deduplicated/YYYYMMDD_HHMMSS.json
uv run python src/pipeline/stage4_filter.py data/filtered_keywords/YYYYMMDD_HHMMSS.json 4
uv run python src/pipeline/stage5_discord_webhook.py data/filtered/digest_YYYYMMDD_HHMMSS_v4.md
```

### GitHub Actions Secrets

Required for automated execution:

1. `CLAUDE_CODE_OAUTH_TOKEN` - Claude AI access
2. `DISCORD_WEBHOOK_URL` - Discord delivery

## Architecture

**5-Stage Pipeline:**

1. **Stage 1:** Fetch RSS feeds (15+ sources)
2. **Stage 2:** Aggregate last 7 days
3. **Stage 2.5:** Deduplicate by URL (~80% reduction)
4. **Stage 3:** Local keyword blacklist filter (128 keywords)
5. **Stage 4:** Claude AI categorization (MUST-KNOW/INTERESSANT/NICE-TO-KNOW)
6. **Stage 5:** Discord webhook delivery

**External Services:**

- Discord: Webhook delivery
- GitHub Actions: Daily execution at 7:00 UTC

## Key Features

### Deduplication
- 7-day lookback window
- URL-based matching
- Filters ~80% duplicates effectively

### AI Filtering
- 3-tier categorization
- Tech/AI focus for INTERESSANT tier
- World news for MUST-KNOW tier
- Grouped miscellaneous in NICE-TO-KNOW

### Discord Formatting
- Section-aware zero-width space separators
- Compact bullet lists in NICE-TO-KNOW
- Smart chunking (<2000 chars/message)

## Documentation

See [CLAUDE.md](./CLAUDE.md) for complete project documentation, architecture decisions, and technical details.

## Cost

- **Claude API:** Included in Claude Pro subscription
- **GitHub Actions:** Free tier (<2000 min/month)
- **Total:** **€0/year** (completely free!)
