# News Aggregation Bot - Project Brief

## Project Overview
Weekly automated news digest system that fetches German news feeds, filters content using Claude AI, and delivers personalized summaries to Discord.

## Goals
- Eliminate noise from traditional news sources (opinion pieces, irrelevant content)
- Receive curated world news once per week
- Zero-cost or low-cost solution (~80€/year acceptable)
- Fully automated execution

## Tech Stack

### Core Components
- **RSS Feeds**: Direct feed access (no Inoreader needed - tested successfully)
- **Claude Agent SDK (Python)**: Content filtering and summarization via Anthropic API
- **Discord Webhook**: Delivery mechanism (post-MVP)
- **Python 3.11+**: Implementation language
- **GitHub Actions**: Weekly cron execution

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

```
┌─────────────┐
│  Inoreader  │  Fetches feeds, handles Cloudflare
│     API     │  Pre-filtering via Rules (optional)
└──────┬──────┘
       │
       │ Weekly cron trigger
       │
┌──────▼──────────────────────────┐
│  Python Script                  │
│  - Fetch articles via API       │
│  - OAuth token management       │
│  - Rate limiting                │
└──────┬──────────────────────────┘
       │
       │ Raw articles
       │
┌──────▼──────────────────────────┐
│  Claude Sonnet 4.5 (Bedrock)    │
│  - Filter opinion pieces        │
│  - Remove irrelevant content    │
│  - Summarize key points         │
│  - Format for readability       │
└──────┬──────────────────────────┘
       │
       │ Filtered digest
       │
┌──────▼──────────────────────────┐
│  Discord Webhook                │
│  - Formatted message            │
│  - Weekly delivery              │
└─────────────────────────────────┘
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

## Implementation Steps

### Phase 1: Setup & Verification
1. **Test direct feed access** (5 min)
   ```python
   import requests
   r = requests.get('https://www.tagesschau.de/xml/rss2/')
   print(r.status_code)
   ```
   Determine if Cloudflare bypass is actually needed

2. **Inoreader setup** (30 min)
   - Create Pro account (6,67€/month)
   - Register OAuth app at https://www.inoreader.com/developers/
   - Set redirect URI: `http://localhost:8080/oauth/redirect`
   - Add target feeds
   - Test OAuth flow

3. **Infrastructure setup** (2-3h if Oracle Cloud)
   - Provision Oracle Cloud Always Free VM
   - Configure networking (VCN, security lists)
   - Install Python 3.11+, dependencies
   - Setup cron for weekly execution

### Phase 2: Core Implementation
4. **OAuth implementation** (1-2h)
   - Implement token acquisition
   - Token refresh logic
   - Secure token storage

5. **Inoreader API integration** (2-3h)
   - Fetch unread articles
   - Parse article metadata
   - Handle pagination
   - Mark articles as read after processing

6. **Claude filtering** (2-3h)
   - Bedrock client setup
   - Prompt engineering for content filtering
   - Batch processing for efficiency
   - Cost optimization

7. **Discord integration** (30 min)
   - Webhook URL configuration
   - Message formatting (Markdown)
   - Error handling

### Phase 3: Polish & Automation
8. **Filtering refinement** (ongoing)
   - Iterate on Claude prompts
   - Add/remove sources based on quality
   - Tune summary length

9. **Monitoring & logging** (1h)
   - Error notifications
   - Success confirmations
   - Usage tracking

## Technical Considerations

### Inoreader API
- OAuth 2.0 required
- Rate limiting: Pro plan guaranteed hourly refresh
- Endpoints needed:
  - `/reader/api/0/stream/contents` - Fetch articles
  - `/reader/api/0/subscription/list` - List feeds
  - `/reader/api/0/edit-tag` - Mark as read

### Claude Filtering Prompt Strategy
```
You are filtering a news feed for a technical reader interested in:
- World news (politics, economics, major events)
- Tech/AI developments
- No opinion pieces or editorials
- No local German news unless internationally significant

For each article, determine:
1. Is this actual news or opinion/analysis?
2. Is this internationally relevant?
3. Does this match the reader's interests?

Return only articles that pass all criteria with:
- Original headline
- 2-3 sentence summary
- Why it's relevant
```

### Cost Estimation
- **Inoreader Pro**: 80€/year (6,67€/month)
- **AWS Bedrock**: ~0.50-2€/month (weekly processing, ~50 articles)
- **Oracle Cloud**: Free tier sufficient
- **Total**: ~85-105€/year

### Security Considerations
- Store OAuth tokens encrypted or in secure secret manager
- Use environment variables for sensitive config
- Implement retry logic with exponential backoff
- Log failures without exposing credentials

## Success Metrics
- ✅ Zero manual intervention after setup
- ✅ Digest delivered every Sunday 8 AM
- ✅ 90%+ relevant articles (no opinion pieces)
- ✅ 5-15 articles per digest
- ✅ <5 minute reading time

## Alternative: Minimal Viable Product (MVP)
If Inoreader seems overkill, start with:
1. Direct RSS fetch with `feedparser` (test if Cloudflare blocks)
2. If blocked, deploy on Oracle Cloud with residential-like IP
3. If that fails, then invest in Inoreader Pro

## Decision Points

### Do we need Inoreader?
**Test first**: Try direct feed access from target infrastructure
- If feeds are open → Use `feedparser` + simple cron
- If Cloudflare blocks → Evaluate Oracle Cloud vs Inoreader Pro

### Which infrastructure?
- **Oracle Cloud** if feeds need bypass but want zero vendor lock-in
- **Inoreader Pro** if willing to pay for convenience
- **Home server** if already available

### Filtering location?
- **Pre-filter in Inoreader**: Use Rules feature, reduce Claude costs
- **Filter in Claude**: More flexibility, slightly higher costs

## Next Steps
1. **Immediate**: Test direct feed access from local machine
2. **If accessible**: Build MVP with `feedparser` + Claude + Discord
3. **If blocked**: Decide between Oracle Cloud (free, complex) vs Inoreader (paid, simple)
4. **Then**: Implement full solution based on decision

## Resources
- Inoreader API Docs: https://www.inoreader.com/developers/
- Inoreader OAuth Guide: https://www.inoreader.com/developers/oauth
- AWS Bedrock Python SDK: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime.html
- Discord Webhooks: https://discord.com/developers/docs/resources/webhook

## Notes
- User has existing AWS Bedrock access via MOIA work
- User prefers honest, direct communication
- Weekly digest frequency keeps costs minimal
- Focus on pragmatic solutions over perfect architecture
