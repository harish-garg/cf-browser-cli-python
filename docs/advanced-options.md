# Advanced Crawl Options

When starting a crawl interactively, select **"Configure advanced options"** to access these parameter groups. In CLI mode, these map directly to command flags.

## Crawl Scope

Control how broadly the crawler follows links.

| Parameter | CLI Flag | Description |
|-----------|----------|-------------|
| `depth` | `--depth N` | Max link depth from the seed URL. `0` = only the seed page. |
| `source` | `--source TYPE` | Where to discover URLs: `all` (links + sitemaps), `sitemaps`, or `links` |
| `includeSubdomains` | `--subdomains` | Follow links to subdomains of the seed URL |
| `includeExternalLinks` | `--external-links` | Follow links to external domains |

## URL Patterns

Filter which URLs get crawled using wildcard patterns.

| Parameter | CLI Flag | Description |
|-----------|----------|-------------|
| `includePatterns` | `--include-patterns` | Only crawl URLs matching these patterns (e.g. `/blog/*`, `/docs/*`) |
| `excludePatterns` | `--exclude-patterns` | Skip URLs matching these patterns (e.g. `/admin/*`, `/api/*`) |

In interactive mode, enter patterns as comma-separated values.

## Output Formats

Choose what content to capture for each page.

| Format | Description |
|--------|-------------|
| `html` | Raw HTML of each page |
| `markdown` | Cleaned markdown conversion |
| `json` | AI-extracted structured data (requires a prompt and/or schema) |

When `json` is selected, you can provide:
- **AI extraction prompt** — describe what data to extract (e.g. "Extract the title, date, and summary")
- **JSON schema file** — path to a JSON schema that defines the expected output structure

Output is saved per-page and as combined files. See the output structure in the main README.

## Page Rendering

Control browser rendering behavior.

| Parameter | CLI Flag | Description |
|-----------|----------|-------------|
| `render` | `--no-render` | Toggle JavaScript rendering (enabled by default) |
| `waitForSelector` | `--wait-selector CSS` | Wait for a CSS selector to appear before capturing content |

The selector wait includes a configurable timeout (default: 5000ms, set interactively).

## Cache Control

Control how the API uses cached results.

| Parameter | CLI Flag | Description |
|-----------|----------|-------------|
| `maxAge` | `--max-age N` | Accept cached results up to N seconds old |
| `modifiedSince` | `--modified-since YYYY-MM-DD` | Only return pages modified after this date |

## Authentication

Access pages that require authentication.

| Parameter | Description |
|-----------|-------------|
| Basic auth | Username/password sent with each request |
| Custom headers | Arbitrary HTTP headers (e.g. `Authorization: Bearer token`) |

In CLI mode, authentication is configured interactively. For automated use, consider setting headers via the API payload directly.
