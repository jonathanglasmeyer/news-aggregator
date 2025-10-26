#!/usr/bin/env python3
"""
Test direct RSS feed access for German news sources.
Determines if Inoreader API is needed for Cloudflare bypass.
"""

import requests
from datetime import datetime

FEEDS = {
    'Tagesschau': 'https://www.tagesschau.de/xml/rss2/',
    'Zeit Online': 'https://newsfeed.zeit.de/index',
    'Spiegel': 'https://www.spiegel.de/schlagzeilen/index.rss',
}

def test_feed(name, url):
    """Test if feed is accessible without authentication."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")

    try:
        # Use a real browser user agent to avoid basic bot detection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        response = requests.get(url, headers=headers, timeout=10)

        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"Content-Length: {len(response.content)} bytes")

        # Check for Cloudflare
        if 'cloudflare' in response.text.lower():
            print("⚠️  Cloudflare detected in response")

        # Check if it looks like RSS/XML
        content_preview = response.text[:500]
        if '<?xml' in content_preview or '<rss' in content_preview or '<feed' in content_preview:
            print("✅ Valid RSS/XML detected")
            # Show first item title if possible
            if '<title>' in response.text:
                import re
                titles = re.findall(r'<title>(.*?)</title>', response.text)
                if len(titles) > 1:  # Skip feed title, get first article
                    print(f"First article: {titles[1][:100]}")
        else:
            print("❌ Does not appear to be RSS/XML")
            print(f"Preview: {content_preview[:200]}")

        return response.status_code == 200

    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print(f"\nRSS Feed Accessibility Test")
    print(f"Timestamp: {datetime.now().isoformat()}")

    results = {}
    for name, url in FEEDS.items():
        results[name] = test_feed(name, url)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for name, success in results.items():
        status = "✅ Accessible" if success else "❌ Blocked/Failed"
        print(f"{name}: {status}")

    accessible_count = sum(results.values())
    print(f"\nResult: {accessible_count}/{len(FEEDS)} feeds accessible")

    if accessible_count == len(FEEDS):
        print("\n🎉 All feeds accessible! Inoreader API likely not needed.")
    elif accessible_count > 0:
        print("\n⚠️  Some feeds accessible. Consider direct access + fallback.")
    else:
        print("\n❌ No feeds accessible. Inoreader API or Oracle Cloud needed.")

if __name__ == '__main__':
    main()
