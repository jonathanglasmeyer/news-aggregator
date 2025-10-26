#!/usr/bin/env python3
"""
Test script for embedding-based blacklist filtering
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'services'))

from filter_logic import benchmark_filters
from FlagEmbedding import BGEM3FlagModel


def load_sample_articles():
    """Load some recent deduplicated articles for testing"""
    dedup_files = sorted(Path('data/deduplicated').glob('*.json'), reverse=True)
    if not dedup_files:
        print("❌ No deduplicated files found")
        sys.exit(1)

    # Load latest file
    with open(dedup_files[0], 'r') as f:
        data = json.load(f)

    articles = data.get('articles', [])
    print(f"📂 Loaded {len(articles)} articles from {dedup_files[0].name}")
    return articles


def main():
    print("="*80)
    print("EMBEDDING FILTER TEST")
    print("="*80)

    # Load sample articles
    articles = load_sample_articles()

    if not articles:
        print("❌ No articles to test")
        return

    # Load embedding model
    print("\n🔄 Loading embedding model BAAI/bge-m3...")
    model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
    print("✅ Model loaded")

    # Run benchmark
    results = benchmark_filters(articles, model)

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print(f"\n✅ Benchmark completed successfully")
    print(f"   - Keyword filter kept: {results['keyword_stats']['filtered_count']} articles")
    print(f"   - Embedding filter kept: {results['embedding_stats']['filtered_count']} articles")
    print(f"   - Agreement: {results['kept_by_both']} articles")
    print(f"   - Disagreement: {results['only_keyword'] + results['only_embedding']} articles")


if __name__ == '__main__':
    main()
