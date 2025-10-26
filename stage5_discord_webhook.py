#!/usr/bin/env python3
"""
Stage 5: Post Digest to Discord via Webhook
============================================

Posts the generated digest to Discord using a webhook.
Used by GitHub Actions for automated daily posts.

Usage:
    python stage5_discord_webhook.py data/filtered/digest_20251026_144713_v4.md
"""

import os
import sys
import requests
from pathlib import Path
from datetime import datetime

DISCORD_MESSAGE_LIMIT = 2000


def load_digest(digest_path: Path) -> str:
    """Load digest content from markdown file"""
    with open(digest_path, 'r', encoding='utf-8') as f:
        return f.read()


def split_content_by_sections(content: str) -> list[str]:
    """
    Split content intelligently at section boundaries.
    Prioritizes splitting at # headers.
    """
    chunks = []
    lines = content.split('\n')

    current_chunk = []
    current_length = 0

    # Skip until MUST-KNOW section
    start_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('# MUST-KNOW'):
            start_idx = i
            break

    # Stop at DISCARDED section (don't post discarded articles)
    end_idx = len(lines)
    for i, line in enumerate(lines[start_idx:], start=start_idx):
        if line.strip().startswith('# DISCARDED'):
            end_idx = i
            break

    main_content = lines[start_idx:end_idx]

    # Split main content at section boundaries
    for line in main_content:
        # Check if we're at a section header
        is_section = line.startswith('# ') and not line.startswith('## ')

        # Split before section headers if current chunk is not empty
        if is_section and current_chunk:
            chunk_text = '\n'.join(current_chunk)
            if len(chunk_text) > 0:
                chunks.append(chunk_text)
            current_chunk = []
            current_length = 0

        # Calculate what the chunk size would be with this line added
        if current_chunk:
            test_chunk = '\n'.join(current_chunk + [line])
        else:
            test_chunk = line

        # If adding this line would exceed limit, save current chunk first
        if len(test_chunk) > DISCORD_MESSAGE_LIMIT:
            if current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_length = 0
            # Now add the line to the new chunk (even if it's too long by itself)
            # Long lines will be handled individually
            if len(line) > DISCORD_MESSAGE_LIMIT:
                # Split very long lines at word boundaries
                words = line.split(' ')
                temp_line = ''
                for word in words:
                    if len(temp_line) + len(word) + 1 <= DISCORD_MESSAGE_LIMIT:
                        temp_line += (' ' if temp_line else '') + word
                    else:
                        if temp_line:
                            current_chunk.append(temp_line)
                        temp_line = word
                if temp_line:
                    current_chunk.append(temp_line)
            else:
                current_chunk.append(line)
        else:
            current_chunk.append(line)

        current_length = len('\n'.join(current_chunk)) if current_chunk else 0

    # Add remaining chunk
    if current_chunk:
        chunk_text = '\n'.join(current_chunk)
        if len(chunk_text) > 0:
            chunks.append(chunk_text)

    return chunks


def format_for_discord(content: str) -> str:
    """Format markdown for Discord"""
    import re

    # Disable link previews by wrapping URLs in <>
    content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'[\1](<\2>)', content)

    # Remove horizontal rules
    content = content.replace('---', '')

    # Ensure newline before h1 headers (# but not ##)
    # This fixes the formatting issue where text runs directly into headers
    content = re.sub(r'([^\n])\n(# [^#])', r'\1\n\n\2', content)

    return content


def post_to_discord(webhook_url: str, chunks: list[str]):
    """Post content chunks to Discord webhook"""
    print(f"\n📤 Posting {len(chunks)} messages to Discord...")

    for i, chunk in enumerate(chunks, 1):
        # Add header to first message
        if i == 1:
            date = datetime.now().strftime('%Y-%m-%d')
            message = f"📰 **News Digest** {date}\n\n{chunk}"
        else:
            message = chunk

        # Post to webhook
        payload = {
            "content": message,
            "username": "News Digest Bot"
        }

        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            print(f"   ✅ Posted chunk {i}/{len(chunks)}")

            # Rate limiting: Discord allows ~5 messages per 5 seconds
            if i < len(chunks):
                import time
                time.sleep(1)

        except requests.exceptions.HTTPError as e:
            print(f"   ❌ Failed to post chunk {i}: {e}")
            print(f"   Response: {response.text}")
            raise


def main():
    print("\n" + "="*80)
    print("STAGE 5: POST TO DISCORD (WEBHOOK)")
    print("="*80 + "\n")

    # Get webhook URL
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL environment variable not set")
        sys.exit(1)

    # Get digest file
    if len(sys.argv) > 1:
        digest_path = Path(sys.argv[1])
    else:
        # Use latest digest
        digest_files = sorted(Path('data/filtered').glob('digest_*.md'), reverse=True)
        if not digest_files:
            print("❌ No digest files found")
            sys.exit(1)
        digest_path = digest_files[0]

    if not digest_path.exists():
        print(f"❌ Digest file not found: {digest_path}")
        sys.exit(1)

    print(f"📂 Digest: {digest_path.name}")

    # Load and process digest
    print(f"\n⏳ Loading digest...")
    content = load_digest(digest_path)

    print(f"⏳ Formatting for Discord...")
    content = format_for_discord(content)

    print(f"⏳ Splitting into chunks...")
    chunks = split_content_by_sections(content)
    print(f"   Created {len(chunks)} chunks")

    # Post to Discord
    try:
        post_to_discord(webhook_url, chunks)
    except Exception as e:
        print(f"\n❌ Failed to post to Discord: {e}")
        sys.exit(1)

    print("\n" + "="*80)
    print(f"✅ DIGEST POSTED TO DISCORD")
    print(f"   {len(chunks)} messages sent")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
