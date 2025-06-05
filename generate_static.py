import json
import os
import html

POSTS_FILE = 'posts.json'
OUTPUT_DIR = 'docs'

os.makedirs(OUTPUT_DIR, exist_ok=True)

posts = []
if os.path.exists(POSTS_FILE):
    with open(POSTS_FILE, 'r', encoding='utf-8') as f:
        posts = json.load(f)

with open(os.path.join(OUTPUT_DIR, 'index.html'), 'w', encoding='utf-8') as f:
    f.write('<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">\n<title>Simple Blog</title>\n</head>\n<body>\n<h1>Simple Blog</h1>\n')
    if posts:
        for post in posts:
            title = html.escape(post.get('title', ''))
            content = html.escape(post.get('content', ''))
            f.write(f'<div>\n  <h2>{title}</h2>\n  <p>{content}</p>\n</div>\n')
    else:
        f.write('<p>No posts yet.</p>\n')
    f.write('</body>\n</html>')
