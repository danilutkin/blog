import os
import re
from pathlib import Path

import markdown
from flask import Flask, render_template_string, request, redirect, url_for

POSTS_DIR = Path('posts')
POSTS_DIR.mkdir(exist_ok=True)

app = Flask(__name__)


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", '-', text)
    text = re.sub(r"[^a-z0-9\-а-яё]", '', text)
    return text


def load_posts():
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
        posts.append({'title': title, 'slug': md_file.stem, 'content': html_content})
    return posts


posts = load_posts()


@app.route('/')
def index():
    return render_template_string(
        '''<!doctype html>
<title>Simple Blog</title>
<h1>Simple Blog</h1>
{% for post in posts %}
  <div>
    <h2>{{ post.title }}</h2>
    {{ post.content|safe }}
  </div>
{% else %}
  <p>No posts yet.</p>
{% endfor %}
<h2>Add post</h2>
<form method="post" action="/add">
  <p><input name="title" placeholder="Title"></p>
  <p><textarea name="content" placeholder="Content"></textarea></p>
  <p><button type="submit">Add</button></p>
</form>
''', posts=posts)


@app.route('/add', methods=['POST'])
def add():
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    if title and content:
        slug = slugify(title)
        md_file = POSTS_DIR / f"{slug}.md"
        with md_file.open('w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n{content}\n")
        global posts
        posts = load_posts()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
