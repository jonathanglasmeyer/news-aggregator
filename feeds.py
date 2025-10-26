"""
Final RSS feed configuration for news aggregator.
10 feeds, ~307 articles/week, balanced coverage.
"""

FEEDS = {
    'German News': {
        'Tagesschau': {
            'url': 'https://www.tagesschau.de/xml/rss2/',
            'description': 'German public broadcaster, general news',
            'avg_articles_week': 40,
        },
        'Tagesschau Ausland': {
            'url': 'https://www.tagesschau.de/ausland/index~rss2.xml',
            'description': 'Tagesschau international/foreign news section',
            'avg_articles_week': 49,
        },
        'Deutschlandfunk': {
            'url': 'https://www.deutschlandfunk.de/die-nachrichten.353.de.rss',
            'description': 'German public radio news',
            'avg_articles_week': 27,
        },
    },

    'International News': {
        'The Guardian World': {
            'url': 'https://www.theguardian.com/world/rss',
            'description': 'UK newspaper, world news section',
            'avg_articles_week': 45,
        },
        'France 24 English': {
            'url': 'https://www.france24.com/en/rss',
            'description': 'French international news, European perspective',
            'avg_articles_week': 24,
        },
    },

    'Tech News': {
        'Ars Technica': {
            'url': 'http://feeds.arstechnica.com/arstechnica/index',
            'description': 'In-depth technical coverage, long-form articles',
            'avg_articles_week': 20,
        },
        'The Verge': {
            'url': 'https://www.theverge.com/rss/index.xml',
            'description': 'Broad tech coverage, consumer focus',
            'avg_articles_week': 10,
        },
        'Heise Top': {
            'url': 'https://www.heise.de/rss/heise-top-atom.xml',
            'description': 'Top German tech news stories',
            'avg_articles_week': 22,
        },
        'Heise Developer': {
            'url': 'https://www.heise.de/developer/rss/news-atom.xml',
            'description': 'German developer/software news',
            'avg_articles_week': 20,
        },
    },
}

# Flatten for easy iteration
def get_all_feeds():
    """Return flat list of all feed configs."""
    all_feeds = []
    for category, feeds in FEEDS.items():
        for name, config in feeds.items():
            all_feeds.append({
                'name': name,
                'category': category,
                **config
            })
    return all_feeds

# Summary stats
TOTAL_FEEDS = sum(len(feeds) for feeds in FEEDS.values())
ESTIMATED_ARTICLES_WEEK = sum(
    feed['avg_articles_week']
    for category in FEEDS.values()
    for feed in category.values()
)

if __name__ == '__main__':
    print(f"Feed Configuration Summary")
    print(f"{'='*60}\n")
    print(f"Total feeds: {TOTAL_FEEDS}")
    print(f"Estimated articles/week: {ESTIMATED_ARTICLES_WEEK}")
    print(f"\nBreakdown by category:\n")

    for category, feeds in FEEDS.items():
        cat_total = sum(f['avg_articles_week'] for f in feeds.values())
        print(f"{category}:")
        for name, config in feeds.items():
            pct = (config['avg_articles_week'] / ESTIMATED_ARTICLES_WEEK) * 100
            print(f"  - {name:30s} {config['avg_articles_week']:3d}/week ({pct:4.1f}%)")
        print(f"  Category total: {cat_total}/week\n")
