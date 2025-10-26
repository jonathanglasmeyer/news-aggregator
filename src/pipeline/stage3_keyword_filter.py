#!/usr/bin/env python3
"""
Stage 3: Keyword-Based Blacklist Filtering (Local)
===================================================

Applies keyword-based blacklist filtering directly in GitHub Actions.
No remote service or embedding model needed.

Input: data/deduplicated/YYYYMMDD_HHMMSS.json
Output: data/filtered_keywords/YYYYMMDD_HHMMSS.json
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add services to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'services'))
from filter_logic import simple_filter


def main():
    if len(sys.argv) < 2:
        print("Usage: python stage3_keyword_filter.py <deduplicated_json_file>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        sys.exit(1)

    print("="*80)
    print("STAGE 3: KEYWORD-BASED BLACKLIST FILTERING")
    print("="*80)
    print(f"\n📂 Input: {input_file}")

    # Load deduplicated articles
    with open(input_file, 'r') as f:
        data = json.load(f)

    articles = data.get('articles', [])
    print(f"📊 Loaded: {len(articles)} deduplicated articles")

    if not articles:
        print("⚠️  No articles to filter (empty input)")
        sys.exit(0)

    # Apply keyword filter
    print("\n🔍 Applying keyword-based blacklist filter...")
    kept_articles, stats = simple_filter(articles)

    print(f"\n✅ Filtering complete:")
    print(f"   - Input: {stats['input_count']} articles")
    print(f"   - Kept: {stats['filtered_count']} articles")
    print(f"   - Blocked: {stats['blacklisted_count']} articles ({stats['reduction_rate']})")

    if stats['top_blacklist_reasons']:
        print(f"\n🔝 Top blacklist reasons:")
        for keyword, count in list(stats['top_blacklist_reasons'].items())[:5]:
            print(f"   - '{keyword}': {count} articles")

    # Prepare output
    output_dir = Path('data/filtered_keywords')
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f"{timestamp}.json"

    output_data = {
        'metadata': {
            'timestamp': timestamp,
            'input_file': str(input_file),
            'stage': 'keyword_filter',
            'stats': stats
        },
        'articles': kept_articles
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 Saved: {output_file}")
    print(f"📈 {len(kept_articles)} articles ready for Stage 4 (Claude filtering)")


if __name__ == '__main__':
    main()
