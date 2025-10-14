# Simple VPN Blog

A minimal, Hacker News-style blog for VPN service content. Generates static HTML with RSS feeds.

## Features

- **Zero dependencies** - Just Python 3 standard library
- **Static generation** - Fast loading, works everywhere
- **RSS & Atom feeds** - Automatic feed generation
- **Mobile responsive** - Clean, readable design
- **GitHub Pages ready** - Automatic deployment

## Usage

### Adding Posts

1. Create a new file in `posts/` directory:
   ```
   posts/2024-01-25-your-post-title.txt
   ```

2. Write your content in plain text:
   ```
   Your Post Title

   Your content here...

   - Bullet points work
   - Just use dashes
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

The blog automatically deploys to GitHub Pages when you push to the `main` branch.

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