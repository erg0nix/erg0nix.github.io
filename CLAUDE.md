# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Local Development
```bash
# Run development server with live reload
hugo server

# Build for production
hugo

# Build with minification (production equivalent)
hugo --minify
```

### Testing and Validation
No formal test suite exists. Manual testing involves:
- Running `hugo server` and checking the site at http://localhost:1313
- Verifying responsive design on mobile and desktop
- Checking that all navigation links work correctly

## Repository Structure

This is a Hugo static site with a custom terminal-inspired theme. The site is deployed automatically to GitHub Pages via GitHub Actions.

### Key Directories
- `content/` - Markdown content files organized by section
  - `_index.md` - Homepage content
  - `blog/` - Blog posts
  - `projects/` - Projects section
  - `bookmarks/` - Bookmarks section
- `layouts/` - Hugo template files
  - `_default/baseof.html` - Base template with sidebar layout
  - `partials/head.html` - Contains all CSS styling inline
- `static/` - Static assets (images, favicons)

### Template Architecture
- **Single template design**: All CSS is embedded in `layouts/partials/head.html` 
- **Responsive layout**: Flexbox-based layout with mobile-first approach
- **Terminal aesthetic**: Monospace fonts, neon colors, animated gradient background with snow effect
- **Sidebar layout**: Fixed sidebar with profile info and navigation on desktop, collapsible on mobile

### Content Patterns
- All content uses Markdown with Hugo front matter
- Section pages use `_index.md` files
- Blog posts follow standard Hugo blog structure
- Custom terminal-style navigation with tilde prefix (`~/projects`, `~/blog`)

## Hugo Configuration

Key settings in `hugo.toml`:
- Uses `github-dark` syntax highlighting
- Unsafe HTML rendering enabled for custom styling
- RSS feed generation enabled
- Base URL configured for GitHub Pages deployment

## Deployment

- **Auto-deployment**: GitHub Actions workflow deploys to GitHub Pages on push to `main`
- **Hugo version**: 0.128.0 (specified in workflow)
- **Build process**: Uses `hugo --minify` for production builds
- **Domain**: Site available at https://ergonix.dev (custom domain with Cloudflare)

## Theme Customization

The site uses a custom theme with these design principles:
- Terminal/retro aesthetic with pixelated avatar
- Dark theme with neon accent colors
- Animated gradient background with snow particles
- System info sidebar mimicking terminal output
- Mobile-responsive design with collapsible navigation

All styling is contained in a single `<style>` block in `head.html` for simplicity and performance.