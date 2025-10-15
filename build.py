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


AUTOLINK_RE = re.compile(r"(?P<url>[a-z][a-z0-9+.-]*://[^\s<]+)", flags=re.IGNORECASE)


def render_body(body: str) -> str:
    if not body:
        return ""

    blocks: list[str] = []
    paragraph_lines: list[str] = []
    list_items: list[list[str]] = []
    list_type: str | None = None
    in_code_fence = False
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            text = " ".join(paragraph_lines)
            blocks.append(f"<p>{render_inlines(text)}</p>")
            paragraph_lines = []

    def flush_list() -> None:
        nonlocal list_items, list_type
        if list_type and list_items:
            tag = "ul" if list_type == "unordered" else "ol"
            items_html = "".join(
                f"<li>{' '.join(parts)}</li>" for parts in list_items
            )
            blocks.append(f"<{tag}>" + items_html + f"</{tag}>")
        list_items = []
        list_type = None

    def flush_code() -> None:
        nonlocal code_lines
        if code_lines:
            code_html = "\n".join(html.escape(line) for line in code_lines)
            blocks.append(f"<pre><code>{code_html}</code></pre>")
            code_lines = []

    for raw_line in body.splitlines():
        line = raw_line.rstrip("\n")

        if in_code_fence:
            if line.strip().startswith("```"):
                in_code_fence = False
                flush_code()
            else:
                code_lines.append(line)
            continue

        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            in_code_fence = True
            code_lines = []
            continue

        if not stripped:
            flush_paragraph()
            continue

        bullet_match = re.match(r"^([-*+])\s+(.*)$", stripped)
        ordered_match = re.match(r"^(\d+)[.)]\s+(.*)$", stripped)

        if bullet_match:
            flush_paragraph()
            if list_type not in (None, "unordered"):
                flush_list()
            list_type = "unordered"
            list_items.append([render_inlines(bullet_match.group(2))])
            continue

        if ordered_match:
            flush_paragraph()
            if list_type not in (None, "ordered"):
                flush_list()
            list_type = "ordered"
            list_items.append([render_inlines(ordered_match.group(2))])
            continue

        if list_type and raw_line.startswith(" ") and list_items:
            list_items[-1].append(render_inlines(stripped))
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            flush_paragraph()
            flush_list()
            level = len(heading_match.group(1))
            content = heading_match.group(2).strip()
            blocks.append(f"<h{level}>{render_inlines(content)}</h{level}>")
            continue

        if list_type:
            flush_list()
        paragraph_lines.append(stripped)

    if in_code_fence:
        # Unclosed fence: treat captured lines as literal code.
        in_code_fence = False
        flush_code()

    flush_paragraph()
    flush_list()

    return "\n".join(blocks)


def linkify(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        url = match.group("url")
        escaped = html.escape(url)
        href = html.escape(url, quote=True)
        return f"<a href=\"{href}\">{escaped}</a>"

    return AUTOLINK_RE.sub(repl, text)


def render_inlines(text: str) -> str:
    segments: list[str] = []
    i = 0
    length = len(text)
    plain_buffer: list[str] = []

    def flush_plain() -> None:
        if plain_buffer:
            combined = "".join(plain_buffer)
            escaped = linkify(html.escape(combined))
            segments.append(escaped)
            plain_buffer.clear()

    while i < length:
        if text.startswith("**", i):
            end = text.find("**", i + 2)
            if end != -1:
                flush_plain()
                content = text[i + 2 : end]
                segments.append(f"<strong>{render_inlines(content)}</strong>")
                i = end + 2
                continue
        if text.startswith("*", i):
            end = text.find("*", i + 1)
            if end != -1:
                flush_plain()
                content = text[i + 1 : end]
                segments.append(f"<em>{render_inlines(content)}</em>")
                i = end + 1
                continue
        if text.startswith("`", i):
            end = text.find("`", i + 1)
            if end != -1:
                flush_plain()
                code_content = text[i + 1 : end]
                segments.append(f"<code>{html.escape(code_content)}</code>")
                i = end + 1
                continue
        if text.startswith("[", i):
            close_bracket = text.find("]", i + 1)
            if close_bracket != -1 and close_bracket + 1 < length and text[close_bracket + 1] == "(":
                close_paren = text.find(")", close_bracket + 2)
                if close_paren != -1:
                    flush_plain()
                    label = text[i + 1 : close_bracket]
                    url = text[close_bracket + 2 : close_paren]
                    segments.append(
                        f"<a href=\"{html.escape(url, quote=True)}\">{render_inlines(label)}</a>"
                    )
                    i = close_paren + 1
                    continue

        plain_buffer.append(text[i])
        i += 1

    flush_plain()

    return "".join(segments)


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
