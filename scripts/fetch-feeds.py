#!/usr/bin/env python3
"""
RSS Feed Aggregator for Hugo
Fetches RSS feeds, normalizes content, and outputs JSON for Hugo data.
"""

import json
import hashlib
import re
import toml
import requests
import feedparser
from datetime import datetime
from pathlib import Path
from html import unescape
from urllib.parse import urlparse

def load_feeds_config(config_path="feeds.toml"):
    """Load feed configuration from TOML file."""
    with open(config_path, 'r') as f:
        config = toml.load(f)
    return config['feeds']

def clean_html(text):
    """Remove HTML tags and decode entities."""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    text = unescape(text)
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text)
    # Trim
    text = text.strip()
    return text

def truncate_summary(text, max_length=300):
    """Truncate text to max_length on word boundary."""
    if not text or len(text) <= max_length:
        return text
    
    # Find last space before max_length
    truncated = text[:max_length]
    last_space = truncated.rfind(' ')
    if last_space > 0:
        return truncated[:last_space] + "..."
    return truncated + "..."

def generate_id(entry):
    """Generate stable SHA-1 ID from entry content."""
    # Try guid/id first, then link, then title
    identity_source = ""
    
    if hasattr(entry, 'id') and entry.id:
        identity_source = entry.id
    elif hasattr(entry, 'guid') and entry.guid:
        identity_source = entry.guid
    elif hasattr(entry, 'link') and entry.link:
        identity_source = entry.link
    elif hasattr(entry, 'title') and entry.title:
        identity_source = entry.title
    
    return hashlib.sha1(identity_source.encode('utf-8')).hexdigest()

def parse_date(entry):
    """Extract and normalize published date."""
    date_str = None
    
    # Try published first, then updated
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        date_str = datetime(*entry.published_parsed[:6]).isoformat() + 'Z'
    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
        date_str = datetime(*entry.updated_parsed[:6]).isoformat() + 'Z'
    
    return date_str

def fetch_feed(feed_config):
    """Fetch and parse a single RSS feed."""
    try:
        print(f"Fetching {feed_config['name']} from {feed_config['url']}")
        
        # Fetch with user agent
        headers = {'User-Agent': 'RSS Aggregator/1.0'}
        response = requests.get(feed_config['url'], headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse feed
        feed = feedparser.parse(response.content)
        
        if feed.bozo:
            print(f"Warning: Feed {feed_config['name']} has parsing issues")
        
        items = []
        for entry in feed.entries:
            # Generate stable ID
            item_id = generate_id(entry)
            
            # Extract title
            title = clean_html(getattr(entry, 'title', '')).strip()
            if not title:
                title = "(untitled)"
            
            # Extract link
            link = getattr(entry, 'link', '')
            if not link:
                continue  # Skip items without links
            
            # Extract and clean summary
            summary = ""
            if hasattr(entry, 'summary'):
                summary = truncate_summary(clean_html(entry.summary))
            elif hasattr(entry, 'description'):
                summary = truncate_summary(clean_html(entry.description))
            
            # Parse date
            published = parse_date(entry)
            
            item = {
                'id': item_id,
                'title': title,
                'link': link,
                'source': feed_config['name']
            }
            
            if summary:
                item['summary'] = summary
            if published:
                item['published'] = published
                
            items.append(item)
        
        print(f"Fetched {len(items)} items from {feed_config['name']}")
        return items
        
    except Exception as e:
        print(f"Error fetching {feed_config['name']}: {e}")
        return []

def main():
    """Main function."""
    print("Starting RSS feed aggregation...")
    
    # Load feeds configuration
    feeds = load_feeds_config()
    
    # Fetch all feeds
    all_items = []
    seen_ids = set()
    
    for feed_config in feeds:
        items = fetch_feed(feed_config)
        
        # Deduplicate
        for item in items:
            if item['id'] not in seen_ids:
                all_items.append(item)
                seen_ids.add(item['id'])
    
    # Sort by published date (newest first), undated items last
    def sort_key(item):
        if 'published' in item:
            return (0, item['published'])
        else:
            return (1, '')  # Undated items sort after dated ones
    
    all_items.sort(key=sort_key, reverse=True)
    
    # Limit to 500 items
    if len(all_items) > 500:
        all_items = all_items[:500]
        print(f"Limited to 500 items (had {len(all_items)})")
    
    # Create output data
    output_data = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'items': all_items
    }
    
    # Ensure data directory exists
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    # Write JSON output
    output_path = data_dir / 'feeds.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Generated {len(all_items)} items in {output_path}")
    print("RSS feed aggregation complete!")

if __name__ == '__main__':
    main()