#!/usr/bin/env python3
"""Static blog builder with minimal templates and per-post pages."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
import html
import re
from string import Template
from textwrap import shorten
from typing import Iterable

POSTS_DIR = Path("posts")
OUTPUT_DIR = Path("docs")
SITE_TITLE = "Wanderlust & Wonder"
SITE_TAGLINE = "Tiny stories from the road"
CONTACT_EMAIL = "hello@example.com"
SOCIAL_LINKS = {
    "GitHub": "https://github.com/example",
    "Mastodon": "https://hachyderm.io/@example",
    "Email": f"mailto:{CONTACT_EMAIL}",
}

TEMPLATES_DIR = Path("templates")


TEMPLATE_CACHE: dict[str, Template] = {}

ABOUT_MARKDOWN = """
I’m Alex, the traveler behind Wanderlust & Wonder. This blog doubles as my field journal—short dispatches from trains, ferries, and late-night cafés when the day’s impressions are still warm.

### What you can expect
- Sensory snapshots from the road, not bucket lists.
- Honest notes about logistics so future-me remembers what actually worked.
- Occasional sketches of people met along the way.

### How the site is built
Everything you read is rendered from plain text files by a tiny Python script. No frameworks, no databases—just durable HTML optimized for fast, accessible reading.

If you spot something that needs clarity, reply via email and it will wind up in the next revision.
"""

ARCHIVE_BLURB = "Every story published so far, organized by the year it was captured."

POST_FILENAME = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2})-(?P<slug>.+)\.(?P<ext>txt|md)$"
)

@dataclass
class Heading:
    level: int
    text: str
    anchor: str


@dataclass
class RenderedBody:
    html: str
    headings: list[Heading] = field(default_factory=list)


@dataclass
class Post:
    title: str
    date: date
    slug: str
    summary: str
    description: str
    body_html: str
    headings: list[Heading]

    @property
    def filename(self) -> str:
        return f"{self.slug}.html"

    @property
    def iso_date(self) -> str:
        return self.date.isoformat()


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
    rendered = render_body(body)
    summary = extract_summary(body)
    description = shorten(summary, width=155, placeholder="…") if summary else title

    return Post(
        title=title,
        date=date,
        slug=slug,
        summary=summary or title,
        description=description,
        body_html=rendered.html,
        headings=rendered.headings,
    )


AUTOLINK_RE = re.compile(r"(?P<url>[a-z][a-z0-9+.-]*://[^\s<]+)", flags=re.IGNORECASE)


def get_template(name: str) -> Template:
    template = TEMPLATE_CACHE.get(name)
    if template is None:
        path = TEMPLATES_DIR / name
        TEMPLATE_CACHE[name] = template = Template(path.read_text(encoding="utf-8"))
    return template


def render_social_links() -> str:
    items: list[str] = []
    for label, url in SOCIAL_LINKS.items():
        items.append(
            "<li>"
            f"<a href=\"{html.escape(url, quote=True)}\" "
            "class=\"group inline-flex items-center gap-2 text-sm font-medium text-neutral-600 transition-transform duration-200 hover:translate-x-1 hover:text-neutral-900 dark:text-neutral-300 dark:hover:text-white\">"
            f"{html.escape(label)}"
            "<span aria-hidden=\"true\" class=\"transition-transform duration-200 group-hover:translate-x-1\">→</span>"
            "</a>"
            "</li>"
        )
    return "\n".join(items)


def render_page(
    template_name: str,
    *,
    page_title: str,
    description: str,
    canonical: str | None = None,
    **context: str,
) -> str:
    base_template = get_template("base.html")
    body_template = get_template(template_name)

    body_context = {
        "site_name": SITE_TITLE,
        "site_tagline": SITE_TAGLINE,
        **context,
    }
    body_html = body_template.substitute(body_context)

    meta_extra: list[str] = []
    if canonical:
        meta_extra.append(
            f"<link rel=\"canonical\" href=\"{html.escape(canonical, quote=True)}\">"
        )

    return base_template.substitute(
        page_title=html.escape(page_title),
        meta_description=html.escape(description),
        meta_extra="\n".join(meta_extra),
        site_name=SITE_TITLE,
        site_tagline=SITE_TAGLINE,
        contact_email=html.escape(CONTACT_EMAIL),
        footer_links=render_social_links(),
        current_year=str(date.today().year),
        body=body_html,
    )


def extract_plain_text(markup: str) -> str:
    text = markup
    text = re.sub(r"\(\(([^:()]+)::([^()]+)\)\)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_summary(body: str) -> str:
    for paragraph in body.split("\n\n"):
        clean = extract_plain_text(paragraph)
        if clean:
            return clean
    return ""


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower())
    slug = slug.strip("-")
    return slug or "section"


def render_body(body: str) -> RenderedBody:
    if not body:
        return RenderedBody(html="", headings=[])

    context = RenderContext()
    blocks: list[str] = []
    paragraph_lines: list[str] = []
    list_items: list[list[str]] = []
    list_type: str | None = None
    in_code_fence = False
    code_lines: list[str] = []
    headings: list[Heading] = []
    heading_counts: dict[str, int] = {}

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
            blocks.append(
                "<pre class=\"mt-8 overflow-x-auto rounded-3xl bg-neutral-950 text-neutral-50 shadow-xl ring-1 ring-white/10 dark:bg-neutral-900 dark:text-neutral-50 dark:ring-white/10\">"
                "<code class=\"block font-mono text-sm leading-6\">"
                + code_html
                + "</code></pre>"
            )
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
            inline_html = render_inlines(content, context)
            plain_text = extract_plain_text(content)
            anchor_base = slugify(plain_text)
            count = heading_counts.get(anchor_base, 0)
            heading_counts[anchor_base] = count + 1
            anchor = anchor_base if count == 0 else f"{anchor_base}-{count}"
            blocks.append(f"<h{level} id=\"{anchor}\">{inline_html}</h{level}>")
            headings.append(Heading(level=level, text=plain_text, anchor=anchor))
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

    return RenderedBody(html="\n".join(blocks), headings=headings)


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
                            "<span class=\"inline-flex items-center gap-1 align-baseline\">"
                            f"<button type=\"button\" class=\"underline decoration-dotted underline-offset-4 transition-colors duration-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-500\" popovertarget=\"{popover_id}\">{html.escape(term_raw)}</button>"
                            f"<aside id=\"{popover_id}\" class=\"z-20 max-w-xs rounded-2xl border border-neutral-200/70 bg-white/95 p-4 text-sm leading-6 text-neutral-700 shadow-xl backdrop-blur-lg dark:border-white/10 dark:bg-neutral-900/95 dark:text-neutral-100\" popover=\"auto\" role=\"note\">"
                            f"<strong class=\"block text-sm font-semibold text-neutral-900 dark:text-neutral-100\">{html.escape(term_raw)}</strong>"
                            f"<span class=\"mt-2 block text-sm text-neutral-600 dark:text-neutral-200\">{definition_html}</span>"
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


def render_post_cards(posts: Iterable[Post]) -> str:
    cards: list[str] = []
    for post in posts:
        cards.append(
            f'<article class="group relative flex h-full flex-col justify-between rounded-3xl border border-neutral-200/70 bg-white/80 p-6 shadow-sm backdrop-blur transition-transform duration-300 hover:-translate-y-0.5 hover:shadow-xl motion-reduce:transform-none motion-reduce:shadow-none dark:border-neutral-800/60 dark:bg-white/5">'
            '<div class="flex flex-col gap-4">'
            f'<p class="text-xs font-semibold uppercase tracking-[0.3em] text-neutral-500 dark:text-neutral-400"><time datetime="{post.iso_date}">{html.escape(post.date.strftime("%B %d, %Y"))}</time></p>'
            f'<h2 class="text-2xl font-semibold leading-tight text-neutral-900 dark:text-white"><a href="{post.slug}.html" class="inline-flex items-center gap-2 transition-transform duration-200 group-hover:translate-x-1">{html.escape(post.title)}<span aria-hidden="true" class="text-lg">→</span></a></h2>'
            f'<p class="text-base text-neutral-600 dark:text-neutral-300">{html.escape(post.summary)}</p>'
            '</div>'
            '<div class="mt-6 flex items-center justify-between">'
            f'<a href="{post.slug}.html" class="inline-flex items-center gap-2 text-sm font-semibold text-neutral-700 transition-transform duration-200 hover:translate-x-1 hover:text-neutral-900 dark:text-neutral-200 dark:hover:text-white" aria-label="Read {html.escape(post.title)}">Read<span aria-hidden="true">→</span></a>'
            '</div>'
            '</article>'
        )
    return "\n".join(cards)


def render_toc(headings: Iterable[Heading]) -> str:
    items: list[str] = []
    for heading in headings:
        if heading.level <= 1 or heading.level > 4:
            continue
        indent = max(0, min(heading.level - 2, 3))
        padding = ["pl-0", "pl-4", "pl-8", "pl-12"][indent]
        items.append(
            f'<li class="{padding}"><a href="#{heading.anchor}" class="inline-flex items-center gap-2 text-sm font-medium text-neutral-600 transition-transform duration-200 hover:translate-x-1 hover:text-neutral-900 dark:text-neutral-300 dark:hover:text-white">{html.escape(heading.text)}</a></li>'
        )

    if not items:
        return ""

    nav_html = (
        '<nav aria-label="Table of contents" class="lg:sticky lg:top-24 rounded-2xl border border-neutral-200/70 bg-white/80 p-6 text-sm text-neutral-600 shadow-sm backdrop-blur dark:border-neutral-800/60 dark:bg-white/5 dark:text-neutral-300">'
        '<h2 class="text-xs font-semibold uppercase tracking-[0.3em] text-neutral-500 dark:text-neutral-400">On this page</h2>'
        '<ol class="mt-4 space-y-2">'
        + ''.join(items)
        + '</ol></nav>'
    )
    return f'<aside class="hidden lg:block lg:w-64 lg:flex-none">{nav_html}</aside>'


def render_related_posts(posts: Iterable[Post]) -> str:
    selection = [post for post in posts][:3]
    if not selection:
        return ""

    items: list[str] = []
    for post in selection:
        items.append(
            f'<li class="group rounded-2xl border border-neutral-200/70 bg-white/60 p-5 shadow-sm backdrop-blur transition-transform duration-200 hover:-translate-y-0.5 hover:shadow-lg motion-reduce:transform-none motion-reduce:shadow-none dark:border-neutral-800/60 dark:bg-white/5">'
            f'<p class="text-xs font-semibold uppercase tracking-[0.2em] text-neutral-500 dark:text-neutral-400"><time datetime="{post.iso_date}">{html.escape(post.date.strftime("%b %d, %Y"))}</time></p>'
            f'<a href="{post.slug}.html" class="mt-2 inline-flex items-center gap-2 text-base font-semibold text-neutral-800 transition-transform duration-200 hover:translate-x-1 dark:text-neutral-100">{html.escape(post.title)}<span aria-hidden="true">→</span></a>'
            f'<p class="mt-3 text-sm text-neutral-600 dark:text-neutral-300">{html.escape(post.description)}</p>'
            '</li>'
        )

    return (
        '<section class="mt-16 border-t border-neutral-200/70 pt-10 dark:border-neutral-800/60">'
        '<h2 class="text-sm font-semibold uppercase tracking-[0.3em] text-neutral-500 dark:text-neutral-400">Keep reading</h2>'
        '<ul class="mt-6 grid gap-6 sm:grid-cols-2">'
        + ''.join(items)
        + '</ul></section>'
    )


def render_index(posts: Iterable[Post]) -> str:
    post_list = list(posts)
    cards_html = render_post_cards(post_list)
    if not cards_html:
        cards_html = (
            '<div class="rounded-3xl border border-dashed border-neutral-300 bg-white/60 p-10 text-center text-neutral-500 backdrop-blur dark:border-neutral-800 dark:bg-white/5 dark:text-neutral-300">'
            '<p class="text-base">No stories yet. Drop a markdown file into posts/ to publish your first dispatch.</p>'
            '</div>'
        )

    return render_page(
        'index.html',
        page_title=f'{SITE_TITLE} · {SITE_TAGLINE}',
        description=SITE_TAGLINE,
        post_grid=cards_html,
    )


def render_post_page(post: Post, posts: Iterable[Post]) -> str:
    toc_panel = render_toc(post.headings)
    related_html = render_related_posts([p for p in posts if p.slug != post.slug])

    return render_page(
        'post.html',
        page_title=f'{post.title} · {SITE_TITLE}',
        description=post.description,
        post_title=html.escape(post.title),
        post_date=html.escape(post.date.strftime("%B %d, %Y")),
        post_iso_date=post.iso_date,
        article_body=post.body_html,
        toc_panel=toc_panel,
        related_posts=related_html,
    )


def render_about_page() -> str:
    rendered = render_body(ABOUT_MARKDOWN)
    description = extract_summary(ABOUT_MARKDOWN)
    return render_page(
        'about.html',
        page_title=f'About · {SITE_TITLE}',
        description=description or SITE_TAGLINE,
        about_title='About Wanderlust & Wonder',
        about_body=rendered.html,
    )


def render_archive_page(posts: Iterable[Post]) -> str:
    post_list = list(posts)
    by_year: dict[int, list[Post]] = {}
    for post in post_list:
        by_year.setdefault(post.date.year, []).append(post)

    sections: list[str] = []
    for year in sorted(by_year.keys(), reverse=True):
        entries: list[str] = []
        for entry in sorted(by_year[year], key=lambda item: item.date, reverse=True):
            excerpt = shorten(entry.summary, width=120, placeholder='…')
            entries.append(
                f'<li class="flex flex-col gap-2 rounded-2xl border border-transparent p-4 transition-colors duration-200 hover:border-neutral-200/70 dark:hover:border-neutral-800/60">'
                f'<a href="{entry.slug}.html" class="inline-flex items-center gap-2 text-base font-semibold text-neutral-800 transition-transform duration-200 hover:translate-x-1 dark:text-neutral-100">{html.escape(entry.title)}<span aria-hidden="true">→</span></a>'
                f'<p class="text-sm text-neutral-500 dark:text-neutral-400"><time datetime="{entry.iso_date}">{html.escape(entry.date.strftime("%B %d, %Y"))}</time> · {html.escape(excerpt)}</p>'
                '</li>'
            )

        section_html = (
            f'<section class="space-y-4">'
            f'<h2 class="text-lg font-semibold tracking-tight text-neutral-900 dark:text-white">{year}</h2>'
            '<ul class="grid gap-4 md:grid-cols-2">'
            + ''.join(entries)
            + '</ul></section>'
        )
        sections.append(section_html)

    archive_body = (
        ''.join(sections)
        if sections
        else '<p class="text-neutral-500 dark:text-neutral-300">No stories in the archive yet.</p>'
    )

    return render_page(
        'archive.html',
        page_title=f'Archive · {SITE_TITLE}',
        description=ARCHIVE_BLURB,
        archive_body=archive_body,
        archive_count=str(len(post_list)),
        archive_body_lede=ARCHIVE_BLURB,
    )

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

    keep_files = {"index.html", "about.html", "archive.html"}

    write_file(OUTPUT_DIR / "index.html", render_index(posts))
    write_file(OUTPUT_DIR / "about.html", render_about_page())
    write_file(OUTPUT_DIR / "archive.html", render_archive_page(posts))

    for post in posts:
        keep_files.add(post.filename)
        write_file(OUTPUT_DIR / post.filename, render_post_page(post, posts))

    clean_output_dir(keep_files)

    print(
        f"Generated {len(posts)} post page(s) plus index.html, about.html, and archive.html"
    )


if __name__ == "__main__":
    build()
