# News Aggregation Bot

Weekly automated news digest system that fetches German news feeds, filters content using Claude AI, and delivers personalized summaries to Discord.

## Testing Feed Accessibility

### Local Test (Residential IP)
```bash
python test_feeds.py
```

### GitHub Actions Test (Datacenter IP)
The workflow `.github/workflows/test-feeds.yml` tests if feeds are accessible from GitHub Actions runners (Azure IPs).

To run:
1. Push this repo to GitHub
2. Go to Actions tab
3. Run "Test RSS Feed Access" workflow manually

## Setup

```bash
pip install -r requirements.txt
```

## Next Steps

See [CLAUDE.md](./CLAUDE.md) for full project documentation.
