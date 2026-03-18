# CLI Reference

When you pass a subcommand, `crawl-cli` runs in non-interactive mode.

## crawl

Start a new crawl.

```bash
python main.py crawl --url URL [options]
```

| Flag | Description |
|------|-------------|
| `--url URL` | **(required)** URL to crawl |
| `--limit N` | Page limit (default: 100) |
| `--formats FORMAT [...]` | Output formats: `html`, `markdown`, `json` |
| `--depth N` | Max crawl depth (0 = seed URL only) |
| `--source TYPE` | Crawl source: `all`, `sitemaps`, `links` |
| `--subdomains` | Include subdomains |
| `--external-links` | Include external links |
| `--include-patterns PAT [...]` | URL wildcard include patterns |
| `--exclude-patterns PAT [...]` | URL wildcard exclude patterns |
| `--reject-resources TYPE [...]` | Resource types to block (default: image, media, font, stylesheet) |
| `--no-render` | Disable JavaScript rendering |
| `--wait-selector CSS` | CSS selector to wait for before capturing |
| `--max-age N` | Max cache age in seconds |
| `--modified-since YYYY-MM-DD` | Only pages modified after this date |
| `--json-prompt TEXT` | AI extraction prompt (requires `json` format) |
| `--json-schema PATH` | Path to JSON schema file for extraction |
| `--label TEXT` | Label for this crawl |
| `--no-wait` | Start crawl and return immediately |

**Examples:**

```bash
# Basic crawl with markdown output
python main.py crawl --url https://harishgarg.com --limit 50 --formats markdown

# Deep crawl with pattern filtering
python main.py crawl --url https://docs.harishgarg.com --limit 200 \
  --depth 3 --source sitemaps --subdomains \
  --include-patterns "/blog/*" "/docs/*" \
  --exclude-patterns "/admin/*"

# AI extraction
python main.py crawl --url https://harishgarg.com --limit 10 \
  --formats json --json-prompt "Extract the title and summary"
```

## list

List all crawl jobs.

```bash
python main.py list
```

## status

Check job status. Shows all pending jobs if no ID given.

```bash
python main.py status [JOB_ID]
```

If the job is complete, results are automatically downloaded and saved.

## cancel

Cancel a running crawl.

```bash
python main.py cancel JOB_ID
```

## stats

View statistics for a completed crawl.

```bash
python main.py stats JOB_ID
```

Shows record count, content size, browser seconds, and status breakdown.

## search

Search within a completed crawl's content.

```bash
python main.py search JOB_ID "query"
```

## diff

Compare URLs between two completed crawls.

```bash
python main.py diff JOB_ID_A JOB_ID_B
```

Shows added, removed, and common URLs.

## batch

Crawl multiple URLs from a file. See [Batch Crawling](batch.md) for file format details.

```bash
python main.py batch --file urls.txt [options]
```

| Flag | Description |
|------|-------------|
| `--file PATH` | **(required)** Path to URL list file |
| `--limit N` | Page limit per crawl (default: 100) |
| `--formats FORMAT [...]` | Output formats |
| `--reject-resources TYPE [...]` | Resource types to block |
| `--no-wait` | Start all crawls without waiting for completion |

## screenshot

Take a screenshot of a single URL. Screenshots are saved to `output/screenshots/` and logged in `screenshot_log.json`.

```bash
python main.py screenshot --url URL [options]
```

| Flag | Description |
|------|-------------|
| `--url URL` | **(required)** URL to screenshot |
| `--output PATH` | Custom output file path |
| `--full-page` | Capture full scrollable page |
| `--format FMT` | Image format: `png`, `jpeg`, `webp` (default: png) |
| `--quality N` | JPEG/WebP quality 0-100 |
| `--width N` | Viewport width in pixels (default: 1280) |
| `--height N` | Viewport height in pixels (default: 720) |
| `--device-scale N` | Device scale factor |
| `--selector CSS` | CSS selector to capture |
| `--wait-for CSS` | Wait for CSS selector before capture |
| `--wait-until EVENT` | Navigation wait event (`load`, `domcontentloaded`, `networkidle0`, `networkidle2`) |
| `--timeout N` | Navigation timeout in ms |
| `--omit-background` | Transparent background |
| `--user-agent TEXT` | Custom user agent string |
| `--label TEXT` | Filename label suffix |

**Examples:**

```bash
# Basic screenshot
python main.py screenshot --url https://harishgarg.com

# Full-page WebP with custom viewport
python main.py screenshot --url https://harishgarg.com --full-page --format webp --width 1920 --height 1080

# Wait for content to load before capturing
python main.py screenshot --url https://harishgarg.com --wait-for ".main-content" --wait-until networkidle0
```

## screenshot-batch

Take screenshots of multiple URLs from a file. See [Batch Operations](batch.md) for file format details.

```bash
python main.py screenshot-batch --file urls.txt [options]
```

| Flag | Description |
|------|-------------|
| `--file PATH` | **(required)** Path to URL list file |
| `--full-page` | Capture full scrollable page |
| `--format FMT` | Image format: `png`, `jpeg`, `webp` (default: png) |
| `--quality N` | JPEG/WebP quality 0-100 |
| `--width N` | Viewport width in pixels (default: 1280) |
| `--height N` | Viewport height in pixels (default: 720) |
| `--device-scale N` | Device scale factor |
| `--wait-for CSS` | Wait for CSS selector before capture |
| `--wait-until EVENT` | Navigation wait event |
| `--timeout N` | Navigation timeout in ms |
| `--omit-background` | Transparent background |
| `--user-agent TEXT` | Custom user agent string |

## pdf

Generate a PDF from a URL or raw HTML. PDFs are saved to `output/pdfs/` and logged in `pdf_log.json`.

```bash
python main.py pdf --url URL [options]
python main.py pdf --html HTML [options]
```

`--url` and `--html` are mutually exclusive; exactly one is required.

| Flag | Description |
|------|-------------|
| `--url URL` | URL to render as PDF |
| `--html HTML` | Raw HTML string to render as PDF |
| `--output PATH` | Custom output file path |
| `--format FMT` | Page format: `letter`, `legal`, `tabloid`, `ledger`, `a0`–`a6` (default: letter) |
| `--landscape` | Landscape orientation |
| `--print-background` | Print background graphics |
| `--scale N` | Page scale factor (0.1–2) |
| `--display-header-footer` | Display header and footer |
| `--header-template HTML` | HTML template for the header |
| `--footer-template HTML` | HTML template for the footer |
| `--margin-top VAL` | Top margin (e.g. `1cm`, `0.5in`) |
| `--margin-bottom VAL` | Bottom margin |
| `--margin-left VAL` | Left margin |
| `--margin-right VAL` | Right margin |
| `--width N` | Viewport width in pixels (default: 1280) |
| `--height N` | Viewport height in pixels (default: 720) |
| `--wait-for CSS` | Wait for CSS selector before capture |
| `--wait-until EVENT` | Navigation wait event (`load`, `domcontentloaded`, `networkidle0`, `networkidle2`) |
| `--timeout N` | Navigation timeout in ms |
| `--user-agent TEXT` | Custom user agent string |
| `--label TEXT` | Filename label suffix |

**Examples:**

```bash
# Basic PDF from URL
python main.py pdf --url https://harishgarg.com

# A4 landscape with background graphics
python main.py pdf --url https://harishgarg.com --format a4 --landscape --print-background

# PDF from raw HTML
python main.py pdf --html "<h1>Hello World</h1><p>Generated PDF</p>"

# Custom margins and header/footer
python main.py pdf --url https://harishgarg.com --margin-top 1cm --margin-bottom 1cm \
  --display-header-footer --footer-template "<span style='font-size:10px'>Page <span class='pageNumber'></span></span>"

# Wait for dynamic content before generating
python main.py pdf --url https://harishgarg.com --wait-for ".main-content" --wait-until networkidle0
```

## pdf-batch

Generate PDFs for multiple URLs from a file. See [Batch Operations](batch.md) for file format details.

```bash
python main.py pdf-batch --file urls.txt [options]
```

| Flag | Description |
|------|-------------|
| `--file PATH` | **(required)** Path to URL list file |
| `--format FMT` | Page format (default: letter) |
| `--landscape` | Landscape orientation |
| `--print-background` | Print background graphics |
| `--scale N` | Page scale factor (0.1–2) |
| `--width N` | Viewport width in pixels (default: 1280) |
| `--height N` | Viewport height in pixels (default: 720) |
| `--wait-for CSS` | Wait for CSS selector before capture |
| `--wait-until EVENT` | Navigation wait event |
| `--timeout N` | Navigation timeout in ms |
| `--user-agent TEXT` | Custom user agent string |
