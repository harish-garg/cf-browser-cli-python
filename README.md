# crawl-cli

Interactive CLI and command-line tool for the [Cloudflare Browser Rendering APIs](https://developers.cloudflare.com/browser-rendering/) 

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

Add your Cloudflare credentials to `.env`:

```
CF_ACCOUNT_ID=your_account_id
CF_API_TOKEN=your_api_token
```

## Usage

**Interactive mode** — run without arguments for the full menu:

```bash
python main.py
```

**CLI mode** — pass a subcommand to skip the menu:

```bash
# Crawling
python main.py crawl --url https://example.com --limit 50 --formats markdown
python main.py list
python main.py status JOB_ID

# Screenshots
python main.py screenshot --url https://example.com
python main.py screenshot --url https://example.com --full-page --format webp
python main.py screenshot-batch --file urls.txt --full-page
```

Crawl results are saved under `output/{job_id}/`. Screenshots are saved under `output/screenshots/`.

## Docs

- [CLI Reference](docs/cli.md) — all subcommands and flags
- [Advanced Crawl Options](docs/advanced-options.md) — depth, URL patterns, rendering, auth, and more
- [Batch Crawling & Screenshots](docs/batch.md) — batch crawl or screenshot multiple URLs from a file

## Project Structure

```
main.py                    # Entry point: CLI vs interactive dispatch
core/
  config.py                # .env loading, API config, constants
  api.py                   # HTTP: start, poll, paginate, cancel crawls
  jobs.py                  # crawl_jobs.json management
  prompts.py               # Interactive questionary flows + menu
  output.py                # Save crawl results, search, stats, diff
  cli.py                   # argparse CLI mode
  batch.py                 # Batch crawling from URL list
  screenshot_api.py        # POST to /screenshot endpoint
  screenshot_output.py     # Save screenshots + JSON log
```
