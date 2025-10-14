# Wanderlust & Wonder

A minimal, Hacker News-style personal blog about travels, discoveries, and life's beautiful moments. Generates static HTML with RSS feeds.

## Features

- **Zero dependencies** - Just Python 3 standard library
- **Static generation** - Fast loading, works everywhere
- **RSS & Atom feeds** - Automatic feed generation
- **Mobile responsive** - Clean, readable design
- **GitHub Pages ready** - Automatic deployment
- **Personal storytelling** - Perfect for travel and lifestyle content

## Usage

### Adding Posts

1. Create a new file in `posts/` directory:
   ```
   posts/2024-01-25-your-post-title.txt
   ```

2. Write your content in plain text:
   ```
   Weekend in Prague

   Just got back from an incredible weekend in Prague...

   - Visited the old town square
   - Found this amazing café near the castle
   - The architecture was breathtaking
   ```

3. Generate the site:
   ```bash
   python3 build.py
   ```

4. Commit and push to deploy

### File Naming

Posts must follow this format:
```
YYYY-MM-DD-title-with-dashes.txt
```

Example: `2024-01-25-vpn-setup-guide.txt`

### Content Format

- First line: Post title
- Rest: Content in plain text
- Lists: Use `- ` for bullet points
- No special syntax needed

## Deployment

### GitHub Pages

1. Push the repository to GitHub (for example as `<username>/blog`).
2. In the repository settings, enable **GitHub Pages** with the `docs/` folder as the source.
3. Your site will be available at:

   ```
   https://<username>.github.io/blog/
   ```

   Replace `<username>` with your GitHub account name. Once the first publish finishes, you can share that URL as the public link to the blog.

## Local Development

```bash
# Generate static site
python3 build.py

# View in browser
open docs/index.html
```

## RSS Feeds

- RSS 2.0: `/rss.xml`
- Atom 1.0: `/atom.xml`

Both feeds are automatically generated and include the latest 10 posts.