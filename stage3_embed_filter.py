#!/usr/bin/env python3
"""
Stage 3: Embedding-based Pre-Filter
Reduces article count semantically before expensive Claude filtering.
Uses EmbeddingGemma for multilingual semantic understanding.
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import numpy as np


def load_aggregated_data(input_file=None):
    """Load aggregated articles."""
    if not input_file:
        # Find latest aggregated dump
        dumps = sorted(Path('data/aggregated').glob('*.json'))
        if not dumps:
            print("❌ No aggregated dumps found in data/aggregated/")
            print("   Run stage2_aggregate.py first")
            return None, None
        input_file = str(dumps[-1])
        print(f"Using latest aggregated dump: {input_file}")

    print(f"\nLoading articles from: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    articles = data['articles']
    date_range = data.get('date_range', {})
    date_start = date_range.get('start', 'unknown')
    date_end = date_range.get('end', 'unknown')
    print(f"Loaded {len(articles)} articles from {date_start} to {date_end}\n")

    return articles, input_file


def embed_articles(articles):
    """Generate embeddings for article titles using EmbeddingGemma."""
    print(f"\n{'='*80}")
    print(f"STAGE 3: EMBEDDING-BASED PRE-FILTER")
    print(f"{'='*80}\n")

    print(f"⏳ Loading EmbeddingGemma model...")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('google/embeddinggemma-300m')
        print(f"✅ Model loaded\n")
    except ImportError:
        print(f"❌ sentence-transformers not installed")
        print(f"   Run: uv pip install sentence-transformers")
        return None
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print(f"   Falling back to smaller model...")
        try:
            model = SentenceTransformer('BAAI/bge-m3')
            print(f"✅ Fallback model loaded\n")
        except:
            print(f"❌ Could not load any model")
            return None

    print(f"🔢 Generating embeddings for {len(articles)} articles...")
    titles = [a['title'] + ' ' + a.get('content', '')[:200] for a in articles]
    embeddings = model.encode(titles, show_progress_bar=True)
    print(f"✅ Generated {len(embeddings)} embeddings\n")

    return embeddings


def cluster_articles(articles, embeddings):
    """Cluster articles by semantic similarity."""
    print(f"{'='*80}")
    print(f"CLUSTERING")
    print(f"{'='*80}\n")

    try:
        from sklearn.cluster import DBSCAN
    except ImportError:
        print(f"❌ scikit-learn not installed")
        print(f"   Run: uv pip install scikit-learn")
        return None

    # DBSCAN clustering
    # eps: max distance between samples in cluster
    # min_samples: min samples in cluster (1 = all points get clustered)
    print(f"🔍 Running DBSCAN clustering...")
    clustering = DBSCAN(eps=0.35, min_samples=1, metric='cosine').fit(embeddings)
    labels = clustering.labels_

    # Group articles by cluster
    clusters = defaultdict(list)
    for idx, label in enumerate(labels):
        clusters[label].append(idx)

    print(f"✅ Found {len(clusters)} clusters\n")

    # Cluster stats
    cluster_sizes = [len(clusters[label]) for label in clusters]
    print(f"Cluster size distribution:")
    print(f"  Min:    {min(cluster_sizes)}")
    print(f"  Max:    {max(cluster_sizes)}")
    print(f"  Mean:   {np.mean(cluster_sizes):.1f}")
    print(f"  Median: {np.median(cluster_sizes):.1f}")

    return clusters, labels


def score_clusters(articles, clusters, labels):
    """
    Score clusters by relevance.
    Simple aggressive blacklist-based filtering.
    Blacklist match = instant reject.
    """
    print(f"\n{'='*80}")
    print(f"SCORING CLUSTERS")
    print(f"{'='*80}\n")

    # Aggressive blacklist - instant reject
    blacklist = [
        # Sport (komplett raus)
        'fußball', 'bundesliga', 'football', 'soccer', 'tennis', 'golf',
        'basketball', 'baseball', 'cricket', 'rugby', 'formel 1', 'f1',
        'olympia', 'olympics', 'wm', 'em', 'world cup', 'champions league',
        'spieler', 'trainer', 'verein', 'mannschaft', 'team wins', 'defeated',

        # Entertainment (komplett raus)
        'promi', 'promis', 'celebrity', 'celebrities', 'star dies',
        'actor', 'actress', 'singer', 'musician', 'band', 'album',
        'movie', 'film', 'tv show', 'serie', 'netflix', 'disney',
        'eurovision', 'song contest', 'esc',

        # Einzelne Kriminalfälle/Unfälle (komplett raus)
        'heist', 'robbery', 'burglar', 'burglarized',
        'tourist dies', 'hotel balcony', 'balcony fall',
        'murder suspect', 'arrested after killing',

        # Lokale deutsche News (sehr spezifisch)
        'fischerei', 'fischer', 'angeln', 'wetter', 'weather forecast',
        'verkehr', 'traffic', 'blitzer', 'stau', 'zeitumstellung',
        'bürgerentscheid', 'umweltpreis',

        # Nischen-Themen
        'workshop', 'schulung', 'fortbildung', 'seminar', 'veranstaltung',
        'rezept', 'kochen', 'cooking', 'recipe',

        # Frickel-Hardware (kein Raspberry Pi, Arduino, E-Reader etc.)
        'raspberry pi', 'raspi', 'arduino', 'e-reader', 'e-ink',
        'einplatinencomputer', 'single-board computer', 'maker', 'diy hardware',

        # Security/Vulnerabilities (filtert 95% raus, wichtige aktive Angriffe kommen durch andere Keywords durch)
        'sicherheitslücke', 'schwachstelle', 'vulnerability', 'cve-',
        'zero-day', 'zero day', 'exploit entdeckt', 'lücke bedroht', 'lücke gefunden',
        'lücke geschlossen', 'patch verfügbar', 'hotfix', 'security update',
        'security advisory', 'security flaw', 'sicherheitsupdate', 'patchday',

        # Software-Updates/Bugfixes (zu granular)
        'patch tuesday', 'security patch', 'bugfix release',
        'windows update', 'microsoft patch', 'kde plasma',
        'gnome release', 'browser update', 'beta release',
        'minor release', 'version release', 'update verfügbar',
        'neue version', 'powertoys', 'software update',
    ]

    # Relevance keywords (boost important topics)
    relevance = [
        # Politik/Weltgeschehen
        'krieg', 'war', 'konflikt', 'conflict', 'trump', 'biden', 'harris',
        'election', 'wahl', 'präsident', 'president', 'minister',
        'ukraine', 'russia', 'china', 'usa', 'israel', 'gaza', 'iran',
        'putin', 'xi jinping', 'netanyahu',

        # Tech/AI (high-level)
        'ki', 'ai', 'artificial intelligence', 'openai', 'anthropic', 'claude',
        'chatgpt', 'llm', 'model', 'deepseek', 'google ai', 'meta ai',

        # Wirtschaft/Klima
        'klimawandel', 'climate change', 'energie', 'energy', 'renewable',
        'wirtschaft', 'economy', 'gdp', 'inflation', 'recession', 'tariff',
        'sanktion', 'sanctions', 'trade war',
    ]

    cluster_scores = {}
    rejected_clusters = []

    for cluster_id, article_indices in clusters.items():
        cluster_articles = [articles[i] for i in article_indices]

        # Check all articles in cluster for blacklist
        all_text = ' '.join([
            a['title'].lower() + ' ' + a.get('content', '').lower()[:200]
            for a in cluster_articles
        ])

        # Instant reject if blacklist match (whole word match only)
        blacklist_matches = []
        for word in blacklist:
            # Use word boundaries to match whole words only
            pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(pattern, all_text):
                blacklist_matches.append(word)
                break  # One match is enough

        if blacklist_matches:
            cluster_scores[cluster_id] = 0  # Instant reject
            rejected_clusters.append({
                'id': cluster_id,
                'reason': blacklist_matches[0],
                'sample': cluster_articles[0]['title'][:60]
            })
            continue

        # Default: Accept (score = 100)
        score = 100.0

        # Boost if relevance keywords found
        relevance_matches = sum(1 for word in relevance if word in all_text)
        score += relevance_matches * 10  # Small boost

        cluster_scores[cluster_id] = score

    print(f"Blacklist-rejected clusters: {len(rejected_clusters)}")
    print(f"Accepted clusters: {sum(1 for s in cluster_scores.values() if s > 0)}\n")

    if rejected_clusters[:5]:
        print("Sample rejected clusters:")
        for r in rejected_clusters[:5]:
            print(f"  - '{r['reason']}' in: {r['sample']}")

    return cluster_scores


def filter_by_score(articles, clusters, cluster_scores):
    """
    Filter articles by cluster score.
    Simple: score > 0 = keep, score = 0 = reject (blacklisted).
    """
    print(f"\n{'='*80}")
    print(f"FILTERING")
    print(f"{'='*80}\n")

    # Keep articles from non-blacklisted clusters
    kept_articles = []
    filtered_out = 0

    cluster_stats = []
    for cluster_id, article_indices in clusters.items():
        score = cluster_scores[cluster_id]
        cluster_articles = [articles[i] for i in article_indices]

        if score > 0:  # Not blacklisted
            # Keep representative articles from cluster
            # If cluster is large (>5), keep only most recent 5
            if len(cluster_articles) > 5:
                cluster_articles = sorted(
                    cluster_articles,
                    key=lambda x: x.get('published', '1900-01-01'),
                    reverse=True
                )[:5]  # Keep top 5 most recent

            kept_articles.extend(cluster_articles)
            cluster_stats.append({
                'id': cluster_id,
                'score': score,
                'size': len(article_indices),
                'kept': len(cluster_articles),
                'sample_title': cluster_articles[0]['title'][:60]
            })
        else:
            filtered_out += len(cluster_articles)

    # Sort by score descending
    cluster_stats.sort(key=lambda x: x['score'], reverse=True)

    print(f"Kept clusters: {len(cluster_stats)}")
    print(f"Blacklisted clusters: {sum(1 for s in cluster_scores.values() if s == 0)}\n")

    print(f"Top 10 clusters kept:")
    for i, stat in enumerate(cluster_stats[:10], 1):
        print(f"  {i:2d}. Score {stat['score']:5.1f} | "
              f"Size {stat['size']:3d} | "
              f"Kept {stat['kept']:2d} | "
              f"{stat['sample_title']}")

    print(f"\n{'='*80}")
    print(f"RESULTS")
    print(f"{'='*80}\n")
    print(f"Input articles:     {len(articles)}")
    print(f"Output articles:    {len(kept_articles)}")
    print(f"Filtered out:       {filtered_out}")
    print(f"Reduction:          {(1 - len(kept_articles)/len(articles))*100:.1f}%")

    return kept_articles


def save_embedded_output(articles, input_file):
    """Save filtered articles to data/embedded/."""
    Path('data/embedded').mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"data/embedded/{timestamp}.json"

    # Preserve original metadata
    with open(input_file, 'r') as f:
        original_data = json.load(f)

    output_data = {
        'timestamp': datetime.now().isoformat(),
        'input_file': input_file,
        'date_range': original_data.get('date_range'),
        'stage': 'embedded_prefilter',
        'total_articles': len(articles),
        'articles': articles,
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    return filename


def main():
    """Main execution."""
    # Load data
    input_file = sys.argv[1] if len(sys.argv) > 1 else None
    articles, input_file = load_aggregated_data(input_file)

    if not articles:
        return

    # Generate embeddings
    embeddings = embed_articles(articles)
    if embeddings is None:
        return

    # Cluster articles
    result = cluster_articles(articles, embeddings)
    if result is None:
        return
    clusters, labels = result

    # Score clusters
    cluster_scores = score_clusters(articles, clusters, labels)

    # Filter by score (blacklist-based, no threshold)
    filtered_articles = filter_by_score(articles, clusters, cluster_scores)

    # Save output
    output_file = save_embedded_output(filtered_articles, input_file)
    print(f"\n💾 Saved to: {output_file}")
    print(f"\nNext step: Run stage4_filter.py {output_file}")


if __name__ == '__main__':
    main()
