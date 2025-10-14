#!/usr/bin/env python3
"""Static blog builder with minimal templates and per-post pages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import html
import re
from typing import Iterable

POSTS_DIR = Path("posts")
OUTPUT_DIR = Path("docs")
SITE_TITLE = "Wanderlust & Wonder"
SITE_TAGLINE = "Tiny stories from the road"
STYLE_NAME = "style.css"

POST_FILENAME = re.compile(r"(?P<date>\d{4}-\d{2}-\d{2})-(?P<slug>.+)\.txt$")

STYLE_CONTENT = """/* Tiny, readable defaults */
:root {
  color-scheme: light dark;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.6;
  margin: 0;
}
body {
  background-color: #f5f5f5;
  margin: 0 auto;
  max-width: 48rem;
  padding: 2.5rem 1.5rem 4rem;
}
a {
  color: inherit;
}
header,
footer {
  text-align: center;
  margin-bottom: 2.5rem;
}
nav a {
  text-decoration: none;
  font-weight: 600;
}
article {
  margin-bottom: 3rem;
}
.post-date {
  color: #666;
  font-size: 0.9rem;
  margin-top: -0.5rem;
}
ul {
  padding-left: 1.2rem;
}
pre,
code {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}
"""


@dataclass
class Post:
    title: str
    date: date
    slug: str
    body: str
    body_html: str

    @property
    def filename(self) -> str:
        return f"{self.slug}.html"


def parse_post(path: Path) -> Post | None:
    match = POST_FILENAME.match(path.name)
    if not match:
        return None

    date_str = match.group("date")
    slug = match.group("slug")

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None

    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return None

    lines = raw.splitlines()
    title = lines[0].strip() if lines else slug.replace("-", " ").title()
    body = "\n".join(lines[1:]).strip()
    body_html = render_body(body)

    return Post(title=title, date=date, slug=slug, body=body, body_html=body_html)


def render_body(body: str) -> str:
    if not body:
        return ""

    blocks: list[str] = []
    buffer: list[str] = []
    in_list = False

    def flush_paragraph() -> None:
        nonlocal buffer
        if buffer:
            text = " ".join(buffer)
            blocks.append(f"<p>{html.escape(text)}</p>")
            buffer = []

    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            if in_list:
                blocks.append("</ul>")
                in_list = False
            flush_paragraph()
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            if not in_list:
                blocks.append("<ul>")
                in_list = True
            blocks.append(f"<li>{html.escape(stripped[2:])}</li>")
            continue

        if in_list:
            blocks.append("</ul>")
            in_list = False

        buffer.append(stripped)

    if in_list:
        blocks.append("</ul>")
    flush_paragraph()

    return "\n".join(blocks)


def load_posts() -> list[Post]:
    posts: list[Post] = []
    if not POSTS_DIR.exists():
        return posts

    for path in sorted(POSTS_DIR.glob("*.txt")):
        post = parse_post(path)
        if post:
            posts.append(post)

    posts.sort(key=lambda post: post.date, reverse=True)
    return posts


def render_post_page(post: Post) -> str:
    title = html.escape(post.title)
    date_str = post.date.strftime("%B %d, %Y")
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<meta charset=\"utf-8\">
<title>{title} – {html.escape(SITE_TITLE)}</title>
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<link rel=\"stylesheet\" href=\"{STYLE_NAME}\">
<body>
<header>
  <p><a href=\"index.html\">{html.escape(SITE_TITLE)}</a></p>
  <p>{html.escape(SITE_TAGLINE)}</p>
</header>
<main>
  <article>
    <h1>{title}</h1>
    <p class=\"post-date\">{html.escape(date_str)}</p>
    {post.body_html}
  </article>
</main>
<footer>
  <p><a href=\"index.html\">Back to all stories</a></p>
</footer>
</body>
</html>
"""


def first_paragraph_html(body_html: str) -> str | None:
    match = re.search(r"<p>(.*?)</p>", body_html, flags=re.DOTALL)
    if match:
        return match.group(0)
    match = re.search(r"<li>(.*?)</li>", body_html, flags=re.DOTALL)
    if match:
        return f"<p>{match.group(1)}</p>"
    return None


def render_index(posts: Iterable[Post]) -> str:
    items: list[str] = []
    for post in posts:
        title = html.escape(post.title)
        date_str = html.escape(post.date.strftime("%B %d, %Y"))
        summary = first_paragraph_html(post.body_html) or ""
        summary_html = summary if summary else ""
        items.append(
            """
    <article>
      <h2><a href=\"{slug}.html\">{title}</a></h2>
      <p class=\"post-date\">{date}</p>
      {summary}
    </article>
            """.strip().format(slug=post.slug, title=title, date=date_str, summary=summary_html)
        )

    posts_html = "\n".join(items) if items else "<p>No stories yet. Add a text file to posts/.</p>"

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<meta charset=\"utf-8\">
<title>{html.escape(SITE_TITLE)}</title>
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<link rel=\"stylesheet\" href=\"{STYLE_NAME}\">
<body>
<header>
  <h1>{html.escape(SITE_TITLE)}</h1>
  <p>{html.escape(SITE_TAGLINE)}</p>
</header>
<main>
{posts_html}
</main>
<footer>
  <p>Built with plain text files and a small Python script.</p>
</footer>
</body>
</html>
"""


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def clean_output_dir(keep: set[str]) -> None:
    for path in OUTPUT_DIR.glob("**/*"):
        if path.is_dir():
            continue
        rel = path.relative_to(OUTPUT_DIR).as_posix()
        if rel not in keep:
            path.unlink()
    # remove empty directories
    for path in sorted(OUTPUT_DIR.glob("**/*"), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def build() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    posts = load_posts()

    keep_files = {"index.html", STYLE_NAME}

    write_file(OUTPUT_DIR / STYLE_NAME, STYLE_CONTENT.strip() + "\n")
    write_file(OUTPUT_DIR / "index.html", render_index(posts))

    for post in posts:
        keep_files.add(post.filename)
        write_file(OUTPUT_DIR / post.filename, render_post_page(post))

    clean_output_dir(keep_files)

    print(f"Generated {len(posts)} post page(s) and index.html")


if __name__ == "__main__":
    build()
