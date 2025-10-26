#!/usr/bin/env python3
"""
Stage 3: Embedding-based Pre-Filter (Remote)
=============================================

Calls the embedding filter service on Hetzner via SSH tunnel.
Used by GitHub Actions to filter articles without loading heavy ML models.

Usage:
    python stage3_embed_filter_remote.py data/deduplicated/20251026_145033.json
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Find project root (2 levels up from src/pipeline/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
EMBEDDED_DIR = DATA_DIR / 'embedded'
EMBEDDED_DIR.mkdir(parents=True, exist_ok=True)

HETZNER_HOST = "hetzner"
SERVICE_URL = "http://localhost:3007/filter"


def load_articles(input_path: Path) -> list[dict]:
    """Load articles from deduplicated JSON"""
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('articles', [])


def filter_via_remote_service(articles: list[dict]) -> tuple[list[dict], dict]:
    """
    Send articles to remote embedding filter service via SSH.
    Returns filtered articles and stats.
    """
    # Prepare request payload
    request_data = {
        "articles": articles
    }
    request_json = json.dumps(request_data)

    # Call service via SSH
    # We use SSH to curl localhost:3007 on the remote server
    # Use --data-binary @- to read from stdin (avoids "Argument list too long")
    ssh_command = [
        "ssh", HETZNER_HOST,
        f"curl -s -X POST {SERVICE_URL} -H 'Content-Type: application/json' --data-binary @-"
    ]

    try:
        print(f"📡 Calling remote embedding filter service...")
        result = subprocess.run(
            ssh_command,
            input=request_json,  # Pass JSON via stdin
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            raise Exception(f"SSH/curl failed: {result.stderr}")

        # Parse response
        response = json.loads(result.stdout)
        filtered_articles = response['filtered_articles']
        stats = response['stats']

        return filtered_articles, stats

    except subprocess.TimeoutExpired:
        raise Exception("Remote service call timed out after 5 minutes")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse service response: {e}\nOutput: {result.stdout}")
    except Exception as e:
        raise Exception(f"Remote service call failed: {e}")


def save_embedded(articles: list[dict], output_path: Path, stats: dict):
    """Save filtered articles to JSON file"""
    output_data = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'filtered_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'method': 'remote_embedding_service',
            'service_host': HETZNER_HOST,
            'total_input': stats['input_count'],
            'filtered_output': stats['filtered_count'],
            'blacklisted': stats['blacklisted_count'],
            'reduction_rate': stats['reduction_rate'],
            'top_blacklist_reasons': stats.get('top_blacklist_reasons', {})
        },
        'articles': articles
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)


def main():
    print("\n" + "="*80)
    print("STAGE 3: EMBEDDING FILTER (REMOTE)")
    print("="*80 + "\n")

    # Determine input file
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    else:
        # Use latest deduplicated file
        dedup_files = sorted((DATA_DIR / 'deduplicated').glob('*.json'), reverse=True)
        if not dedup_files:
            print("❌ Keine deduplizierten Dateien gefunden")
            sys.exit(1)
        input_path = dedup_files[0]

    if not input_path.exists():
        print(f"❌ Datei nicht gefunden: {input_path}")
        sys.exit(1)

    print(f"📂 Input: {input_path.name}")

    # Load articles
    print(f"\n⏳ Lade Artikel...")
    articles = load_articles(input_path)
    total_input = len(articles)
    print(f"   Geladen: {total_input} Artikel")

    # Filter via remote service
    print(f"\n📡 Filtere via Remote Service ({HETZNER_HOST})...")
    try:
        filtered_articles, stats = filter_via_remote_service(articles)
    except Exception as e:
        print(f"\n❌ Fehler beim Remote-Call: {e}")
        sys.exit(1)

    filtered_count = len(filtered_articles)

    print(f"\n📊 Filter-Statistik:")
    print(f"   Input:        {stats['input_count']} Artikel")
    print(f"   Gefiltert:    {filtered_count} Artikel")
    print(f"   Verworfen:    {stats['blacklisted_count']} Artikel ({stats['reduction_rate']})")

    if stats.get('top_blacklist_reasons'):
        print(f"\n📋 Top Blacklist-Gründe:")
        for reason, count in list(stats['top_blacklist_reasons'].items())[:5]:
            print(f"   {count:3d}x {reason}")

    # Save filtered articles
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = EMBEDDED_DIR / f'{timestamp}.json'

    print(f"\n💾 Speichere gefilterte Artikel...")
    save_embedded(filtered_articles, output_path, stats)
    print(f"   ✅ Gespeichert: {output_path.name}")

    print("\n" + "="*80)
    print(f"✅ REMOTE FILTERING ABGESCHLOSSEN")
    print(f"   {filtered_count} Artikel → {output_path}")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
