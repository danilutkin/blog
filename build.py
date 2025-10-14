#!/usr/bin/env python3
"""
Simple static blog generator - Hacker News style
Converts text files to static HTML with RSS feeds
"""

import os
import re
from datetime import datetime
from pathlib import Path

# Configuration
POSTS_DIR = Path('posts')
OUTPUT_DIR = Path('docs')
SITE_TITLE = "VPN Blog"
SITE_URL = "https://yourusername.github.io/your-repo"  # Update this
SITE_DESCRIPTION = "Simple, private VPN service for Russia and abroad"

def parse_post_filename(filename):
    """Extract date and title from filename like '2024-01-15-vpn-setup-guide.txt'"""
    match = re.match(r'(\d{4}-\d{2}-\d{2})-(.+)\.txt$', filename)
    if not match:
        return None, None
    date_str, title = match.groups()
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        return date, title.replace('-', ' ')
    except ValueError:
        return None, None

def load_posts():
    """Load all posts from posts directory"""
    posts = []
    
    if not POSTS_DIR.exists():
        POSTS_DIR.mkdir(exist_ok=True)
        return posts
    
    for txt_file in sorted(POSTS_DIR.glob('*.txt'), reverse=True):  # Newest first
        date, title = parse_post_filename(txt_file.name)
        if not date or not title:
            print(f"Warning: Skipping invalid filename: {txt_file.name}")
            continue
            
        with txt_file.open('r', encoding='utf-8') as f:
            content = f.read().strip()
        
        if not content:
            continue
            
        # Extract title from first line if it exists
        lines = content.split('\n')
        if lines and lines[0].strip():
            title = lines[0].strip()
            content = '\n'.join(lines[1:]).strip()
        
        # Create slug for URLs
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
        
        posts.append({
            'title': title,
            'slug': slug,
            'content': content,
            'date': date,
            'filename': txt_file.name
        })
    
    return posts

def html_escape(text):
    """Escape HTML special characters"""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#x27;'))

def format_content(content):
    """Convert plain text to HTML with basic formatting"""
    lines = content.split('\n')
    html_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            html_lines.append('<br>')
        elif line.startswith('- '):
            # Simple list item
            item = html_escape(line[2:])
            html_lines.append(f'<li>{item}</li>')
        else:
            # Regular paragraph
            escaped = html_escape(line)
            html_lines.append(f'<p>{escaped}</p>')
    
    return '\n'.join(html_lines)

def generate_index(posts):
    """Generate main index page"""
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{SITE_TITLE}</title>
    <meta name="description" content="{SITE_DESCRIPTION}">
    <link rel="stylesheet" href="style.css">
    <link rel="alternate" type="application/rss+xml" href="rss.xml">
    <link rel="alternate" type="application/atom+xml" href="atom.xml">
</head>
<body>
    <header>
        <h1><a href="index.html">{SITE_TITLE}</a></h1>
        <nav>
            <a href="rss.xml">RSS</a> | 
            <a href="atom.xml">Atom</a>
        </nav>
    </header>
    <main>
'''
    
    if posts:
        html += '        <div class="posts">\n'
        for post in posts:
            # Create excerpt (first 200 chars)
            excerpt = post['content'][:200].replace('\n', ' ')
            if len(post['content']) > 200:
                excerpt += '...'
            
            date_str = post['date'].strftime('%Y-%m-%d')
            html += f'''            <article class="post">
                <h2><a href="{post['slug']}.html">{post['title']}</a></h2>
                <time>{date_str}</time>
                <div class="excerpt">{html_escape(excerpt)}</div>
            </article>
'''
        html += '        </div>\n'
    else:
        html += '        <p>No posts yet. Check back soon!</p>\n'
    
    html += '''    </main>
    <footer>
        <p>Simple, private VPN service</p>
    </footer>
</body>
</html>'''
    
    return html

def generate_post_page(post, all_posts):
    """Generate individual post page"""
    # Find previous/next posts
    current_index = next(i for i, p in enumerate(all_posts) if p['slug'] == post['slug'])
    prev_post = all_posts[current_index + 1] if current_index + 1 < len(all_posts) else None
    next_post = all_posts[current_index - 1] if current_index > 0 else None
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{post['title']} - {SITE_TITLE}</title>
    <meta name="description" content="{html_escape(post['content'][:200])}">
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1><a href="index.html">{SITE_TITLE}</a></h1>
        <nav>
            <a href="index.html">← Back to posts</a>
        </nav>
    </header>
    <main>
        <article class="post-full">
            <h1>{post['title']}</h1>
            <time>{post['date'].strftime('%Y-%m-%d')}</time>
            <div class="content">
                {format_content(post['content'])}
            </div>
        </article>
        
        <nav class="post-nav">
'''
    
    if prev_post:
        html += f'            <a href="{prev_post["slug"]}.html" class="prev">← {prev_post["title"]}</a>\n'
    if next_post:
        html += f'            <a href="{next_post["slug"]}.html" class="next">{next_post["title"]} →</a>\n'
    
    html += '''        </nav>
    </main>
    <footer>
        <p>Simple, private VPN service</p>
    </footer>
</body>
</html>'''
    
    return html

def generate_rss(posts):
    """Generate RSS 2.0 feed"""
    rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>{SITE_TITLE}</title>
        <link>{SITE_URL}</link>
        <description>{SITE_DESCRIPTION}</description>
        <language>en</language>
        <lastBuildDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')}</lastBuildDate>
'''
    
    for post in posts[:10]:  # Latest 10 posts
        pub_date = post['date'].strftime('%a, %d %b %Y %H:%M:%S GMT')
        content = html_escape(post['content'][:500])
        if len(post['content']) > 500:
            content += '...'
        
        rss += f'''        <item>
            <title>{html_escape(post['title'])}</title>
            <link>{SITE_URL}/{post['slug']}.html</link>
            <description>{content}</description>
            <pubDate>{pub_date}</pubDate>
            <guid>{SITE_URL}/{post['slug']}.html</guid>
        </item>
'''
    
    rss += '''    </channel>
</rss>'''
    
    return rss

def generate_atom(posts):
    """Generate Atom 1.0 feed"""
    atom = f'''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <title>{SITE_TITLE}</title>
    <link href="{SITE_URL}" />
    <link href="{SITE_URL}/atom.xml" rel="self" />
    <id>{SITE_URL}</id>
    <updated>{datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}</updated>
    <author>
        <name>{SITE_TITLE}</name>
    </author>
    <subtitle>{SITE_DESCRIPTION}</subtitle>
'''
    
    for post in posts[:10]:  # Latest 10 posts
        updated = post['date'].strftime('%Y-%m-%dT%H:%M:%SZ')
        content = html_escape(post['content'])
        
        atom += f'''    <entry>
        <title>{html_escape(post['title'])}</title>
        <link href="{SITE_URL}/{post['slug']}.html" />
        <id>{SITE_URL}/{post['slug']}.html</id>
        <updated>{updated}</updated>
        <summary>{html_escape(post['content'][:200])}</summary>
        <content type="html">{content}</content>
    </entry>
'''
    
    atom += '</feed>'
    
    return atom

def main():
    """Main generation function"""
    print("Building static blog...")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    # Copy CSS file
    import shutil
    if Path('style.css').exists():
        shutil.copy2('style.css', OUTPUT_DIR / 'style.css')
        print("Copied style.css")
    
    # Load posts
    posts = load_posts()
    print(f"Found {len(posts)} posts")
    
    if not posts:
        print("No posts found. Create some .txt files in the posts/ directory.")
        return
    
    # Generate index page
    index_html = generate_index(posts)
    with (OUTPUT_DIR / 'index.html').open('w', encoding='utf-8') as f:
        f.write(index_html)
    print("Generated index.html")
    
    # Generate individual post pages
    for post in posts:
        post_html = generate_post_page(post, posts)
        with (OUTPUT_DIR / f"{post['slug']}.html").open('w', encoding='utf-8') as f:
            f.write(post_html)
    print(f"Generated {len(posts)} post pages")
    
    # Generate RSS feed
    rss_xml = generate_rss(posts)
    with (OUTPUT_DIR / 'rss.xml').open('w', encoding='utf-8') as f:
        f.write(rss_xml)
    print("Generated rss.xml")
    
    # Generate Atom feed
    atom_xml = generate_atom(posts)
    with (OUTPUT_DIR / 'atom.xml').open('w', encoding='utf-8') as f:
        f.write(atom_xml)
    print("Generated atom.xml")
    
    print("Build complete!")

if __name__ == '__main__':
    main()