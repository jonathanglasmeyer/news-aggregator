#!/usr/bin/env python3
"""
Stage 2: Aggregate - Load last 7 daily dumps and deduplicate.
Saves to data/aggregated/ for Stage 3 filtering.
Can be run ad-hoc anytime - always processes last 7 days.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict


def load_last_7_days():
    """Load daily dumps from last 7 days."""
    print(f"{'='*80}")
    print(f"STAGE 2: AGGREGATE - Last 7 Days")
    print(f"{'='*80}\n")
    print(f"Loading daily dumps from last 7 days...\n")

    daily_dir = Path('data/raw/daily')
    all_articles = []
    loaded_dates = []

    # Get last 7 days
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        filepath = daily_dir / f"{date}.json"

        if filepath.exists():
            print(f"  {date}  ", end='', flush=True)
            with open(filepath, 'r') as f:
                data = json.load(f)
                count = len(data['articles'])
                all_articles.extend(data['articles'])
                loaded_dates.append(date)
                print(f"✅ {count:3d} articles")
        else:
            print(f"  {date}   ⚠️  Not found (skipping)")

    print(f"\nLoaded {len(all_articles)} total articles from {len(loaded_dates)} days")
    return all_articles, loaded_dates


def deduplicate_articles(articles):
    """
    Deduplicate articles by URL (primary) or title+source (fallback).
    Keep the most recent version of duplicates.
    """
    print(f"\n{'='*80}")
    print(f"DEDUPLICATION")
    print(f"{'='*80}\n")

    seen_urls = {}
    seen_title_source = {}
    duplicates = 0

    # Process in reverse chronological order (most recent first)
    # Assumes articles are already roughly sorted by date
    sorted_articles = sorted(
        articles,
        key=lambda x: x.get('published') or '1900-01-01',
        reverse=True
    )

    unique_articles = []

    for article in sorted_articles:
        url = article.get('link', '')
        title = article.get('title', '')
        source = article.get('source', '')

        # Primary dedup: by URL
        if url and url in seen_urls:
            duplicates += 1
            continue

        # Fallback dedup: by title + source
        key = (title, source)
        if key in seen_title_source:
            duplicates += 1
            continue

        # New article
        if url:
            seen_urls[url] = True
        seen_title_source[key] = True
        unique_articles.append(article)

    print(f"Input articles:      {len(articles)}")
    print(f"Unique articles:     {len(unique_articles)}")
    print(f"Duplicates removed:  {duplicates}")
    print(f"Dedup rate:          {(duplicates/len(articles)*100):.1f}%")

    return unique_articles


def save_aggregated(articles, loaded_dates):
    """Save aggregated articles to data/aggregated/."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    week = datetime.now().strftime('%Y-W%U')  # For metadata only
    filename = f"data/aggregated/{timestamp}.json"

    # Calculate stats
    stats = {
        'by_category': defaultdict(int),
        'by_source': defaultdict(int),
        'by_day': defaultdict(int),
    }

    for article in articles:
        stats['by_category'][article['category']] += 1
        stats['by_source'][article['source']] += 1
        if article.get('published'):
            day = article['published'][:10]
            stats['by_day'][day] += 1

    dump_data = {
        'week': week,
        'timestamp': datetime.now().isoformat(),
        'date_range': {
            'start': min(loaded_dates) if loaded_dates else None,
            'end': max(loaded_dates) if loaded_dates else None,
        },
        'days_included': len(loaded_dates),
        'total_articles': len(articles),
        'articles': articles,
        'stats': {
            'by_category': dict(stats['by_category']),
            'by_source': dict(stats['by_source']),
            'by_day': dict(stats['by_day']),
        }
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(dump_data, f, indent=2, ensure_ascii=False)

    return filename


def print_stats(filename):
    """Print statistics about the weekly aggregate."""
    print(f"\n{'='*80}")
    print(f"STATISTICS")
    print(f"{'='*80}\n")

    with open(filename, 'r') as f:
        data = json.load(f)

    print(f"Week: {data['week']}")
    print(f"Date range: {data['date_range']['start']} to {data['date_range']['end']}")
    print(f"Days included: {data['days_included']}/7")
    print(f"Total articles: {data['total_articles']}\n")

    print("By category:")
    for category, count in sorted(data['stats']['by_category'].items()):
        pct = (count / data['total_articles']) * 100
        print(f"  {category:20s} {count:3d} ({pct:4.1f}%)")

    print(f"\nBy day:")
    for day in sorted(data['stats']['by_day'].keys(), reverse=True):
        count = data['stats']['by_day'][day]
        pct = (count / data['total_articles']) * 100
        bar = '█' * int(pct / 3)
        print(f"  {day}  {count:3d} ({pct:4.1f}%) {bar}")

    print(f"\nTop sources:")
    sorted_sources = sorted(
        data['stats']['by_source'].items(),
        key=lambda x: x[1],
        reverse=True
    )
    for source, count in sorted_sources[:10]:
        pct = (count / data['total_articles']) * 100
        print(f"  {source:30s} {count:3d} ({pct:4.1f}%)")


def main():
    """Main execution."""
    # Load last 7 days
    articles, loaded_dates = load_last_7_days()

    if not articles:
        print("\n❌ No articles loaded. Exiting.")
        return

    # Deduplicate
    unique_articles = deduplicate_articles(articles)

    # Save aggregated
    print(f"\n{'='*80}")
    print(f"SAVING AGGREGATED DATA")
    print(f"{'='*80}\n")

    filename = save_aggregated(unique_articles, loaded_dates)
    print(f"✅ Saved {len(unique_articles)} unique articles to: {filename}\n")

    # Print stats
    print_stats(filename)

    print(f"\n{'='*80}")
    print(f"DONE - STAGE 2")
    print(f"{'='*80}\n")
    print(f"Next step: Run stage3_filter.py {filename}")


if __name__ == '__main__':
    main()
