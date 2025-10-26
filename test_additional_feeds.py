#!/usr/bin/env python3
"""
Test additional international news sources for diversity.
"""

import feedparser
from datetime import datetime
import re

# Additional feeds to test for better diversity
FEEDS = {
    'The Economist': {
        'The Economist': 'https://www.economist.com/rss',
        'The Economist World': 'https://www.economist.com/sections/world/rss.xml',
        'The Economist International': 'https://www.economist.com/international/rss.xml',
    },
    'European Perspectives': {
        'France 24 English': 'https://www.france24.com/en/rss',
        'Deutsche Welle English': 'https://rss.dw.com/xml/rss-en-all',
        'Euronews': 'https://www.euronews.com/rss',
    },
    'Asian/Middle East': {
        'South China Morning Post': 'https://www.scmp.com/rss/91/feed',
        'The Japan Times': 'https://www.japantimes.co.jp/feed/',
        'Al Jazeera English': 'https://www.aljazeera.com/xml/rss/all.xml',
    },
    'Business/Economics': {
        'Financial Times': 'https://www.ft.com/?format=rss',
        'Bloomberg': 'https://www.bloomberg.com/feed/podcast/bloomberg-surveillance.xml',
        'Reuters Business': 'http://feeds.reuters.com/reuters/businessNews',
    },
}

def test_and_analyze_feed(name, url):
    """Test feed accessibility and analyze content depth."""
    try:
        # Test HTTP access
        import requests
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return {
                'accessible': False,
                'status': response.status_code,
                'entries': 0,
                'avg_content': 0,
            }

        # Parse with feedparser
        feed = feedparser.parse(url)

        if not feed.entries:
            return {
                'accessible': False,
                'status': 200,
                'entries': 0,
                'avg_content': 0,
                'note': 'No entries found'
            }

        # Analyze content
        content_lengths = []
        for entry in feed.entries:
            content = None
            if 'content' in entry and entry.content:
                content = entry.content[0].value
            elif 'summary' in entry:
                content = entry.summary
            elif 'description' in entry:
                content = entry.description

            if content:
                # Strip HTML
                clean = re.sub('<[^<]+?>', '', content)
                content_lengths.append(len(clean))

        avg_content = sum(content_lengths) / len(content_lengths) if content_lengths else 0

        # Get sample title
        sample_title = feed.entries[0].get('title', 'NO TITLE')[:60] if feed.entries else ''

        return {
            'accessible': True,
            'status': 200,
            'entries': len(feed.entries),
            'avg_content': int(avg_content),
            'sample_title': sample_title,
            'feed_type': feed.version if hasattr(feed, 'version') else 'unknown',
        }

    except Exception as e:
        return {
            'accessible': False,
            'error': str(e)[:50],
            'entries': 0,
            'avg_content': 0,
        }

def categorize_content(avg_length):
    """Categorize content depth."""
    if avg_length < 150:
        return "❌ Headlines only"
    elif avg_length < 300:
        return "⚠️  Minimal summaries"
    elif avg_length < 600:
        return "✅ Short summaries"
    elif avg_length < 1500:
        return "✅✅ Good summaries"
    else:
        return "✅✅✅ Full/Long text"

def main():
    print(f"ADDITIONAL INTERNATIONAL FEEDS TEST")
    print(f"Timestamp: {datetime.now().isoformat()}\n")
    print(f"Testing for better geographic and perspective diversity...\n")

    all_results = []

    for category, feeds in FEEDS.items():
        print(f"\n{'='*80}")
        print(f"## {category}")
        print(f"{'='*80}")

        for name, url in feeds.items():
            print(f"\nTesting: {name}")
            print(f"URL: {url}")

            result = test_and_analyze_feed(name, url)
            result['name'] = name
            result['category'] = category
            all_results.append(result)

            if result['accessible']:
                content_cat = categorize_content(result['avg_content'])
                print(f"✅ Status: {result['status']}")
                print(f"   Entries: {result['entries']}")
                print(f"   Avg content: {result['avg_content']} chars - {content_cat}")
                if 'sample_title' in result:
                    print(f"   Sample: {result['sample_title']}")
            else:
                print(f"❌ Failed: {result.get('error', result.get('note', 'HTTP ' + str(result.get('status', 'unknown'))))}")

    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY - RECOMMENDED ADDITIONS")
    print(f"{'='*80}\n")

    # Filter good feeds (accessible + decent content)
    good_feeds = [r for r in all_results if r['accessible'] and r['avg_content'] >= 300]

    if good_feeds:
        print("Feeds with good content (300+ chars):\n")
        for feed in good_feeds:
            content_cat = categorize_content(feed['avg_content'])
            print(f"  ✅ {feed['name']:30s} ({feed['entries']:3d} entries, {feed['avg_content']:4d} chars) {content_cat}")
            print(f"     └─ {feed['category']}")
    else:
        print("⚠️  No feeds with substantial content found.")

    # Show accessible but minimal content
    minimal_feeds = [r for r in all_results if r['accessible'] and r['avg_content'] < 300]
    if minimal_feeds:
        print(f"\n\nAccessible but minimal content (need article fetching):\n")
        for feed in minimal_feeds:
            print(f"  ⚠️  {feed['name']:30s} ({feed['entries']:3d} entries, {feed['avg_content']:4d} chars)")

if __name__ == '__main__':
    main()
