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
