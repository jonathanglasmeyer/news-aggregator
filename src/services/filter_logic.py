"""
Shared Filter Logic
===================

Domain logic for article filtering - shared between local and remote execution.
Contains blacklist keywords, clustering logic, and filtering rules.
"""

from typing import List, Dict, Tuple, Any
import numpy as np


# Blacklist Keywords - Single Source of Truth
BLACKLIST_KEYWORDS = [
    # Sport
    'olympia', 'olympisch', 'weltmeister', 'europameister', 'fußball', 'bundesliga',
    'champions league', 'europa league', 'em 2024', 'wm 2026', 'spieltag', 'tabellenführer',
    'aufstieg', 'abstieg', 'pokal', 'finale', 'halbfinale', 'viertelfinale',
    'tennis', 'formel 1', 'tour de france', 'wimbledon', 'super bowl',

    # Entertainment & Celebrities
    'oscar', 'oscar-verleihung', 'goldene kamera', 'bambi', 'eurovision',
    'song contest', 'dschungelcamp', 'bachelor', 'bachelorette', 'dsds',
    'the voice', 'lets dance', 'promi big brother', 'gntm',
    'netflix serie', 'amazon prime serie', 'tatort', 'polizeiruf',

    # Royalty & Celebrity Gossip
    'könig charles', 'königin camilla', 'prinz william', 'prinzessin kate',
    'royal family', 'prinzessin diana', 'meghan markle', 'prinz harry',
    'monaco royal', 'schweden königshaus', 'niederland königshaus',

    # Local German News
    'stadtrat', 'gemeinderat', 'bürgermeister', 'landrat', 'kreistag',
    'kommunalwahl', 'kommunalpolitik', 'ortsverband', 'bezirksamt',
    'stadtverwaltung', 'landesregierung einzelnes bundesland',

    # Crime & Local Incidents
    'festnahme', 'fahndung', 'vermisst', 'leiche gefunden', 'brand in',
    'unfall auf', 'einbruch', 'diebstahl', 'überfall', 'räuber',
    'polizeieinsatz', 'feuerwehreinsatz', 'rettungseinsatz',

    # Weather & Natural Events
    'wetterbericht', 'wettervorhersage', 'temperatur', 'regen', 'schnee',
    'unwetterwarnung', 'sturmwarnung', 'hochwasser einzelfall',
    'hitzewarnung', 'kältewelle', 'gewitter', 'hagel',

    # Traffic & Infrastructure
    'stau', 'verkehrsmeldung', 'baustelle', 'sperrung', 'umleitung',
    'streik deutsche bahn', 'verspätung', 'zugausfall', 'flugausfall',

    # Consumer News
    'produkttest', 'stiftung warentest', 'öko-test', 'rückruf',
    'lebensmittelwarnung', 'warenrückruf einzelfall',

    # Security/Vulnerabilities (filtert 95% raus)
    'sicherheitslücke', 'schwachstelle', 'vulnerability', 'cve-',
    'zero-day', 'zero day', 'exploit entdeckt', 'lücke bedroht',
    'lücke gefunden', 'lücke geschlossen', 'patch verfügbar',
    'hotfix', 'security update', 'security advisory',
    'security flaw', 'sicherheitsupdate', 'patchday',

    # Frickel-Hardware (kein Raspberry Pi, Arduino, E-Reader etc.)
    'raspberry pi', 'raspi', 'arduino', 'e-reader', 'e-ink',
    'einplatinencomputer', 'single-board computer',
    'diy hardware',
]


def contains_blacklisted_keyword(text: str, keywords: List[str] = None) -> Tuple[bool, str]:
    """
    Check if text contains any blacklisted keyword.

    Args:
        text: Text to check
        keywords: Optional custom keyword list (defaults to BLACKLIST_KEYWORDS)

    Returns:
        (is_blacklisted, matched_keyword)
    """
    if keywords is None:
        keywords = BLACKLIST_KEYWORDS

    text_lower = text.lower()
    for keyword in keywords:
        if keyword.lower() in text_lower:
            return True, keyword
    return False, ""


def filter_by_blacklist(articles: List[Dict]) -> Tuple[List[Dict], List[Dict], Dict[str, int]]:
    """
    Filter articles by blacklist keywords.

    Args:
        articles: List of article dicts with 'title' and 'content' (or 'description')

    Returns:
        (kept_articles, blacklisted_articles, blacklist_stats)
    """
    kept_articles = []
    blacklisted_articles = []
    blacklist_stats = {}

    for article in articles:
        text = f"{article['title']} {article['content']}"
        is_blacklisted, keyword = contains_blacklisted_keyword(text)

        if is_blacklisted:
            blacklisted_articles.append(article)
            blacklist_stats[keyword] = blacklist_stats.get(keyword, 0) + 1
        else:
            kept_articles.append(article)

    return kept_articles, blacklisted_articles, blacklist_stats


def cluster_and_filter_with_embeddings(articles: List[Dict], model) -> Tuple[List[Dict], Dict[str, Any]]:
    """
    Full embedding-based clustering and filtering.
    Uses DBSCAN clustering + blacklist filtering.

    Args:
        articles: List of article dicts
        model: Embedding model (e.g., BGEM3FlagModel)

    Returns:
        (filtered_articles, stats_dict)
    """
    # First pass: Blacklist filtering
    kept_articles, blacklisted_articles, blacklist_stats = filter_by_blacklist(articles)

    # TODO: Add DBSCAN clustering here if needed
    # For now, just use blacklist filtering

    stats = {
        'input_count': len(articles),
        'filtered_count': len(kept_articles),
        'blacklisted_count': len(blacklisted_articles),
        'reduction_rate': f"{len(blacklisted_articles) / len(articles) * 100:.1f}%" if articles else "0%",
        'top_blacklist_reasons': dict(sorted(blacklist_stats.items(), key=lambda x: x[1], reverse=True)[:10])
    }

    return kept_articles, stats


def simple_filter(articles: List[Dict]) -> Tuple[List[Dict], Dict[str, Any]]:
    """
    Simple keyword-based filtering without embeddings.
    Faster, suitable for API/remote calls.

    Args:
        articles: List of article dicts

    Returns:
        (filtered_articles, stats_dict)
    """
    kept_articles, blacklisted_articles, blacklist_stats = filter_by_blacklist(articles)

    stats = {
        'input_count': len(articles),
        'filtered_count': len(kept_articles),
        'blacklisted_count': len(blacklisted_articles),
        'reduction_rate': f"{len(blacklisted_articles) / len(articles) * 100:.1f}%" if articles else "0%",
        'top_blacklist_reasons': dict(sorted(blacklist_stats.items(), key=lambda x: x[1], reverse=True)[:10])
    }

    return kept_articles, stats


# Blacklist Categories for Embedding-Based Filtering
BLACKLIST_CATEGORIES = {
    'sport': 'Fußball Bundesliga Champions League Olympia Weltmeisterschaft Europameisterschaft Tennis Formel 1 Tour de France Wimbledon Super Bowl Spieltag Tabellenführer Torwart Mannschaft Trainer Verein Pokal',
    'entertainment': 'Oscar Goldene Kamera Bambi Eurovision Song Contest Dschungelcamp Bachelor Bachelorette DSDS Netflix Serie Amazon Prime Tatort Polizeiruf Promi Celebrity Show',
    'royalty': 'König Königin Prinz Prinzessin Royal Family Diana Meghan Markle Harry William Kate Camilla Charles Monaco Schweden Niederlande Königshaus',
    'local_politics': 'Stadtrat Gemeinderat Bürgermeister Landrat Kreistag Kommunalwahl Kommunalpolitik Ortsverband Bezirksamt Stadtverwaltung',
    'crime_local': 'Festnahme Fahndung Vermisst Leiche gefunden Brand Unfall Einbruch Diebstahl Überfall Räuber Polizeieinsatz Feuerwehreinsatz',
    'weather': 'Wetterbericht Wettervorhersage Temperatur Regen Schnee Unwetter Sturm Hochwasser Hitze Kälte Gewitter Hagel',
    'traffic': 'Stau Verkehrsmeldung Baustelle Sperrung Umleitung Streik Deutsche Bahn Verspätung Zugausfall Flugausfall',
    'consumer': 'Produkttest Stiftung Warentest Ökotest Rückruf Lebensmittelwarnung Warenrückruf',
    'security_vulns': 'Sicherheitslücke Schwachstelle Vulnerability CVE Zero-Day Exploit Patch Hotfix Security Update Advisory Flaw Patchday',
    'diy_hardware': 'Raspberry Pi Arduino E-Reader E-Ink Einplatinencomputer Single-Board Computer DIY Hardware Basteln'
}

# Cache for category embeddings
_CATEGORY_EMBEDDINGS_CACHE = None


def get_blacklist_category_embeddings(model) -> Dict[str, np.ndarray]:
    """
    Get or create embeddings for blacklist categories.
    Cached after first call for performance.

    Args:
        model: Embedding model (BGEM3FlagModel)

    Returns:
        Dict mapping category name to embedding vector
    """
    global _CATEGORY_EMBEDDINGS_CACHE

    if _CATEGORY_EMBEDDINGS_CACHE is not None:
        return _CATEGORY_EMBEDDINGS_CACHE

    print("🔄 Creating blacklist category embeddings...")
    category_embeddings = {}

    for category, keywords in BLACKLIST_CATEGORIES.items():
        # Encode the concatenated keywords for this category
        embedding = model.encode([keywords])['dense_vecs'][0]
        category_embeddings[category] = embedding

    _CATEGORY_EMBEDDINGS_CACHE = category_embeddings
    print(f"✅ Created {len(category_embeddings)} category embeddings")

    return category_embeddings


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def embedding_based_blacklist_filter(
    articles: List[Dict],
    model,
    threshold: float = 0.6
) -> Tuple[List[Dict], Dict[str, Any]]:
    """
    Embedding-based blacklist filtering.
    More robust than keyword matching - catches semantic similarity.

    Args:
        articles: List of article dicts
        model: Embedding model (BGEM3FlagModel)
        threshold: Similarity threshold for blacklisting (default 0.6)

    Returns:
        (filtered_articles, stats_dict)
    """
    if not articles:
        return [], {'input_count': 0, 'filtered_count': 0, 'blacklisted_count': 0}

    # Get category embeddings (cached)
    category_embeddings = get_blacklist_category_embeddings(model)

    # Embed all articles
    article_texts = [f"{a['title']} {a['content']}" for a in articles]
    article_embeddings = model.encode(article_texts)['dense_vecs']

    kept_articles = []
    blacklisted_articles = []
    category_hits = {cat: 0 for cat in BLACKLIST_CATEGORIES.keys()}

    for i, article in enumerate(articles):
        article_emb = article_embeddings[i]

        # Check similarity to each blacklist category
        max_similarity = 0.0
        matched_category = None

        for category, cat_emb in category_embeddings.items():
            similarity = cosine_similarity(article_emb, cat_emb)
            if similarity > max_similarity:
                max_similarity = similarity
                matched_category = category

        # Blacklist if similarity exceeds threshold
        if max_similarity > threshold:
            blacklisted_articles.append(article)
            category_hits[matched_category] += 1
        else:
            kept_articles.append(article)

    stats = {
        'input_count': len(articles),
        'filtered_count': len(kept_articles),
        'blacklisted_count': len(blacklisted_articles),
        'reduction_rate': f"{len(blacklisted_articles) / len(articles) * 100:.1f}%" if articles else "0%",
        'threshold': threshold,
        'category_hits': dict(sorted(category_hits.items(), key=lambda x: x[1], reverse=True))
    }

    return kept_articles, stats


def benchmark_filters(
    articles: List[Dict],
    model
) -> Dict[str, Any]:
    """
    Run both filtering approaches and compare results.

    Args:
        articles: List of article dicts
        model: Embedding model

    Returns:
        Benchmark results dict
    """
    print("\n" + "="*80)
    print("FILTER BENCHMARK: Keyword vs Embedding")
    print("="*80)

    # Run keyword-based filter
    print("\n1️⃣  Running keyword-based filter...")
    kept_keyword, stats_keyword = simple_filter(articles)

    # Run embedding-based filter
    print("\n2️⃣  Running embedding-based filter...")
    kept_embedding, stats_embedding = embedding_based_blacklist_filter(articles, model)

    # Compare results
    keyword_ids = {a['link'] for a in kept_keyword}
    embedding_ids = {a['link'] for a in kept_embedding}

    only_keyword = keyword_ids - embedding_ids
    only_embedding = embedding_ids - keyword_ids
    both = keyword_ids & embedding_ids

    print("\n" + "="*80)
    print("BENCHMARK RESULTS")
    print("="*80)
    print(f"\n📊 Input: {len(articles)} articles")
    print(f"\n🔑 Keyword Filter:")
    print(f"   Kept: {len(kept_keyword)} articles")
    print(f"   Blocked: {stats_keyword['blacklisted_count']} articles")
    print(f"   Rate: {stats_keyword['reduction_rate']}")

    print(f"\n🧠 Embedding Filter:")
    print(f"   Kept: {len(kept_embedding)} articles")
    print(f"   Blocked: {stats_embedding['blacklisted_count']} articles")
    print(f"   Rate: {stats_embedding['reduction_rate']}")

    print(f"\n🔍 Comparison:")
    print(f"   Both kept: {len(both)} articles")
    print(f"   Only keyword kept: {len(only_keyword)} articles")
    print(f"   Only embedding kept: {len(only_embedding)} articles")

    # Show examples of differences
    if only_keyword:
        print(f"\n   📰 Examples blocked by embedding but not keyword:")
        for link in list(only_keyword)[:3]:
            art = next(a for a in articles if a['link'] == link)
            print(f"      - {art['title'][:80]}")

    if only_embedding:
        print(f"\n   📰 Examples blocked by keyword but not embedding:")
        for link in list(only_embedding)[:3]:
            art = next(a for a in articles if a['link'] == link)
            print(f"      - {art['title'][:80]}")

    return {
        'keyword_stats': stats_keyword,
        'embedding_stats': stats_embedding,
        'kept_by_both': len(both),
        'only_keyword': len(only_keyword),
        'only_embedding': len(only_embedding)
    }
