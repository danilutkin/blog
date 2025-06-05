import json
import os
from flask import Flask, render_template_string, request, redirect, url_for

DATA_FILE = 'posts.json'

app = Flask(__name__)


def load_posts():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_posts(posts):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


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
    <p>{{ post.content }}</p>
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
        posts.append({'title': title, 'content': content})
        save_posts(posts)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
