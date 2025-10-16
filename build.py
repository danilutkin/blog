#!/usr/bin/env python3
"""Static blog builder with minimal templates and per-post pages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import html
import json
import re
from typing import Iterable

POSTS_DIR = Path("posts")
OUTPUT_DIR = Path("docs")
SITE_TITLE = "Wanderlust & Wonder"
SITE_TAGLINE = "Tiny stories from the road"
STYLE_NAME = "style.css"

POST_FILENAME = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2})-(?P<slug>.+)\.(?P<ext>txt|md)$"
)

STYLE_CONTENT = """/* Tiny, readable defaults with modern touches */
:root {
  color-scheme: light dark;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.6;
  margin: 0;
  --surface: color-mix(in srgb, Canvas 92%, CanvasText 8%);
  --surface-border: color-mix(in srgb, CanvasText 20%, transparent);
  --card-radius: 1.1rem;
}
body {
  background: color-mix(in srgb, Canvas 98%, CanvasText 3%);
  margin: 0 auto;
  max-width: 52rem;
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
main.feed {
  display: grid;
  gap: 2rem;
}
.post-card {
  background: var(--surface);
  border: 1px solid var(--surface-border);
  border-radius: var(--card-radius);
  box-shadow: 0 1rem 2rem -1.5rem color-mix(in srgb, CanvasText 40%, transparent);
  padding: 1.75rem;
  transition: transform 150ms ease, box-shadow 150ms ease;
}
.post-card:hover,
.post-card:focus-within {
  transform: translateY(-4px);
  box-shadow: 0 1.35rem 2.75rem -1.5rem color-mix(in srgb, CanvasText 45%, transparent);
}
.post-card h2 {
  margin: 0 0 0.35rem;
  font-size: clamp(1.4rem, 1.2rem + 0.5vw, 1.7rem);
}
.post-card > .post-date {
  color: color-mix(in srgb, CanvasText 55%, transparent);
  font-size: 0.9rem;
  margin: 0;
}
.post-card > p {
  margin-top: 0.9rem;
}
.post-date {
  color: color-mix(in srgb, CanvasText 55%, transparent);
  font-size: 0.9rem;
  margin-top: -0.25rem;
}
ul {
  padding-left: 1.2rem;
}
pre,
code {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}
.glossary-term {
  align-items: center;
  display: inline-flex;
  gap: 0.4rem;
}
.glossary-trigger {
  background: none;
  border: 0;
  border-bottom: 1px dashed currentColor;
  cursor: pointer;
  font: inherit;
  padding: 0;
  text-align: left;
}
.glossary-trigger:focus-visible {
  outline: 2px solid currentColor;
  outline-offset: 3px;
}
.glossary-popover {
  background: var(--surface);
  border: 1px solid var(--surface-border);
  border-radius: 0.75rem;
  box-shadow: 0 1.75rem 3rem -2rem color-mix(in srgb, CanvasText 40%, transparent);
  margin: 0;
  max-width: min(24rem, 80vw);
  padding: 1rem 1.25rem;
}
.glossary-popover:popover-open {
  animation: popover-in 120ms ease;
}
.glossary-popover strong {
  display: block;
  font-size: 0.95rem;
  margin-bottom: 0.4rem;
}
.glossary-definition {
  display: block;
  font-size: 0.95rem;
  line-height: 1.5;
}
@keyframes popover-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
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


@dataclass
class RenderContext:
    popover_index: int = 0

    def new_popover_id(self) -> str:
        self.popover_index += 1
        return f"glossary-popover-{self.popover_index}"


def parse_post(path: Path) -> Post | None:
    match = POST_FILENAME.match(path.name)
    if not match:
        return None

    date_str = match.group("date")
    slug = match.group("slug")
    ext = match.group("ext")

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None

    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        return None

    lines = raw.splitlines()
    title_line = ""
    body_start = 0
    for idx, line in enumerate(lines):
        if line.strip():
            title_line = line.strip()
            body_start = idx + 1
            break

    if not title_line:
        return None

    if ext == "md":
        heading_match = re.match(r"^#+\s*(.*)$", title_line)
        if heading_match and heading_match.group(1).strip():
            title_line = heading_match.group(1).strip()

    title = title_line or slug.replace("-", " ").title()
    body = "\n".join(lines[body_start:]).strip()
    body_html = render_body(body)

    return Post(title=title, date=date, slug=slug, body=body, body_html=body_html)


AUTOLINK_RE = re.compile(r"(?P<url>[a-z][a-z0-9+.-]*://[^\s<]+)", flags=re.IGNORECASE)


def render_body(body: str) -> str:
    if not body:
        return ""

    context = RenderContext()
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
            blocks.append(f"<p>{render_inlines(text, context)}</p>")
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
            list_items.append([render_inlines(bullet_match.group(2), context)])
            continue

        if ordered_match:
            flush_paragraph()
            if list_type not in (None, "ordered"):
                flush_list()
            list_type = "ordered"
            list_items.append([render_inlines(ordered_match.group(2), context)])
            continue

        if list_type and raw_line.startswith(" ") and list_items:
            list_items[-1].append(render_inlines(stripped, context))
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            flush_paragraph()
            flush_list()
            level = len(heading_match.group(1))
            content = heading_match.group(2).strip()
            blocks.append(f"<h{level}>{render_inlines(content, context)}</h{level}>")
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


def render_inlines(text: str, context: RenderContext) -> str:
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
                segments.append(f"<strong>{render_inlines(content, context)}</strong>")
                i = end + 2
                continue
        if text.startswith("*", i):
            end = text.find("*", i + 1)
            if end != -1:
                flush_plain()
                content = text[i + 1 : end]
                segments.append(f"<em>{render_inlines(content, context)}</em>")
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
        if text.startswith("((", i):
            end = text.find("))", i + 2)
            if end != -1:
                content = text[i + 2 : end]
                if "::" in content:
                    term_raw, definition_raw = (
                        part.strip() for part in content.split("::", 1)
                    )
                    if term_raw and definition_raw:
                        flush_plain()
                        popover_id = context.new_popover_id()
                        definition_html = render_inlines(definition_raw, context)
                        popover_html = (
                            f"<span class=\"glossary-term\">"
                            f"<button type=\"button\" class=\"glossary-trigger\" popovertarget=\"{popover_id}\">{html.escape(term_raw)}</button>"
                            f"<aside id=\"{popover_id}\" class=\"glossary-popover\" popover=\"auto\" role=\"note\">"
                            f"<strong>{html.escape(term_raw)}</strong>"
                            f"<span class=\"glossary-definition\">{definition_html}</span>"
                            "</aside>"
                            "</span>"
                        )
                        segments.append(popover_html)
                        i = end + 2
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
                        f"<a href=\"{html.escape(url, quote=True)}\">{render_inlines(label, context)}</a>"
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


def render_post_page(post: Post, posts: Iterable[Post]) -> str:
    title = html.escape(post.title)
    date_str = post.date.strftime("%B %d, %Y")
    iso_date = post.date.isoformat()

    peer_urls = ["index.html"]
    for other in posts:
        if other.slug != post.slug:
            peer_urls.append(f"{other.slug}.html")

    speculation_script = ""
    if peer_urls:
        rules = {
            "prefetch": [{"source": "list", "urls": peer_urls}],
            "prerender": [
                {"source": "list", "urls": peer_urls, "eagerness": "moderate"}
            ],
        }
        speculation_script = (
            "<script type=\"speculationrules\">\n"
            + json.dumps(rules, indent=2)
            + "\n</script>"
        )

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<meta charset=\"utf-8\">
<title>{title} – {html.escape(SITE_TITLE)}</title>
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<link rel=\"stylesheet\" href=\"{STYLE_NAME}\">
<body class=\"post\">
<header>
  <p><a href=\"index.html\">{html.escape(SITE_TITLE)}</a></p>
  <p>{html.escape(SITE_TAGLINE)}</p>
</header>
<main>
  <article>
    <h1>{title}</h1>
    <p class=\"post-date\"><time datetime=\"{iso_date}\">{html.escape(date_str)}</time></p>
    {post.body_html}
  </article>
</main>
<footer>
  <p><a href=\"index.html\">Back to all stories</a></p>
</footer>
{speculation_script}
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
    post_list = list(posts)
    items: list[str] = []
    for post in post_list:
        title = html.escape(post.title)
        date_str = html.escape(post.date.strftime("%B %d, %Y"))
        summary = first_paragraph_html(post.body_html) or ""
        summary_html = summary if summary else ""
        card_html = f"""
    <article class=\"post-card\">
      <template shadowroot=\"open\">
        <style>
          :host {{
            display: block;
          }}
          .card {{
            display: grid;
            gap: 0.75rem;
          }}
          header {{
            margin: 0;
          }}
          .meta {{
            margin: 0;
            font-size: 0.9rem;
            color: color-mix(in srgb, currentColor 55%, transparent);
          }}
          .summary {{
            display: grid;
            gap: 0.65rem;
          }}
          ::slotted(h2) {{
            margin: 0;
            font-size: clamp(1.4rem, 1.2rem + 0.5vw, 1.7rem);
          }}
          ::slotted(.post-date) {{
            margin: 0;
            font-size: 0.9rem;
            color: color-mix(in srgb, currentColor 55%, transparent);
          }}
          ::slotted(p) {{
            margin: 0;
          }}
        </style>
        <article class=\"card\" part=\"surface\">
          <header part=\"header\">
            <slot name=\"title\"></slot>
          </header>
          <div class=\"meta\" part=\"meta\">
            <slot name=\"date\"></slot>
          </div>
          <div class=\"summary\" part=\"summary\">
            <slot></slot>
          </div>
        </article>
      </template>
      <h2 slot=\"title\"><a href=\"{post.slug}.html\">{title}</a></h2>
      <p slot=\"date\" class=\"post-date\"><time datetime=\"{post.date.isoformat()}\">{date_str}</time></p>
      {summary_html}
    </article>
        """.strip()
        items.append(card_html)

    if not items:
        posts_html = "<p>No stories yet. Add a text file to posts/.</p>"
    else:
        posts_html = "\n".join(items)

    speculation_script = ""
    if post_list:
        urls = [f"{post.slug}.html" for post in post_list]
        rules = {
            "prefetch": [{"source": "list", "urls": urls}],
            "prerender": [
                {"source": "list", "urls": urls, "eagerness": "moderate"}
            ],
        }
        speculation_script = (
            "<script type=\"speculationrules\">\n"
            + json.dumps(rules, indent=2)
            + "\n</script>"
        )

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<meta charset=\"utf-8\">
<title>{html.escape(SITE_TITLE)}</title>
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
<link rel=\"stylesheet\" href=\"{STYLE_NAME}\">
<body class=\"home\">
<header>
  <h1>{html.escape(SITE_TITLE)}</h1>
  <p>{html.escape(SITE_TAGLINE)}</p>
</header>
<main class=\"feed\">
{posts_html}
</main>
<footer>
  <p>Built with plain text files and a small Python script.</p>
</footer>
{speculation_script}
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
        write_file(OUTPUT_DIR / post.filename, render_post_page(post, posts))

    clean_output_dir(keep_files)

    print(f"Generated {len(posts)} post page(s) and index.html")


if __name__ == "__main__":
    build()
