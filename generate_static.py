import os
import markdown
from pathlib import Path

POSTS_DIR = Path('posts')
OUTPUT_DIR = Path('docs')
POSTS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

posts = []
for md_file in sorted(POSTS_DIR.glob('*.md')):
    with md_file.open('r', encoding='utf-8') as f:
        lines = f.read().splitlines()
    if not lines:
        continue
    title_line = lines[0]
    title = title_line.lstrip('# ').strip()
    md_content = '\n'.join(lines)
    html_content = markdown.markdown(md_content)
    slug = md_file.stem
    posts.append({'title': title, 'slug': slug, 'content': html_content})

# generate individual post pages
for post in posts:
    with (OUTPUT_DIR / f"{post['slug']}.html").open('w', encoding='utf-8') as f:
        f.write(
            '<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">'
            f'<title>{post["title"]}</title>\n</head>\n<body>\n'
            f'{post["content"]}\n'
            '<p><a href="index.html">Назад к списку</a></p>\n'
            '</body>\n</html>'
        )

# generate index page
with (OUTPUT_DIR / 'index.html').open('w', encoding='utf-8') as f:
    f.write('<!doctype html>\n<html lang="ru">\n<head>\n<meta charset="utf-8">\n'
            '<title>Simple Blog</title>\n</head>\n<body>\n<h1>Simple Blog</h1>\n')
    if posts:
        for post in posts:
            f.write(f'<div>\n  <h2><a href="{post["slug"]}.html">{post["title"]}</a></h2>\n</div>\n')
    else:
        f.write('<p>No posts yet.</p>\n')
    f.write('</body>\n</html>')
