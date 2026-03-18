# browserflare-cli

CLI and interactive tool for the [Cloudflare Browser Rendering APIs](https://developers.cloudflare.com/browser-rendering/), built on the [browserflare](https://github.com/user/browserflare) library.

## Install

```bash
pip install -r requirements.txt
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
python main.py crawl --url https://harishgarg.com --limit 50 --formats markdown
python main.py list
python main.py status JOB_ID

# Screenshots
python main.py screenshot --url https://harishgarg.com
python main.py screenshot --url https://harishgarg.com --full-page --format webp
python main.py screenshot-batch --file urls.txt --full-page

# PDFs
python main.py pdf --url https://harishgarg.com
python main.py pdf --url https://harishgarg.com --format a4 --landscape
python main.py pdf --html "<h1>Hello</h1>" --format letter
python main.py pdf-batch --file urls.txt --format a4 --print-background
```

Crawl results are saved under `output/{job_id}/`. Screenshots are saved under `output/screenshots/`. PDFs are saved under `output/pdfs/`.

## Docs

- [CLI Reference](docs/cli.md) — all subcommands and flags
- [Advanced Crawl Options](docs/advanced-options.md) — depth, URL patterns, rendering, auth, and more
- [Batch Operations](docs/batch.md) — batch crawl, screenshot, or PDF multiple URLs from a file

## Project Structure

```
main.py            # Entry point: CLI vs interactive dispatch
cli.py             # argparse CLI mode
prompts.py         # Interactive questionary flows + menu
docs/              # Documentation
```
