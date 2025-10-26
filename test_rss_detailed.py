#!/usr/bin/env python3
"""
Detailed RSS feed analysis - check what content we actually get.
"""

import feedparser
from datetime import datetime

# Working feeds from previous test
FEEDS = {
    'German News': {
        'Tagesschau': 'https://www.tagesschau.de/xml/rss2/',
        'Deutschlandfunk': 'https://www.deutschlandfunk.de/die-nachrichten.353.de.rss',
        'Tagesschau Ausland': 'https://www.tagesschau.de/ausland/index~rss2.xml',
    },
    'International': {
        'BBC World': 'http://feeds.bbci.co.uk/news/world/rss.xml',
        'The Guardian World': 'https://www.theguardian.com/world/rss',
        'Al Jazeera': 'https://www.aljazeera.com/xml/rss/all.xml',
    },
    'Tech': {
        'Ars Technica': 'http://feeds.arstechnica.com/arstechnica/index',
        'The Verge': 'https://www.theverge.com/rss/index.xml',
        'Heise Online': 'https://www.heise.de/rss/heise-atom.xml',
        'The Register': 'https://www.theregister.com/headlines.atom',
        'Hacker News': 'https://news.ycombinator.com/rss',
    },
}

def analyze_feed(name, url):
    """Parse feed and show what content we get."""
    print(f"\n{'='*80}")
    print(f"{name}")
    print(f"{'='*80}")
    print(f"URL: {url}")

    feed = feedparser.parse(url)

    if feed.bozo:
        print(f"⚠️  Feed parsing warning: {feed.bozo_exception}")

    # Feed metadata
    print(f"\nFeed Type: {feed.version if hasattr(feed, 'version') else 'Unknown'}")
    print(f"Total Entries: {len(feed.entries)}")

    if not feed.entries:
        print("❌ No entries found!")
        return

    # Analyze first 3 entries
    print(f"\n--- Sample Entries (first 3) ---")
    for i, entry in enumerate(feed.entries[:3], 1):
        print(f"\n[{i}] {entry.get('title', 'NO TITLE')[:80]}")

        # Check what fields are available
        has_summary = 'summary' in entry
        has_content = 'content' in entry
        has_description = 'description' in entry
        has_link = 'link' in entry

        print(f"    Fields: ", end="")
        fields = []
        if has_link:
            fields.append("link")
        if has_summary:
            fields.append("summary")
        if has_content:
            fields.append("content")
        if has_description:
            fields.append("description")
        print(", ".join(fields) if fields else "minimal")

        # Show content preview
        content = None
        if has_content and entry.content:
            content = entry.content[0].value
        elif has_summary:
            content = entry.summary
        elif has_description:
            content = entry.description

        if content:
            # Strip HTML tags for preview
            import re
            clean = re.sub('<[^<]+?>', '', content)
            preview = clean[:200].replace('\n', ' ').strip()
            print(f"    Preview: {preview}...")
        else:
            print(f"    Preview: (no content)")

        if has_link:
            print(f"    Link: {entry.link[:60]}...")

    # Summary
    print(f"\n--- Content Analysis ---")

    # Check all entries for content availability
    entries_with_full_text = sum(1 for e in feed.entries if 'content' in e or (
        'summary' in e and len(e.get('summary', '')) > 300
    ))

    print(f"Entries with substantial content: {entries_with_full_text}/{len(feed.entries)}")

    # Average content length
    content_lengths = []
    for entry in feed.entries:
        if 'content' in entry and entry.content:
            content_lengths.append(len(entry.content[0].value))
        elif 'summary' in entry:
            content_lengths.append(len(entry.summary))

    if content_lengths:
        avg_length = sum(content_lengths) / len(content_lengths)
        print(f"Average content length: {int(avg_length)} chars")

        # Categorize
        if avg_length < 200:
            content_type = "Headlines only (need to fetch full article)"
        elif avg_length < 500:
            content_type = "Short summaries"
        elif avg_length < 1500:
            content_type = "Medium summaries (good for filtering)"
        else:
            content_type = "Full-text or long summaries"

        print(f"Content type: {content_type}")

def main():
    print(f"RSS FEED DETAILED ANALYSIS")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    for category, feeds in FEEDS.items():
        print(f"\n{'#'*80}")
        print(f"## {category}")
        print(f"{'#'*80}")

        for name, url in feeds.items():
            try:
                analyze_feed(name, url)
            except Exception as e:
                print(f"\n❌ Error parsing {name}: {e}")

    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print("""
RSS feeds provide varying levels of content:
- Some give full article text
- Most give 200-500 char summaries
- Some only give headlines

For filtering with Claude:
- ✅ Feeds with summaries (200+ chars) work great
- ⚠️  Headline-only feeds need article fetching
- 💰 Fetching full articles costs bandwidth + Claude tokens

Recommendation: Start with feeds that provide good summaries.
""")

if __name__ == '__main__':
    main()
