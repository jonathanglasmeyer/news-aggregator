#!/usr/bin/env python3
"""
Compare tech news sources: Does Heise have unique content
or just repeat US tech news from Ars/Verge?
"""

import feedparser
from datetime import datetime, timedelta
from collections import defaultdict
import re

TECH_FEEDS = {
    'Ars Technica': 'http://feeds.arstechnica.com/arstechnica/index',
    'The Verge': 'https://www.theverge.com/rss/index.xml',
    'Heise Online': 'https://www.heise.de/rss/heise-atom.xml',
}

def parse_date(entry):
    """Parse published date from entry."""
    if 'published_parsed' in entry and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])
    elif 'updated_parsed' in entry and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6])
    return None

def extract_keywords(title):
    """Extract significant keywords from title."""
    # Remove common words
    stopwords = {'the', 'a', 'an', 'in', 'on', 'at', 'for', 'to', 'of', 'and', 'or', 'with', 'from', 'is', 'are', 'was', 'were', 'has', 'have', 'be'}

    # Normalize and split
    title_lower = title.lower()
    # Remove punctuation
    title_clean = re.sub(r'[^\w\s]', ' ', title_lower)
    words = title_clean.split()

    # Filter stopwords and short words
    keywords = [w for w in words if w not in stopwords and len(w) > 3]

    return set(keywords)

def categorize_article(title):
    """Categorize article by topic."""
    title_lower = title.lower()

    # German/European specific
    if any(word in title_lower for word in ['bundeswehr', 'bundestag', 'deutschland', 'europa', 'eu-', 'dsgvo', 'datenschutz', 'bsi']):
        return 'German/EU Politics/Policy'

    # Big tech companies
    if any(word in title_lower for word in ['google', 'apple', 'microsoft', 'meta', 'amazon', 'facebook', 'openai', 'anthropic']):
        return 'Big Tech Companies'

    # AI/ML
    if any(word in title_lower for word in ['ai ', ' ai,', 'artificial intelligence', 'machine learning', 'chatgpt', 'llm', 'claude', 'gemini']):
        return 'AI/ML'

    # Security/Privacy
    if any(word in title_lower for word in ['security', 'hack', 'breach', 'vulnerability', 'exploit', 'malware', 'cyber']):
        return 'Security/Privacy'

    # Hardware
    if any(word in title_lower for word in ['processor', 'cpu', 'gpu', 'nvidia', 'amd', 'intel', 'chip', 'hardware']):
        return 'Hardware'

    # Software/Dev
    if any(word in title_lower for word in ['linux', 'windows', 'macos', 'software', 'developer', 'programming', 'code']):
        return 'Software/Dev'

    # Gaming
    if any(word in title_lower for word in ['game', 'gaming', 'playstation', 'xbox', 'nintendo', 'steam']):
        return 'Gaming'

    # Space/Science
    if any(word in title_lower for word in ['space', 'nasa', 'spacex', 'rocket', 'mars', 'satellite']):
        return 'Space/Science'

    return 'Other'

def main():
    print(f"{'='*80}")
    print(f"TECH NEWS CONTENT OVERLAP ANALYSIS")
    print(f"{'='*80}\n")
    print("Comparing Heise vs. Ars Technica/The Verge...")
    print("Question: Does Heise have unique content?\n")

    all_articles = defaultdict(list)

    # Fetch all feeds
    for name, url in TECH_FEEDS.items():
        print(f"Fetching {name}...", end=" ", flush=True)
        feed = feedparser.parse(url)

        cutoff = datetime.now() - timedelta(days=7)

        for entry in feed.entries:
            pub_date = parse_date(entry)
            if pub_date and pub_date < cutoff:
                continue

            title = entry.get('title', '')
            keywords = extract_keywords(title)
            category = categorize_article(title)

            all_articles[name].append({
                'title': title,
                'keywords': keywords,
                'category': category,
                'date': pub_date,
            })

        print(f"✅ {len(all_articles[name])} articles")

    # Category breakdown per source
    print(f"\n{'='*80}")
    print("CATEGORY BREAKDOWN")
    print(f"{'='*80}\n")

    for source, articles in all_articles.items():
        print(f"## {source} ({len(articles)} articles)")

        category_counts = defaultdict(int)
        for article in articles:
            category_counts[article['category']] += 1

        # Sort by count
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(articles)) * 100
            print(f"   {category:30s} {count:3d} ({percentage:4.1f}%)")
        print()

    # Find keyword overlap
    print(f"{'='*80}")
    print("TOPIC OVERLAP ANALYSIS")
    print(f"{'='*80}\n")

    heise_articles = all_articles['Heise Online']
    us_articles = all_articles['Ars Technica'] + all_articles['The Verge']

    # Check how many Heise articles have similar topics to US sources
    overlapping = 0
    unique_heise = []

    for heise_article in heise_articles:
        heise_keywords = heise_article['keywords']

        # Check if any US article shares 2+ keywords
        has_overlap = False
        for us_article in us_articles:
            shared_keywords = heise_keywords & us_article['keywords']
            if len(shared_keywords) >= 2:
                has_overlap = True
                break

        if has_overlap:
            overlapping += 1
        else:
            unique_heise.append(heise_article)

    overlap_percentage = (overlapping / len(heise_articles)) * 100 if heise_articles else 0
    unique_percentage = 100 - overlap_percentage

    print(f"Heise articles with topic overlap to Ars/Verge: {overlapping}/{len(heise_articles)} ({overlap_percentage:.1f}%)")
    print(f"Heise articles with UNIQUE topics: {len(unique_heise)}/{len(heise_articles)} ({unique_percentage:.1f}%)")

    # Show sample unique Heise articles
    print(f"\n### Sample UNIQUE Heise topics (first 15):")
    for i, article in enumerate(unique_heise[:15], 1):
        print(f"[{i:2d}] {article['title'][:75]}")
        print(f"     Category: {article['category']}")

    # Show sample overlapping topics
    print(f"\n### Sample OVERLAPPING topics:")
    overlap_samples = []
    for heise_article in heise_articles:
        if len(overlap_samples) >= 5:
            break

        heise_keywords = heise_article['keywords']
        for us_article in us_articles:
            shared = heise_keywords & us_article['keywords']
            if len(shared) >= 2:
                overlap_samples.append({
                    'heise': heise_article['title'][:60],
                    'us': us_article['title'][:60],
                    'shared': shared,
                })
                break

    for i, sample in enumerate(overlap_samples, 1):
        print(f"\n[{i}] Heise: {sample['heise']}")
        print(f"    US:    {sample['us']}")
        print(f"    Shared keywords: {', '.join(list(sample['shared'])[:5])}")

    # Conclusion
    print(f"\n\n{'='*80}")
    print("CONCLUSION")
    print(f"{'='*80}\n")

    if unique_percentage > 60:
        print(f"✅ KEEP HEISE - {unique_percentage:.0f}% unique content")
        print(f"   Heise covers different topics (likely German/EU tech, policy, etc.)")
    elif unique_percentage > 40:
        print(f"⚠️  MAYBE KEEP - {unique_percentage:.0f}% unique content")
        print(f"   Moderate overlap, but still substantial unique coverage")
    else:
        print(f"❌ DROP HEISE - Only {unique_percentage:.0f}% unique content")
        print(f"   Mostly overlaps with US tech news sources")

    print(f"\nNote: Unique topics likely include:")
    heise_only_categories = defaultdict(int)
    for article in unique_heise:
        heise_only_categories[article['category']] += 1

    for category, count in sorted(heise_only_categories.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  - {category} ({count} articles)")

if __name__ == '__main__':
    main()
