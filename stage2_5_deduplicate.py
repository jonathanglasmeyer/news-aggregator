#!/usr/bin/env python3
"""
Stage 2.5: Deduplicate Articles
================================

Removes articles that were already processed in the last 7 days.

Input:  data/aggregated/YYYYMMDD_HHMMSS.json
Output: data/deduplicated/YYYYMMDD_HHMMSS.json

Usage:
    python stage2_5_deduplicate.py data/aggregated/20251026_135254.json
    python stage2_5_deduplicate.py  # Uses latest aggregated file
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

DATA_DIR = Path(__file__).parent / 'data'
AGGREGATED_DIR = DATA_DIR / 'aggregated'
DEDUPLICATED_DIR = DATA_DIR / 'deduplicated'
DEDUPLICATED_DIR.mkdir(parents=True, exist_ok=True)

LOOKBACK_DAYS = 7


def load_aggregated_file(file_path: Path) -> list[dict]:
    """Load aggregated articles from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('articles', [])


def get_recent_files(days: int = LOOKBACK_DAYS) -> list[Path]:
    """Get all aggregated files from the last N days"""
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_files = []

    for file_path in sorted(AGGREGATED_DIR.glob('*.json'), reverse=True):
        # Extract date from filename (YYYYMMDD_HHMMSS.json)
        try:
            date_str = file_path.stem.split('_')[0]
            file_date = datetime.strptime(date_str, '%Y%m%d')

            if file_date >= cutoff_date:
                recent_files.append(file_path)
            else:
                # Files are sorted by date, so we can stop here
                break
        except (ValueError, IndexError):
            # Skip files with unexpected naming
            continue

    return recent_files


def extract_urls_from_history(files: list[Path]) -> set[str]:
    """Extract all URLs from historical files"""
    urls = set()

    for file_path in files:
        try:
            articles = load_aggregated_file(file_path)
            for article in articles:
                if 'link' in article and article['link']:
                    urls.add(article['link'])
        except Exception as e:
            print(f"⚠️  Fehler beim Lesen von {file_path.name}: {e}")
            continue

    return urls


def deduplicate_articles(articles: list[dict], historical_urls: set[str]) -> tuple[list[dict], list[dict]]:
    """
    Remove articles with URLs that appear in historical data.
    Returns (new_articles, duplicate_articles)
    """
    new_articles = []
    duplicate_articles = []

    for article in articles:
        url = article.get('link')  # Changed from 'url' to 'link'

        if not url:
            # Keep articles without URL (shouldn't happen, but safe fallback)
            new_articles.append(article)
        elif url in historical_urls:
            duplicate_articles.append(article)
        else:
            new_articles.append(article)

    return new_articles, duplicate_articles


def save_deduplicated(articles: list[dict], output_path: Path, stats: dict):
    """Save deduplicated articles to JSON file"""
    output_data = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'deduplicated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'lookback_days': LOOKBACK_DAYS,
            'total_input': stats['total_input'],
            'duplicates_removed': stats['duplicates_removed'],
            'new_articles': stats['new_articles'],
            'deduplication_rate': f"{stats['deduplication_rate']:.1f}%",
            'historical_files_checked': stats['historical_files_checked']
        },
        'articles': articles
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)


def main():
    print("\n" + "="*80)
    print("STAGE 2.5: DEDUPLICATION")
    print("="*80 + "\n")

    # Determine input file
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    else:
        # Use latest aggregated file
        aggregated_files = sorted(AGGREGATED_DIR.glob('*.json'), reverse=True)
        if not aggregated_files:
            print("❌ Keine aggregierten Dateien gefunden in data/aggregated/")
            sys.exit(1)
        input_path = aggregated_files[0]

    if not input_path.exists():
        print(f"❌ Datei nicht gefunden: {input_path}")
        sys.exit(1)

    print(f"📂 Input: {input_path.name}")

    # Load current articles
    print(f"\n⏳ Lade Artikel aus {input_path.name}...")
    articles = load_aggregated_file(input_path)
    total_input = len(articles)
    print(f"   Geladen: {total_input} Artikel")

    # Get recent files for deduplication
    print(f"\n⏳ Suche historische Dateien (letzte {LOOKBACK_DAYS} Tage)...")
    recent_files = get_recent_files(LOOKBACK_DAYS)

    # Exclude current file from history
    recent_files = [f for f in recent_files if f != input_path]

    print(f"   Gefunden: {len(recent_files)} Dateien")
    if recent_files:
        for f in recent_files[:5]:  # Show first 5
            print(f"   - {f.name}")
        if len(recent_files) > 5:
            print(f"   ... und {len(recent_files) - 5} weitere")

    # Extract URLs from history
    print(f"\n⏳ Extrahiere URLs aus Historie...")
    historical_urls = extract_urls_from_history(recent_files)
    print(f"   {len(historical_urls)} eindeutige URLs in Historie")

    # Deduplicate
    print(f"\n⏳ Dedupliziere Artikel...")
    new_articles, duplicate_articles = deduplicate_articles(articles, historical_urls)

    new_count = len(new_articles)
    duplicate_count = len(duplicate_articles)
    dedup_rate = (duplicate_count / total_input * 100) if total_input > 0 else 0

    # Stats
    stats = {
        'total_input': total_input,
        'new_articles': new_count,
        'duplicates_removed': duplicate_count,
        'deduplication_rate': dedup_rate,
        'historical_files_checked': len(recent_files)
    }

    print(f"\n📊 Deduplizierungs-Statistik:")
    print(f"   Input:     {total_input} Artikel")
    print(f"   Neu:       {new_count} Artikel")
    print(f"   Duplikate: {duplicate_count} Artikel ({dedup_rate:.1f}%)")

    # Show some duplicate examples
    if duplicate_articles:
        print(f"\n📋 Beispiel-Duplikate (erste 3):")
        for i, article in enumerate(duplicate_articles[:3], 1):
            title = article.get('title', 'Ohne Titel')[:60]
            print(f"   {i}. {title}...")

    # Save deduplicated articles
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = DEDUPLICATED_DIR / f'{timestamp}.json'

    print(f"\n💾 Speichere deduplizierte Artikel...")
    save_deduplicated(new_articles, output_path, stats)
    print(f"   ✅ Gespeichert: {output_path.name}")

    print("\n" + "="*80)
    print(f"✅ DEDUPLIZIERUNG ABGESCHLOSSEN")
    print(f"   {new_count} neue Artikel → {output_path}")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
