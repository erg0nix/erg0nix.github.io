---
title: "A public feed using rss"
date: 2025-09-10
draft: false
---

I made the public feed work, subscribing to rss feeds that I would like to follow, but keeping it open for others to see what I read and follow. well, I finally built it.

<!--more-->

## the idea

the concept was pretty simple: pull rss feeds from sources I follow, normalize the content, and display it on the site. make it automated so I don't have to think about it. I wanted people to see what I'm reading without having to maintain yet another social media presence. And I also wanted to have my own public feed that is automatic and I can read it, just aggregating to stuff I subscribe to. Yes rss feed readers exist, but then I couldn't share it with others so that they also can see what I read.

## the setup and recipe to copy this

I went with a pretty straightforward approach:

1. python script to fetch and process feeds
2. hugo template to display the content with pagination
3. github actions to keep everything updated automatically

Is the code any good? nah. But it works and simple to maintain. And thats a little fun, when you don't really care and just want it to work. Like throwing code at the wall and continue doing it until it works, but with some knowledge and precision. Also had claude code check the code after and it added some stuff, it added some comments and stuff but I didn't bother to clean up, since it worked so I think that was fine. Most important was the github actions logic so it didn't just continue to generate and run in loops and do weird stuff.

### feed configuration

first, I needed a way to configure which feeds to follow. went with a simple toml file:

```toml
[[feeds]]
name = "GitHub Blog"
url = "https://github.blog/feed/"

[[feeds]]
name = "Go Blog"
url = "https://go.dev/blog/feed/"
```

keeps it simple and easy to add new feeds later. Why toml? Because its simple to edit and I remembered that it exists. I also write this in neovim and for some reason my setup has better support for it than other stuff and I haven't bothered configuring it correctly.

### the python aggregator

the main script does the heavy lifting, fetches feeds, normalizes content, extracts images, and outputs json for hugo to consume. Also had to get images from the feeds. turns out many rss feeds embed images in their content, so I used beautifulsoup to extract the first image from each post:

```python
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
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

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

def extract_image(entry, feed_url):
    """Extract the first image from RSS entry content."""
    image_url = None
    
    # Look for images in content:encoded first, then description
    content = ""
    if hasattr(entry, 'content') and entry.content:
        content = entry.content[0].value
    elif hasattr(entry, 'description'):
        content = entry.description
    
    if content:
        try:
            soup = BeautifulSoup(content, 'html.parser')
            img_tag = soup.find('img')
            if img_tag and img_tag.get('src'):
                src = img_tag.get('src')
                # Convert relative URLs to absolute
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    base_url = '/'.join(feed_url.split('/')[:3])
                    src = base_url + src
                elif not src.startswith('http'):
                    src = urljoin(feed_url, src)
                image_url = src
        except Exception as e:
            # If HTML parsing fails, continue without image
            pass
    
    return image_url

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
            
            # Extract image
            image = extract_image(entry, feed_config['url'])
            
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
            if image:
                item['image'] = image
                
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

```

### hugo template with pagination

for the frontend, I built a hugo template that uses javascript for client-side pagination. keeps things snappy since all the data is already there:

```javascript
document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM loaded, feedData exists:', !!window.feedData);
  
  if (!window.feedData) {
    console.error('No feedData found!');
    return;
  }
  
  // Parse JSON string if needed
  let feedItems = window.feedData;
  if (typeof feedItems === 'string') {
    try {
      feedItems = JSON.parse(feedItems);
    } catch (e) {
      console.error('Failed to parse feedData JSON:', e);
      return;
    }
  }
  
  console.log('Parsed feedItems:', feedItems);
  console.log('feedItems is array:', Array.isArray(feedItems));
  
  const pageSize = 10;
  const totalItems = feedItems.length;
  const totalPages = Math.ceil(totalItems / pageSize);
  
  console.log('pageSize:', pageSize, 'totalItems:', totalItems, 'totalPages:', totalPages);
  
  // Get current page from URL
  const urlParams = new URLSearchParams(window.location.search);
  let currentPage = parseInt(urlParams.get('page')) || 1;
  if (currentPage < 1) currentPage = 1;
  if (currentPage > totalPages) currentPage = totalPages;
  
  function renderItems(page) {
    const startIndex = (page - 1) * pageSize;
    const endIndex = Math.min(startIndex + pageSize, totalItems);
    const pageItems = feedItems.slice(startIndex, endIndex);
    
    const itemsContainer = document.getElementById('feed-items');
    itemsContainer.innerHTML = '';
    
    pageItems.forEach(item => {
      const article = document.createElement('article');
      article.className = 'feed-item';
      
      let metaHtml = '';
      if (item.published) {
        const date = new Date(item.published).toISOString().split('T')[0];
        metaHtml += `<time>${date}</time>`;
      }
      if (item.source) {
        metaHtml += `<span class="source">${item.source}</span>`;
      }
      
      article.innerHTML = `
        <div class="feed-item-content">
          ${item.image ? `<div class="feed-item-image">
            <img src="${item.image}" alt="${item.title}" loading="lazy">
          </div>` : ''}
          <div class="feed-item-text">
            <h2><a href="${item.link}" target="_blank" rel="noopener">${item.title}</a></h2>
            <div class="feed-item-meta">${metaHtml}</div>
            ${item.summary ? `<p class="summary">${item.summary}</p>` : ''}
          </div>
        </div>
      `;
      
      itemsContainer.appendChild(article);
    });
    
    // Update meta text
    const metaText = document.getElementById('feed-meta-text');
    const generatedDate = new Date(window.feedGeneratedAt).toLocaleString();
    metaText.textContent = `Showing ${startIndex + 1}-${endIndex} of ${totalItems} items • Last updated: ${generatedDate}`;
    
    // Update pagination
    updatePagination(page);
  }
  
  function updatePagination(page) {
    const pagination = document.getElementById('pagination');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const pageInfo = document.getElementById('page-info');
    
    if (totalPages <= 1) {
      pagination.style.display = 'none';
      return;
    }
    
    pagination.style.display = 'flex';
    pageInfo.textContent = `Page ${page} of ${totalPages}`;
    
    // Previous button
    if (page <= 1) {
      prevBtn.style.opacity = '0.5';
      prevBtn.style.pointerEvents = 'none';
    } else {
      prevBtn.style.opacity = '1';
      prevBtn.style.pointerEvents = 'auto';
      prevBtn.onclick = () => goToPage(page - 1);
    }
    
    // Next button  
    if (page >= totalPages) {
      nextBtn.style.opacity = '0.5';
      nextBtn.style.pointerEvents = 'none';
    } else {
      nextBtn.style.opacity = '1';
      nextBtn.style.pointerEvents = 'auto';
      nextBtn.onclick = () => goToPage(page + 1);
    }
  }
  
  function goToPage(page) {
    const url = new URL(window.location);
    if (page === 1) {
      url.searchParams.delete('page');
    } else {
      url.searchParams.set('page', page);
    }
    window.history.pushState({}, '', url);
    currentPage = page;
    renderItems(page);
  }
  
  // Handle browser back/forward
  window.addEventListener('popstate', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const page = parseInt(urlParams.get('page')) || 1;
    currentPage = page;
    renderItems(page);
  });
  
  // Initial render
  renderItems(currentPage);
});
```

the layout shows 10 items per page with proper navigation and keeps the url state synced so you can bookmark specific pages. 

### github actions automation

to keep everything updated, I set up a github action that runs the feed script daily and on manual triggers:

```yaml
name: Update RSS Feeds

on:
  schedule:
    # Run daily at 6 AM UTC
    - cron: '0 6 * * *'
  
  # Run when feeds config is updated
  push:
    paths:
      - 'feeds.toml'
      - 'scripts/fetch-feeds.py'
      - '.github/workflows/update-feeds.yml'
  
  # Allow manual triggering
  workflow_dispatch:

# Permissions needed to commit changes
permissions:
  contents: write

jobs:
  update-feeds:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'
          
      - name: Install Python dependencies
        run: pip install requests feedparser toml beautifulsoup4
        
      - name: Fetch RSS feeds
        run: python scripts/fetch-feeds.py
        
      - name: Check for changes
        id: changes
        run: |
          if git diff --quiet data/feeds.json; then
            echo "changed=false" >> $GITHUB_OUTPUT
          else
            echo "changed=true" >> $GITHUB_OUTPUT
          fi
          
      - name: Commit and push changes
        if: steps.changes.outputs.changed == 'true'
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add data/feeds.json
          git commit -m "Update RSS feeds - $(date '+%Y-%m-%d %H:%M UTC')"
          git push
```

the key thing here is the `paths-ignore` to prevent infinite loops when the action commits the updated feeds.

## So what

the technical bits were straightforward. python for data processing, hugo for static generation, github actions for automation. but the result feels pretty satisfying.

one thing worth noting: while we call it an "rss feed aggregator", we're actually fetching rss feeds (xml format) over standard http/https using rest style requests. rss doesn't have its own transport protocol, it's just xml served over the web like any other resource. the `feedparser` library handles parsing the xml into python objects we can work with. The feed also just overwrites and resets every time its pulled, and I think thats fine. Keeps the json file we write to small and I don't need to have a huge archive of links.

you can check out the [feed page](/feed) to see it. and since everything is automated, it stays current without me having to think about it.
