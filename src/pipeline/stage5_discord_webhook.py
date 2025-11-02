#!/usr/bin/env python3
"""
Stage 5: Post Digest to Discord via Bot (with Thread)
======================================================

Posts the generated digest to Discord:
1. Posts a short summary message in the main channel
2. Creates a thread under that message
3. Posts all digest content in the thread

Used by GitHub Actions for automated daily posts.

Usage:
    python stage5_discord_webhook.py data/filtered/digest_20251026_144713_v4.md

Environment Variables:
    DISCORD_BOT_TOKEN: Discord bot token (from Developer Portal)
    DISCORD_CHANNEL_ID: ID of the channel to post in
"""

import os
import sys
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DISCORD_MESSAGE_LIMIT = 2000
DISCORD_API_BASE = "https://discord.com/api/v10"


def load_digest(digest_path: Path) -> str:
    """Load digest content from markdown file"""
    with open(digest_path, 'r', encoding='utf-8') as f:
        return f.read()


def split_content_by_sections(content: str) -> list[tuple[str, str]]:
    """
    Split content intelligently at section boundaries.
    Prioritizes splitting at # headers.
    Returns list of tuples: (chunk_text, section_name)
    """
    chunks = []
    lines = content.split('\n')

    # Fix LLM output bug: ensure section headers are on their own lines
    for i, line in enumerate(lines):
        for section_name in ['# MUST-KNOW', '# INTERESSANT', '# NICE-TO-KNOW', '# DISCARDED']:
            if section_name in line and not line.strip().startswith(section_name):
                # Split the line at the section header
                before, after = line.split(section_name, 1)
                # Replace with two lines (before gets discarded, section header starts fresh)
                lines[i] = section_name + after
                if before.strip():  # Only insert previous content if non-empty
                    lines.insert(i, before.rstrip())
                break

    current_chunk = []
    current_length = 0
    current_section = None

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

        # Track current section BEFORE splitting
        if is_section:
            if 'MUST-KNOW' in line:
                next_section = 'MUST-KNOW'
            elif 'INTERESSANT' in line:
                next_section = 'INTERESSANT'
            elif 'NICE-TO-KNOW' in line:
                next_section = 'NICE-TO-KNOW'
            else:
                next_section = current_section
        else:
            next_section = current_section

        # Split before section headers if current chunk is not empty
        if is_section and current_chunk:
            chunk_text = '\n'.join(current_chunk)
            if len(chunk_text) > 0:
                chunks.append((chunk_text, current_section))
            current_chunk = []
            current_length = 0

        # Update current section
        current_section = next_section

        # Calculate what the chunk size would be with this line added
        if current_chunk:
            test_chunk = '\n'.join(current_chunk + [line])
        else:
            test_chunk = line

        # If adding this line would exceed limit, save current chunk first
        if len(test_chunk) > DISCORD_MESSAGE_LIMIT:
            if current_chunk:
                chunks.append(('\n'.join(current_chunk), current_section))
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
            chunks.append((chunk_text, current_section))

    return chunks


def format_for_discord(content: str) -> str:
    """Format markdown for Discord"""
    import re

    # Disable link previews by wrapping URLs in <>
    content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'[\1](<\2>)', content)

    # Remove horizontal rules
    content = content.replace('---', '')

    # Ensure double newline before h1 headers (# but not ##)
    # This fixes the formatting issue where text runs directly into headers
    # Step 1: After single newline (but not double newline)
    content = re.sub(r'(?<!\n)(\n)(#)( )(?!#)', r'\1\n\2\3', content)
    # Step 2: At start of string
    content = re.sub(r'^(#)( )(?!#)', r'\n\n\1\2', content)
    # Step 3: After non-newline, non-hash character (text runs into header)
    content = re.sub(r'([^\n#])(#)( )(?!#)', r'\1\n\n\2\3', content)

    return content


def post_initial_message(bot_token: str, channel_id: str) -> str:
    """
    Post the initial message in the main channel.
    Returns the message ID for thread creation.
    """
    date = datetime.now().strftime('%Y-%m-%d')
    message = f"📰 **News Digest** {date}"

    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "content": message
    }

    url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages"
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    return response.json()['id']


def create_thread(bot_token: str, channel_id: str, message_id: str) -> str:
    """
    Create a thread under the initial message.
    Returns the thread ID.
    """
    date = datetime.now().strftime('%d.%m.%Y')
    thread_name = f"News {date}"

    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "name": thread_name,
        "auto_archive_duration": 1440  # Archive after 24 hours
    }

    url = f"{DISCORD_API_BASE}/channels/{channel_id}/messages/{message_id}/threads"
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()

    return response.json()['id']


def post_to_thread(bot_token: str, thread_id: str, chunks: list[tuple[str, str]]):
    """Post content chunks to Discord thread"""
    print(f"\n📤 Posting {len(chunks)} messages to thread...")

    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json"
    }

    for i, (chunk, section) in enumerate(chunks, 1):
        # Add zero-width space on blank line for visual separation
        # Only for MUST-KNOW and INTERESSANT sections, NOT for NICE-TO-KNOW
        if i > 1 and section in ['MUST-KNOW', 'INTERESSANT']:
            message = '\u200b\n' + chunk.rstrip()
        else:
            message = chunk.rstrip()

        payload = {
            "content": message
        }

        url = f"{DISCORD_API_BASE}/channels/{thread_id}/messages"

        try:
            response = requests.post(url, json=payload, headers=headers)
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
    print("STAGE 5: POST TO DISCORD (THREAD)")
    print("="*80 + "\n")

    # Get bot credentials
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    channel_id = os.getenv('DISCORD_CHANNEL_ID')

    if not bot_token:
        print("❌ DISCORD_BOT_TOKEN environment variable not set")
        sys.exit(1)
    if not channel_id:
        print("❌ DISCORD_CHANNEL_ID environment variable not set")
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
        print(f"\n📝 Posting initial message to main channel...")
        message_id = post_initial_message(bot_token, channel_id)
        print(f"   ✅ Posted message (ID: {message_id})")

        print(f"\n🧵 Creating thread...")
        thread_id = create_thread(bot_token, channel_id, message_id)
        print(f"   ✅ Created thread (ID: {thread_id})")

        post_to_thread(bot_token, thread_id, chunks)

    except Exception as e:
        print(f"\n❌ Failed to post to Discord: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "="*80)
    print(f"✅ DIGEST POSTED TO DISCORD")
    print(f"   1 main message + {len(chunks)} thread messages")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
