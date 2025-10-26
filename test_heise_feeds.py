#!/usr/bin/env python3
"""
Test different Heise RSS feeds to find more targeted content.
Goal: News only, no product tests, no workshop announcements.
"""

import feedparser
from datetime import datetime, timedelta
import re

# Different Heise RSS feeds to test
HEISE_FEEDS = {
    'heise-atom.xml (all)': 'https://www.heise.de/rss/heise-atom.xml',
    'heise.rdf (all RDF)': 'https://www.heise.de/rss/heise.rdf',
    'newsticker': 'https://www.heise.de/newsticker/heise-atom.xml',
    'top': 'https://www.heise.de/rss/heise-top-atom.xml',
    'security': 'https://www.heise.de/security/rss/news-atom.xml',
    'developer': 'https://www.heise.de/developer/rss/news-atom.xml',
    'telepolis': 'https://www.heise.de/tp/rss/news-atom.xml',
}

def categorize_article(title):
    """Categorize Heise article."""
    title_lower = title.lower()

    # Filter out unwanted categories
    if any(word in title_lower for word in ['workshop', 'webinar', 'schulung', 'seminar', 'kurs']):
        return 'Workshop/Training (❌ unwanted)'

    if any(word in title_lower for word in ['test:', 'im test', 'ausprobiert', 'review']):
        return 'Product Test (❌ unwanted)'

    if any(word in title_lower for word in ['c\'t fotografie', 'ix-', 'heise-angebot', 'jetzt verfügbar']):
        return 'Heise Magazines (❌ unwanted)'

    if any(word in title_lower for word in ['saugroboter', 'mähroboter', 'staubsauger', 'waschmaschine']):
        return 'Consumer Appliances (❌ unwanted)'

    if any(word in title_lower for word in ['sap ', 'salesforce', 'oracle database', 'it-grundschutz']):
        return 'Enterprise IT (❌ unwanted)'

    # Wanted categories
    if any(word in title_lower for word in ['sicherheitslücke', 'schwachstelle', 'patch', 'exploit', 'cyberangriff', 'datenleck']):
        return 'Security (✅ wanted)'

    if any(word in title_lower for word in ['ki ', ' ai ', 'künstliche intelligenz', 'machine learning', 'chatgpt', 'llm']):
        return 'AI/ML (✅ wanted)'

    if any(word in title_lower for word in ['bundestag', 'eu-', 'dsgvo', 'datenschutz', 'gesetz', 'regulierung']):
        return 'Policy/Regulation (✅ wanted)'

    if any(word in title_lower for word in ['linux', 'windows', 'macos', 'software', 'update', 'release']):
        return 'Software News (✅ wanted)'

    if any(word in title_lower for word in ['chip', 'prozessor', 'nvidia', 'amd', 'intel', 'qualcomm']):
        return 'Hardware News (✅ wanted)'

    return 'Other'

def analyze_feed(name, url):
    """Analyze a Heise RSS feed."""
    try:
        feed = feedparser.parse(url)

        if not feed.entries:
            return None

        # Get last 7 days
        cutoff = datetime.now() - timedelta(days=7)
        recent = []

        for entry in feed.entries:
            if 'published_parsed' in entry and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
                if pub_date < cutoff:
                    continue

            title = entry.get('title', '')
            category = categorize_article(title)

            recent.append({
                'title': title,
                'category': category,
            })

        # Count categories
        from collections import defaultdict
        cat_counts = defaultdict(int)
        for article in recent:
            cat_counts[article['category']] += 1

        # Calculate unwanted percentage
        unwanted = sum(count for cat, count in cat_counts.items() if '❌' in cat)
        wanted = sum(count for cat, count in cat_counts.items() if '✅' in cat)
        other = sum(count for cat, count in cat_counts.items() if '❌' not in cat and '✅' not in cat)

        return {
            'total': len(recent),
            'wanted': wanted,
            'unwanted': unwanted,
            'other': other,
            'categories': dict(cat_counts),
            'sample_titles': [a['title'] for a in recent[:5]],
        }

    except Exception as e:
        return {'error': str(e)}

def main():
    print(f"{'='*80}")
    print("HEISE RSS FEED COMPARISON")
    print(f"{'='*80}\n")
    print("Testing different Heise feeds to avoid product tests, workshops, etc.\n")

    results = {}

    for name, url in HEISE_FEEDS.items():
        print(f"\n{'='*80}")
        print(f"## {name}")
        print(f"{'='*80}")
        print(f"URL: {url}\n")

        result = analyze_feed(name, url)

        if result is None:
            print("❌ No entries found")
            continue

        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            continue

        results[name] = result

        total = result['total']
        wanted = result['wanted']
        unwanted = result['unwanted']
        other = result['other']

        wanted_pct = (wanted / total * 100) if total else 0
        unwanted_pct = (unwanted / total * 100) if total else 0

        print(f"Articles (7 days): {total}")
        print(f"  ✅ Wanted:   {wanted:3d} ({wanted_pct:4.1f}%)")
        print(f"  ❌ Unwanted: {unwanted:3d} ({unwanted_pct:4.1f}%)")
        print(f"  ⚪ Other:    {other:3d} ({(other/total*100):4.1f}%)")

        print(f"\nCategory breakdown:")
        for category, count in sorted(result['categories'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {category:40s} {count:3d}")

        print(f"\nSample titles:")
        for i, title in enumerate(result['sample_titles'], 1):
            print(f"  [{i}] {title[:70]}")

    # Recommendation
    print(f"\n\n{'='*80}")
    print("RECOMMENDATION")
    print(f"{'='*80}\n")

    best_feed = None
    best_score = 0

    for name, result in results.items():
        if 'error' in result or result['total'] == 0:
            continue

        # Score: wanted% - unwanted%, prefer higher article counts
        wanted_pct = (result['wanted'] / result['total']) * 100
        unwanted_pct = (result['unwanted'] / result['total']) * 100
        score = wanted_pct - unwanted_pct

        # Bonus for having decent volume (30-80 articles/week)
        if 30 <= result['total'] <= 80:
            score += 10

        print(f"{name:30s} Score: {score:5.1f} ({result['total']:3d} articles, {wanted_pct:.0f}% wanted, {unwanted_pct:.0f}% unwanted)")

        if score > best_score:
            best_score = score
            best_feed = name

    if best_feed:
        print(f"\n✅ BEST FEED: {best_feed}")
        print(f"   Use: {HEISE_FEEDS[best_feed]}")
    else:
        print("\n⚠️  No clearly better feed found")

if __name__ == '__main__':
    main()
