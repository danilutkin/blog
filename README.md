# Wanderlust & Wonder

A premium static travel blog powered by one Python script and Tailwind CSS via CDN. Content lives in plain-text files, rendering to production-ready HTML in `docs/` for GitHub Pages.

## Quick start

1. Write posts inside `posts/` using the filename pattern `YYYY-MM-DD-slug.txt` (Markdown is also accepted).
2. Put the title on the first non-empty line; the rest of the file becomes the body.
3. Run:
   ```bash
   python3 build.py
   ```
4. Open `docs/index.html` locally or push the repo — GitHub Pages can publish the `docs/` directory as-is.

Removing a post is as simple as deleting its file and running `build.py` again. The builder also cleans up stale HTML in `docs/`.

## Design system & theming

- Tailwind CSS (CDN) + Typography plugin drive all styling — no custom stylesheet.
- Light and dark themes respect `prefers-color-scheme`.
- Responsive layouts feature a glassmorphism hero, sticky nav, and bento grid cards with hover microinteractions that fall back gracefully with `prefers-reduced-motion`.
- Post pages use Tailwind `prose` typography, dark code blocks, and an optional sticky table of contents on large screens.

## Templates

Shared UI lives in `templates/`:

- `base.html` — HTML shell, meta tags, navigation, and footer.
- `index.html` — hero section plus the responsive post grid.
- `post.html` — article layout, sticky TOC placeholder, and related posts block.
- `about.html` — long-form introduction and design philosophy.
- `archive.html` — year-grouped catalog of every story.

The builder injects content into these templates using Python’s `string.Template`. Adjusting layout or Tailwind classes happens in these files.

## Generator data model

Each post becomes:

- `title`: derived from the first non-empty line or Markdown heading.
- `date`: parsed from the filename (`YYYY-MM-DD`).
- `slug`: filename slug reused for URLs.
- `summary`: first paragraph of body text (markdown stripped).
- `description`: summary trimmed to ~155 characters (used for meta tags).
- `body_html`: HTML rendered from the post body (headings receive IDs, code blocks styled).
- `headings`: list of `{level, text, anchor}` for building the table of contents.

These fields drive the home page cards, metadata, table of contents, and related posts list.

## Output structure

Running `python3 build.py` produces:

```
├── docs/
│   ├── index.html      # Home page with hero + post grid
│   ├── about.html      # About page rendered from template content
│   ├── archive.html    # Yearly archive with summaries
│   └── *.html          # One page per post (same slug as source file)
├── posts/              # Plain text source files (inputs)
├── templates/          # Base + page-specific templates
└── build.py            # Static-site generator
```

GitHub Pages can point directly at `docs/`. No additional build step or runtime dependencies are required.
