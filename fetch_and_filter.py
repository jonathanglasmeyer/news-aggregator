#!/usr/bin/env python3
"""
News aggregator - Fetch, filter, and summarize.

Step 1: Local execution, console output.
Later: Discord webhook, GitHub Actions scheduling.
"""

import feedparser
from datetime import datetime, timedelta
import re
import json
import asyncio
from claude_agent_sdk import ClaudeSDKClient
from feeds import get_all_feeds


def strip_html(text):
    """Remove HTML tags from text."""
    return re.sub('<[^<]+?>', '', text)


def parse_date(entry):
    """Parse published date from RSS entry."""
    if 'published_parsed' in entry and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])
    elif 'updated_parsed' in entry and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6])
    return None


def get_content(entry):
    """Extract content from RSS entry."""
    if 'content' in entry and entry.content:
        return entry.content[0].value
    elif 'summary' in entry:
        return entry.summary
    elif 'description' in entry:
        return entry.description
    return ""


def fetch_articles(days=7):
    """Fetch articles from all configured feeds."""
    print(f"Fetching articles from last {days} days...\n")

    cutoff_date = datetime.now() - timedelta(days=days)
    all_articles = []

    feeds = get_all_feeds()

    for feed_config in feeds:
        name = feed_config['name']
        url = feed_config['url']
        category = feed_config['category']

        print(f"  Fetching {name}...", end=' ', flush=True)

        try:
            feed = feedparser.parse(url)

            if not feed.entries:
                print("❌ No entries")
                continue

            count = 0
            for entry in feed.entries:
                pub_date = parse_date(entry)

                # Include if no date or within timeframe
                if pub_date is None or pub_date >= cutoff_date:
                    content = get_content(entry)
                    clean_content = strip_html(content)

                    all_articles.append({
                        'title': entry.get('title', 'NO TITLE'),
                        'link': entry.get('link', ''),
                        'published': pub_date,
                        'content': clean_content,
                        'source': name,
                        'category': category,
                    })
                    count += 1

            print(f"✅ {count} articles")

        except Exception as e:
            print(f"❌ Error: {str(e)[:50]}")

    print(f"\nTotal articles fetched: {len(all_articles)}")
    return all_articles


async def filter_with_claude(articles):
    """
    Filter articles using Claude Agent SDK.
    Uses same auth as `claude` CLI binary.
    """
    print(f"\nFiltering {len(articles)} articles with Claude...")
    print(f"⏳ Preparing articles for Claude...")

    # Prepare articles for Claude
    articles_text = []
    for i, article in enumerate(articles, 1):
        pub_str = article['published'].strftime('%Y-%m-%d') if article['published'] else 'Unknown date'
        articles_text.append(
            f"[{i}] {article['title']}\n"
            f"Source: {article['source']} | {pub_str}\n"
            f"Content: {article['content'][:500]}...\n"
            f"Link: {article['link']}\n"
        )

    articles_input = "\n".join(articles_text)

    # Claude filtering prompt
    prompt = f"""You are filtering a weekly news digest for a technical reader interested in:
- World news (politics, economics, major events)
- Tech/AI developments and software news
- German and European news
- NO opinion pieces, editorials, or analysis articles
- NO product reviews or consumer product tests
- NO workshop announcements or training courses

For each article below, determine:
1. Is this actual NEWS or opinion/analysis/editorial?
2. Is this relevant to the reader's interests?
3. Is this a duplicate or very similar to another article?

ONLY include articles that are:
- Factual news reporting (not opinion)
- Internationally or technically relevant
- Not duplicates

For EACH article you keep, provide:
- Original headline
- 2-3 sentence summary of what happened
- Why it's relevant
- Link

Format your response as a JSON array of objects with these fields:
- title: string
- summary: string (2-3 sentences)
- relevance: string (1 sentence why it matters)
- link: string
- source: string

Articles to filter:

{articles_input}

Respond ONLY with valid JSON, no other text."""

    # Use Claude Agent SDK (uses same auth as `claude` CLI)
    try:
        from claude_agent_sdk import AssistantMessage, TextBlock, ResultMessage
        import time

        print(f"🔌 Connecting to Claude...")
        start = time.time()

        client = ClaudeSDKClient()
        await client.connect()

        connect_time = time.time() - start
        print(f"✅ Connected in {connect_time:.1f}s")

        # Send query (returns None)
        print(f"📤 Sending {len(articles)} articles to Claude for filtering...")
        query_start = time.time()
        await client.query(prompt)

        # Receive response messages
        print(f"📥 Receiving response from Claude...")
        response_text = ""
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_text += block.text
                        print(".", end="", flush=True)  # Progress indicator

        query_time = time.time() - query_start
        print(f"\n✅ Received response in {query_time:.1f}s")

        print(f"🔌 Disconnecting...")
        await client.disconnect()

        # Parse JSON response
        # Claude might wrap it in markdown code blocks, strip those
        json_text = response_text.strip()
        if json_text.startswith('```json'):
            json_text = json_text[7:]
        if json_text.startswith('```'):
            json_text = json_text[3:]
        if json_text.endswith('```'):
            json_text = json_text[:-3]

        filtered_articles = json.loads(json_text.strip())

        print(f"✅ Claude filtered to {len(filtered_articles)} relevant articles\n")
        return filtered_articles

    except Exception as e:
        print(f"❌ Error calling Claude: {e}")
        import traceback
        traceback.print_exc()
        return []


def print_digest(filtered_articles):
    """Print formatted digest to console."""
    print(f"\n{'='*80}")
    print(f"WEEKLY NEWS DIGEST - {datetime.now().strftime('%Y-%m-%d')}")
    print(f"{'='*80}\n")

    if not filtered_articles:
        print("No relevant articles this week.")
        return

    print(f"📰 {len(filtered_articles)} articles selected\n")

    for i, article in enumerate(filtered_articles, 1):
        print(f"[{i}] {article['title']}")
        print(f"Source: {article.get('source', 'Unknown')}")
        print(f"\n{article['summary']}")
        print(f"\n💡 {article['relevance']}")
        print(f"🔗 {article['link']}")
        print(f"\n{'-'*80}\n")


async def main():
    """Main execution."""
    print(f"{'='*80}")
    print(f"NEWS AGGREGATOR - Local Run")
    print(f"{'='*80}\n")

    # Step 1: Fetch articles
    articles = fetch_articles(days=7)

    if not articles:
        print("No articles fetched. Exiting.")
        return

    # Step 2: Filter with Claude
    filtered = await filter_with_claude(articles)

    # Step 3: Print digest
    print_digest(filtered)

    print(f"\n{'='*80}")
    print(f"Done! Processed {len(articles)} → {len(filtered)} articles")
    print(f"{'='*80}")


if __name__ == '__main__':
    asyncio.run(main())
