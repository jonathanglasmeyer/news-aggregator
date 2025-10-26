#!/usr/bin/env python3
"""
Daily Fetch: Fetch RSS feeds and save daily snapshot.
Run daily via GitHub Actions cron.
Saves to data/raw/daily/YYYY-MM-DD.json
"""

import feedparser
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path
# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from feeds import get_all_feeds


def strip_html(text):
    """Remove HTML tags from text."""
    import re
    return re.sub('<[^<]+?>', '', text)


def parse_date(entry):
    """Parse published date from RSS entry."""
    if 'published_parsed' in entry and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])
    elif 'updated_parsed' in entry and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6])
    return None


def get_content(entry):
    """Extract content from RSS entry."""
    if 'content' in entry and entry.content:
        return entry.content[0].value
    elif 'summary' in entry:
        return entry.summary
    elif 'description' in entry:
        return entry.description
    return ""


def fetch_all_articles():
    """Fetch all articles from configured feeds (no date filtering)."""
    print(f"{'='*80}")
    print(f"DAILY FETCH - {datetime.now().strftime('%Y-%m-%d')}")
    print(f"{'='*80}\n")
    print(f"Fetching RSS feeds...\n")

    all_articles = []
    feeds = get_all_feeds()

    for feed_config in feeds:
        name = feed_config['name']
        url = feed_config['url']
        category = feed_config['category']

        print(f"  {name:30s}", end=' ', flush=True)

        try:
            feed = feedparser.parse(url)

            if not feed.entries:
                print("❌ No entries")
                continue

            # Take all entries from RSS (no date filtering)
            for entry in feed.entries:
                pub_date = parse_date(entry)
                content = get_content(entry)
                clean_content = strip_html(content)

                all_articles.append({
                    'title': entry.get('title', 'NO TITLE'),
                    'link': entry.get('link', ''),
                    'published': pub_date.isoformat() if pub_date else None,
                    'content': clean_content,
                    'content_length': len(clean_content),
                    'source': name,
                    'category': category,
                })

            print(f"✅ {len(feed.entries):3d} articles")

        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}")

    return all_articles


def save_dump(articles):
    """Save articles to daily JSON dump."""
    date = datetime.now().strftime('%Y-%m-%d')
    filename = f"data/raw/daily/{date}.json"

    dump_data = {
        'date': date,
        'timestamp': datetime.now().isoformat(),
        'total_articles': len(articles),
        'articles': articles,
        'stats': {
            'by_category': {},
            'by_source': {},
        }
    }

    # Calculate stats
    for article in articles:
        category = article['category']
        source = article['source']

        dump_data['stats']['by_category'][category] = \
            dump_data['stats']['by_category'].get(category, 0) + 1
        dump_data['stats']['by_source'][source] = \
            dump_data['stats']['by_source'].get(source, 0) + 1

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(dump_data, f, indent=2, ensure_ascii=False)

    return filename


def main():
    """Main execution."""
    # Fetch articles
    articles = fetch_all_articles()

    if not articles:
        print("\n❌ No articles fetched. Exiting.")
        return

    # Save dump
    print(f"\n{'='*80}")
    print(f"SAVING DAILY DUMP")
    print(f"{'='*80}\n")

    filename = save_dump(articles)

    print(f"✅ Saved {len(articles)} articles to: {filename}\n")

    print(f"{'='*80}")
    print(f"DONE")
    print(f"{'='*80}\n")
    print(f"Daily snapshot saved. Run weekly_aggregate.py on Sunday to merge 7 days.")


if __name__ == '__main__':
    main()
