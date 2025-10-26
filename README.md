# News Aggregation Bot

Automated daily news digest system that fetches German/international news feeds, filters content using Claude AI, and delivers curated summaries to Discord.

**Status:** Production - Running daily at 8:00 AM German time

## Overview

- **Fully automated** via GitHub Actions (no manual intervention)
- **15+ RSS sources** (German + international news)
- **AI-powered filtering** with Claude Sonnet 4.5
- **Smart deduplication** with 7-day lookback
- **Discord delivery** with clean, formatted messages
- **Final output:** Highly curated daily digest

## Pipeline

The system runs through 5 stages daily:

1. **Fetch RSS Feeds** - Collect articles from 15+ German and international news sources
2. **Aggregate** - Normalize article format and extract metadata
3. **Deduplicate** - Remove duplicate articles from the last 7 days
4. **Keyword Filter** - Apply blacklist of 128 keywords to filter unwanted topics
5. **AI Categorization** - Claude AI categorizes remaining articles into MUST-KNOW, INTERESSANT, and NICE-TO-KNOW
6. **Discord Delivery** - Post curated digest to Discord channel

Result: Highly curated daily digest delivered to Discord

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) for package management
- Claude Pro subscription (for Agent SDK)

### Setup

```bash
# Install dependencies
uv pip install -r requirements.txt

# Setup Claude authentication (generates OAuth token)
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

### GitHub Actions Setup

For automated daily execution, configure these secrets in your GitHub repository:

1. **`CLAUDE_CODE_OAUTH_TOKEN`** - Your Claude OAuth token
   - Run `claude setup-token` locally to generate
   - Token is saved in `~/.claude/config`
   - Add to GitHub Secrets for workflow access
   - Requires Claude Pro subscription

2. **`DISCORD_WEBHOOK_URL`** - Discord webhook URL
   - Create webhook in Discord server settings
   - Format: `https://discord.com/api/webhooks/...`

## Key Features

### AI Filtering
- Claude AI categorizes articles by relevance and importance
- Filters out opinion pieces, sports, and other unwanted topics
- Focuses on world news and tech/AI developments

### Discord Delivery
- Clean, readable message formatting
- Automatic message chunking for long digests

## Documentation

See [CLAUDE.md](./CLAUDE.md) for complete project documentation, architecture decisions, and technical details.

## Cost

- **Claude API:** Included in Claude Pro subscription
- **GitHub Actions:** Free tier (<2000 min/month)
- **Total:** **€0/year** (completely free!)
