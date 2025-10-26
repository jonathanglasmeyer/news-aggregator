#!/usr/bin/env python3
"""
Fetch 7 days worth of articles from final feed list.
Analyze volume, content size, and estimate Claude costs.
"""

import feedparser
from datetime import datetime, timedelta
import time

# Final feed configuration - 9 feeds with good content
FEEDS = {
    'German News': {
        'Tagesschau': 'https://www.tagesschau.de/xml/rss2/',
        'Tagesschau Ausland': 'https://www.tagesschau.de/ausland/index~rss2.xml',
        'Deutschlandfunk': 'https://www.deutschlandfunk.de/die-nachrichten.353.de.rss',
    },
    'International': {
        'The Guardian World': 'https://www.theguardian.com/world/rss',
        'France 24 English': 'https://www.france24.com/en/rss',
        'South China Morning Post': 'https://www.scmp.com/rss/91/feed',
    },
    'Tech': {
        'Ars Technica': 'http://feeds.arstechnica.com/arstechnica/index',
        'The Verge': 'https://www.theverge.com/rss/index.xml',
        'Heise Online': 'https://www.heise.de/rss/heise-atom.xml',
    },
}

def parse_date(entry):
    """Parse published date from entry."""
    if 'published_parsed' in entry and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])
    elif 'updated_parsed' in entry and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6])
    return None

def get_content(entry):
    """Extract content from entry."""
    if 'content' in entry and entry.content:
        return entry.content[0].value
    elif 'summary' in entry:
        return entry.summary
    elif 'description' in entry:
        return entry.description
    return ""

def strip_html(text):
    """Simple HTML tag removal."""
    import re
    return re.sub('<[^<]+?>', '', text)

def fetch_week_articles(name, url, days=7):
    """Fetch articles from last N days."""
    print(f"Fetching: {name}...", end=" ", flush=True)

    try:
        feed = feedparser.parse(url)

        if not feed.entries:
            print("❌ No entries")
            return []

        cutoff_date = datetime.now() - timedelta(days=days)
        week_articles = []

        for entry in feed.entries:
            pub_date = parse_date(entry)

            # If no date, include it (assume recent)
            if pub_date is None:
                include = True
            else:
                include = pub_date >= cutoff_date

            if include:
                content = get_content(entry)
                clean_content = strip_html(content)

                week_articles.append({
                    'title': entry.get('title', 'NO TITLE'),
                    'link': entry.get('link', ''),
                    'published': pub_date,
                    'content': clean_content,
                    'content_length': len(clean_content),
                })

        print(f"✅ {len(week_articles)} articles")
        return week_articles

    except Exception as e:
        print(f"❌ Error: {str(e)[:50]}")
        return []

def main():
    print(f"{'='*80}")
    print(f"WEEKLY VOLUME ANALYSIS - {datetime.now().strftime('%Y-%m-%d')}")
    print(f"{'='*80}\n")
    print(f"Fetching articles from last 7 days...\n")

    all_articles = []
    feed_stats = {}

    for category, feeds in FEEDS.items():
        print(f"\n## {category}")
        print(f"{'-'*80}")

        for name, url in feeds.items():
            articles = fetch_week_articles(name, url, days=7)
            all_articles.extend(articles)

            feed_stats[name] = {
                'count': len(articles),
                'total_chars': sum(a['content_length'] for a in articles),
                'avg_chars': sum(a['content_length'] for a in articles) / len(articles) if articles else 0,
            }

    # Overall stats
    print(f"\n\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}\n")

    total_articles = len(all_articles)
    total_chars = sum(a['content_length'] for a in all_articles)

    print(f"Total articles (7 days): {total_articles}")
    print(f"Total content size: {total_chars:,} chars ({total_chars/1024:.1f} KB)")
    print(f"Average per article: {total_chars/total_articles:.0f} chars" if total_articles else "")

    # Per-feed breakdown
    print(f"\n### Per-Feed Breakdown:")
    for name, stats in feed_stats.items():
        if stats['count'] > 0:
            print(f"  {name:30s} {stats['count']:4d} articles, {stats['total_chars']:7,} chars (avg: {stats['avg_chars']:.0f})")

    # Sample articles
    print(f"\n### Sample Articles (first 10):")
    for i, article in enumerate(all_articles[:10], 1):
        pub_str = article['published'].strftime('%Y-%m-%d %H:%M') if article['published'] else 'No date'
        print(f"\n[{i}] {article['title'][:70]}")
        print(f"    {pub_str} | {article['content_length']} chars")
        print(f"    {article['content'][:150]}...")

    # Claude cost estimation
    print(f"\n\n{'='*80}")
    print(f"CLAUDE FILTERING COST ESTIMATE")
    print(f"{'='*80}\n")

    # Sonnet 4.5 pricing (AWS Bedrock as of 2024)
    # Input: $3 per 1M tokens, Output: $15 per 1M tokens
    # Rough estimate: 1 token ≈ 4 chars

    input_tokens = total_chars / 4  # article content
    input_tokens += 1000  # system prompt + instructions

    # Assume filtered output is ~20% of input (only relevant articles with summaries)
    output_tokens = input_tokens * 0.2

    input_cost = (input_tokens / 1_000_000) * 3
    output_cost = (output_tokens / 1_000_000) * 15
    total_cost_per_week = input_cost + output_cost

    print(f"Estimated tokens (input): {input_tokens:,.0f}")
    print(f"Estimated tokens (output): {output_tokens:,.0f}")
    print(f"\nCost per week:")
    print(f"  Input:  ${input_cost:.4f}")
    print(f"  Output: ${output_cost:.4f}")
    print(f"  Total:  ${total_cost_per_week:.4f}")
    print(f"\nMonthly estimate: ${total_cost_per_week * 4:.2f}")
    print(f"Yearly estimate:  ${total_cost_per_week * 52:.2f}")

    print(f"\n✅ Conclusion:")
    if total_cost_per_week < 0.10:
        print(f"   Very cheap - easily within budget")
    elif total_cost_per_week < 0.50:
        print(f"   Reasonable - well within acceptable range")
    elif total_cost_per_week < 2.00:
        print(f"   Acceptable - might want to optimize filtering")
    else:
        print(f"   Expensive - consider reducing feed count or optimizing")

if __name__ == '__main__':
    main()
