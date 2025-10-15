# Wanderlust & Wonder

This repository holds a minimal static blog: plain text posts plus one small Python script that renders an index page, per-post pages, and a shared stylesheet.

## How it works

- Write stories as plain text or Markdown files in `posts/` (use the `.txt` or `.md` extension).
- Run `python3 build.py`.
- Open `docs/index.html` (the home page) or push to GitHub Pages.

The build step rewrites only three things: the home page, one HTML file per post, and `docs/style.css`.
Anything else left in `docs/` gets cleaned up automatically so the folder always mirrors the posts that exist.

## Writing a post

1. Create a new file whose name starts with the date:
   ```
   posts/2024-02-01-new-adventure.txt
   posts/2024-02-01-new-adventure.md
   ```
2. Put the title on the first non-empty line. If you're writing Markdown, you can optionally start with `# Title` and the build
   script will reuse the heading text.
3. The builder understands common Markdown touches like headings, inline code, emphasis, and lists (using `- ` or numbered
   lines).
4. Run `python3 build.py` to refresh the HTML files in `docs/`.

To delete a story, remove its file and rebuild.

## Local preview

```bash
python3 build.py
open docs/index.html  # or use any browser
```

## Deploying to GitHub Pages

Set the repository's Pages source to the `docs/` folder. Each time you rebuild and push, the index and post pages update automatically.
