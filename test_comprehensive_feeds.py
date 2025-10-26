#!/usr/bin/env python3
"""
Test comprehensive news feed sources.
Focus on wire services, factual reporting, minimal opinion pieces.
"""

import requests
from datetime import datetime
import re

# Comprehensive feed list organized by category
FEEDS = {
    'Wire Services / Agencies': {
        'Reuters World': 'https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best',
        'Reuters Top News': 'http://feeds.reuters.com/reuters/topNews',
        'AP News Top': 'https://feeds.apnews.com/rss/apf-topnews',
        'AFP English': 'https://www.afp.com/en/rss',
    },
    'German News (Factual)': {
        'Tagesschau': 'https://www.tagesschau.de/xml/rss2/',
        'Deutschlandfunk': 'https://www.deutschlandfunk.de/die-nachrichten.353.de.rss',
        'Tagesschau Ausland': 'https://www.tagesschau.de/ausland/index~rss2.xml',
    },
    'International News (Quality)': {
        'BBC World': 'http://feeds.bbci.co.uk/news/world/rss.xml',
        'BBC Top Stories': 'http://feeds.bbci.co.uk/news/rss.xml',
        'The Guardian World': 'https://www.theguardian.com/world/rss',
        'Al Jazeera': 'https://www.aljazeera.com/xml/rss/all.xml',
    },
    'Tech News (Quality, 4-5 sources)': {
        'Ars Technica': 'http://feeds.arstechnica.com/arstechnica/index',
        'The Verge': 'https://www.theverge.com/rss/index.xml',
        'Heise Online': 'https://www.heise.de/rss/heise-atom.xml',
        'The Register': 'https://www.theregister.com/headlines.atom',
        'Hacker News': 'https://news.ycombinator.com/rss',
    },
}

def test_feed(name, url):
    """Test if feed is accessible without authentication."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)

        status = "✅" if response.status_code == 200 else f"❌ {response.status_code}"

        # Check if it's valid RSS/XML/Atom
        content_preview = response.text[:1000].lower()
        is_feed = any(tag in content_preview for tag in ['<?xml', '<rss', '<feed', '<atom'])

        if response.status_code == 200 and not is_feed:
            status = "⚠️  200 but not RSS/XML"

        # Get size
        size = len(response.content) // 1024  # KB

        # Try to extract first article title
        first_article = ""
        if is_feed and response.status_code == 200:
            titles = re.findall(r'<title>(.*?)</title>', response.text)
            if len(titles) > 1:
                first_article = titles[1][:80]

        return {
            'status': status,
            'size': size,
            'sample': first_article,
            'success': response.status_code == 200 and is_feed
        }

    except requests.exceptions.Timeout:
        return {'status': '❌ Timeout', 'size': 0, 'sample': '', 'success': False}
    except requests.exceptions.RequestException as e:
        return {'status': f'❌ {type(e).__name__}', 'size': 0, 'sample': '', 'success': False}

def main():
    print(f"\n{'='*80}")
    print("COMPREHENSIVE NEWS FEED TEST")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"{'='*80}\n")

    all_results = {}
    total_tested = 0
    total_success = 0

    for category, feeds in FEEDS.items():
        print(f"\n## {category}")
        print(f"{'-'*80}")

        category_results = {}
        for name, url in feeds.items():
            total_tested += 1
            result = test_feed(name, url)
            category_results[name] = result

            if result['success']:
                total_success += 1

            print(f"{result['status']:20s} {name:30s} ({result['size']:4d} KB)")
            if result['sample']:
                print(f"{'':20s} └─ {result['sample']}")

        all_results[category] = category_results

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total feeds tested: {total_tested}")
    print(f"Successfully accessible: {total_success}/{total_tested} ({total_success/total_tested*100:.1f}%)")

    print("\n### Recommended Sources (accessible feeds):")
    for category, feeds in all_results.items():
        working_feeds = [name for name, result in feeds.items() if result['success']]
        if working_feeds:
            print(f"\n{category}:")
            for feed in working_feeds:
                print(f"  ✅ {feed}")

    # Failed feeds
    failed = []
    for category, feeds in all_results.items():
        for name, result in feeds.items():
            if not result['success']:
                failed.append(f"{name} ({category})")

    if failed:
        print(f"\n### Failed/Inaccessible feeds:")
        for feed in failed:
            print(f"  ❌ {feed}")

if __name__ == '__main__':
    main()
