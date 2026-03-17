# crawl-cli

Interactive CLI and command-line tool for the [Cloudflare Browser Rendering Crawl API](https://developers.cloudflare.com/browser-rendering/).

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
python main.py crawl --url https://example.com --limit 50 --formats markdown
python main.py list
python main.py status JOB_ID
```

Results are saved under `output/{job_id}/`.

## Docs

- [CLI Reference](docs/cli.md) — all subcommands and flags
- [Advanced Crawl Options](docs/advanced-options.md) — depth, URL patterns, rendering, auth, and more
- [Batch Crawling](docs/batch.md) — crawl multiple URLs from a file

## Project Structure

```
main.py              # Entry point: CLI vs interactive dispatch
crawl/
  config.py           # .env loading, API config, constants
  api.py              # HTTP: start, poll, paginate, cancel
  jobs.py             # crawl_jobs.json management
  prompts.py          # Interactive questionary flows + menu
  output.py           # Save results, search, stats, diff
  cli.py              # argparse CLI mode
  batch.py            # Batch crawling from URL list
```
