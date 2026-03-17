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
python main.py crawl --url https://example.com --limit 50 --formats markdown

# Deep crawl with pattern filtering
python main.py crawl --url https://docs.example.com --limit 200 \
  --depth 3 --source sitemaps --subdomains \
  --include-patterns "/blog/*" "/docs/*" \
  --exclude-patterns "/admin/*"

# AI extraction
python main.py crawl --url https://example.com --limit 10 \
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
