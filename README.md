# crawl-cli

Interactive CLI for using the [Cloudflare Browser Rendering API](https://developers.cloudflare.com/browser-rendering/).

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

```bash
python main.py
```

The interactive menu lets you:

- **Start a new crawl** — specify a URL, page limit, and resource types to block
- **Check job status** — poll pending jobs and download results when complete
- **List previous crawls** — view all past crawl jobs and their status

Results are saved as JSON in the `output/` directory.
