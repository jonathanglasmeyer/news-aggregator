# News Aggregation Bot - Project Brief

## Project Overview
Daily automated news digest system that fetches German news feeds, filters content using Claude AI, and delivers personalized summaries to Discord.

## Goals
- Eliminate noise from traditional news sources (opinion pieces, irrelevant content)
- Receive curated world news daily
- Zero-cost or low-cost solution (~80€/year acceptable)
- Fully automated execution

## Tech Stack

### Core Components
- **RSS Feeds**: Direct feed access (no Inoreader needed - tested successfully)
- **Claude Agent SDK (Python)**: Content filtering and summarization via Anthropic API
- **Discord Webhook**: Delivery mechanism
- **Python 3.11+**: Implementation language
- **GitHub Actions**: Daily cron execution

### Claude Integration
Using Anthropic API directly with Claude Pro/Max plan:
- Install: `uv pip install anthropic`
- Auth: Set `ANTHROPIC_API_KEY` environment variable
- No Bedrock, no AWS - direct Anthropic API

### Infrastructure Options
1. **Oracle Cloud Free Tier** (preferred): Static IP, 4 ARM cores, 24GB RAM, 10TB bandwidth
2. **Local machine/Raspberry Pi**: Residential IP, simple cron
3. **GitHub Actions**: Only if feeds aren't Cloudflare-protected

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
│  - 15+ German/Int'l sources     │
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
       │ Stage 3: Remote Embedding Filter
       │
┌──────▼──────────────────────────┐
│  stage3_embed_filter_remote.py  │
│  - SSH to Hetzner VPS           │
│  - POST JSON via curl           │
│  - Keyword blacklist filter     │
│  - Output: ~50-60 articles      │
└──────┬──────────────────────────┘
       │  ┌─────────────────────────┐
       └─▶│ Hetzner VPS (Port 3007) │
          │ - FastAPI service       │
          │ - Docker container      │
          │ - 128 blacklist keywords│
          └─────────────────────────┘
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
  ↓ embedding filter (SSH → Hetzner)
Keyword-Filtered          → data/embedded/YYYYMMDD_HHMMSS.json
  ↓ claude filter (AI categorization)
Final Digest              → data/filtered/digest_YYYYMMDD_HHMMSS_v4.md
  ↓ post to discord
Discord Channel           → Webhook posts (10-15 messages)
```

## Target News Sources

### German Primary Sources
- Tagesschau: `https://www.tagesschau.de/xml/rss2/`
- Zeit Online: `https://newsfeed.zeit.de/index`
- Spiegel: `https://www.spiegel.de/schlagzeilen/index.rss`

### Additional Sources (to be determined)
- International news (AP, Reuters, BBC)
- Tech/AI specific feeds
- Regional sources

## Implementation Status

### ✅ Completed (Production-Ready)

1. **Stage 1: RSS Fetching**
   - Direct feed access via `feedparser`
   - 15+ German/international sources
   - No Cloudflare issues encountered
   - File: `daily_fetch.py`

2. **Stage 2: Aggregation**
   - Normalized article format
   - Metadata extraction
   - File: `stage2_aggregate.py`

3. **Stage 2.5: Deduplication**
   - 7-day lookback window
   - URL-based deduplication (fixed: was using wrong key 'url' instead of 'link')
   - Filters ~80% duplicates effectively
   - File: `stage2_5_deduplicate.py`

4. **Stage 3: Remote Embedding Filter**
   - Hetzner VPS deployment (Docker)
   - SSH + curl integration
   - 128 keyword blacklist (removed 'maker' for false positives)
   - Files: `stage3_embed_filter_remote.py`, `embedding_service.py`

5. **Stage 4: Claude AI Filter**
   - Claude Agent SDK integration
   - 3-tier categorization (MUST-KNOW/INTERESSANT/NICE-TO-KNOW)
   - Prompt version 4 (tested and working)
   - Compact bullet point post-processing (removes unwanted blank lines)
   - File: `stage4_filter.py`

6. **Stage 5: Discord Delivery**
   - Smart chunking (<2000 chars)
   - Section-aware zero-width space separators
   - Compact NICE-TO-KNOW bullet lists
   - File: `stage5_discord_webhook.py`

7. **GitHub Actions Automation**
   - Daily cron: 7:00 AM UTC (8:00 AM German time MEZ)
   - SSH key setup for Hetzner
   - Secret management (5 secrets)
   - Write permissions for automated commits
   - File: `.github/workflows/daily-digest.yml`

### 🔄 Ongoing Optimization

- Prompt refinement for Stage 4
- Source quality monitoring
- Deduplication accuracy tuning

## Technical Considerations

### Claude Agent SDK
- **Authentication**: OAuth token via `claude setup-token`
- **Model**: claude-sonnet-4.5-20251022
- **Token expiry**: ~1 year (requires renewal)
- **Environment**: `CLAUDE_CODE_OAUTH_TOKEN`
- **Processing time**: ~3-4 minutes for 250-280 articles

### Hetzner VPS (Embedding Service)
- **Server**: Cheapest VPS tier
- **Port**: 3007 (internal only, firewall protected)
- **Container**: Docker with FastAPI
- **Deployment**: `./deploy-embedding.sh` (automated)
- **SSH**: Ed25519 key-based authentication
- **Health check**: `/health` endpoint

### Discord Webhook
- **Format**: Markdown with smart chunking
- **Limit**: 2000 chars per message
- **Rate limit**: 1 request/second
- **Formatting**:
  - Section-aware zero-width space separators (only MUST-KNOW/INTERESSANT)
  - Compact bullet lists in NICE-TO-KNOW (no blank lines)
  - Link preview suppression with `<URL>`

### GitHub Actions Secrets
1. `CLAUDE_CODE_OAUTH_TOKEN` - Claude AI access
2. `DISCORD_WEBHOOK_URL` - Discord delivery
3. `HETZNER_HOST` - VPS hostname
4. `HETZNER_USER` - SSH user (root)
5. `HETZNER_SSH_KEY` - Private key for SSH

### Cost Estimation (Actual)
- **Hetzner VPS**: ~€5/month (cheapest tier)
- **Claude API**: Included in Claude Pro subscription
- **GitHub Actions**: Free tier sufficient (<2000 min/month)
- **Total**: ~€60/year (only Hetzner VPS)

### Security Considerations
- All secrets stored in GitHub Secrets (encrypted at rest)
- SSH key-based authentication (no passwords)
- Embedding service: internal port only, no public exposure
- Discord webhook: rate-limited, no sensitive data exposed
- Data tracked in git for transparency (no PII in articles)

## Success Metrics

### ✅ Achieved
- Zero manual intervention (fully automated)
- Daily digest delivered at 7:00 AM UTC (8:00 AM German time)
- 3-tier categorization working (MUST-KNOW/INTERESSANT/NICE-TO-KNOW)
- Deduplication filters ~80% duplicates (350 → 57 articles)
- Final output: ~15-20 curated articles per day
- Complete end-to-end pipeline tested and validated in GitHub Actions
- Automated commits to repository with results

### 🔄 Monitoring
- Relevance quality (ongoing prompt refinement)
- Deduplication effectiveness (currently 80-85% duplicate rate)
- Discord formatting (section-aware separators, compact bullets)
- Claude API costs (included in Pro subscription)

## Key Architectural Decisions

### ✅ Decided & Implemented

1. **No Inoreader needed** - Direct RSS access works without Cloudflare issues
2. **GitHub Actions over self-hosted** - Free tier sufficient, better reliability
3. **Hetzner VPS for embedding service** - €5/month, Docker deployment
4. **Claude Agent SDK over Bedrock** - Simpler auth, included in Pro subscription
5. **Discord Webhook over Bot** - Simpler for automation, no persistent process
6. **Daily over Weekly** - More manageable article volume per run
7. **Data tracked in git** - Transparency and debugging over repo size concerns

## Lessons Learned

1. **RSS feeds are more accessible than expected** - No Cloudflare blocking encountered
2. **Two-stage filtering works well** - Keyword blacklist (Stage 3) + AI (Stage 4)
3. **Deduplication is essential** - Prevents repeated coverage of same stories (filters ~80% duplicates)
4. **Silent bugs are dangerous** - Deduplication bug (wrong key 'url' vs 'link') was invisible for days, only caught by examining logs
5. **Discord formatting is finicky** - Requires section-aware zero-width spaces and post-processing for compact bullets
6. **GitHub Actions SSH needs careful setup** - Ed25519 keys, known_hosts handling
7. **LLM output needs post-processing** - Claude adds unwanted blank lines between bullets, regex cleanup required

## Resources

### Documentation
- **Claude Agent SDK**: https://github.com/anthropics/claude-code
- **Discord Webhooks**: https://discord.com/developers/docs/resources/webhook
- **feedparser (Python)**: https://feedparser.readthedocs.io/
- **GitHub Actions**: https://docs.github.com/en/actions

### Key Files
- **Pipeline orchestration**: `.github/workflows/daily-digest.yml`
- **Stage scripts**: `daily_fetch.py`, `stage2_aggregate.py`, `stage2_5_deduplicate.py`, `stage3_embed_filter_remote.py`, `stage4_filter.py`, `stage5_discord_webhook.py`
- **Embedding service**: `embedding_service.py`, `filter_logic.py`, `Dockerfile.embedding`, `docker-compose.embedding.yml`
- **Deployment**: `deploy-embedding.sh`

### Setup Commands
```bash
# Claude OAuth token setup
claude setup-token

# Test RSS fetch locally
uv run python daily_fetch.py

# Test full pipeline locally
uv run python stage2_aggregate.py data/raw/daily/YYYY-MM-DD.json
uv run python stage2_5_deduplicate.py data/aggregated/YYYYMMDD_HHMMSS.json
uv run python stage3_embed_filter_remote.py data/deduplicated/YYYYMMDD_HHMMSS.json
uv run python stage4_filter.py data/embedded/YYYYMMDD_HHMMSS.json
uv run python stage5_discord_webhook.py data/filtered/digest_YYYYMMDD_HHMMSS_v4.md

# Deploy embedding service to Hetzner
./deploy-embedding.sh
```

## Notes
- Direct RSS access works without proxies/VPNs
- Claude Pro subscription required for Agent SDK
- Hetzner VPS is cheapest viable option (€5/month)
- Daily execution prevents article overload (vs weekly)
- Data tracked in git aids debugging and transparency
