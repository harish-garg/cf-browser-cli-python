# Batch Crawling

Crawl multiple URLs in sequence from a single file.

## URL File Format

The file can be either **plain text** (one URL per line) or a **JSON array**.

### Plain text

```
# urls.txt
https://example.com
https://docs.example.com
https://blog.example.com

# Lines starting with # are ignored
# Blank lines are ignored
```

### JSON array

```json
[
  "https://example.com",
  "https://docs.example.com",
  "https://blog.example.com"
]
```

## Usage

### CLI

```bash
# Basic batch crawl
python main.py batch --file urls.txt --limit 50

# With output formats
python main.py batch --file urls.txt --limit 100 --formats markdown json

# Fire and forget (don't wait for completion)
python main.py batch --file urls.txt --limit 50 --no-wait
```

### Interactive

Select **"Batch crawl from file"** from the menu. You'll be prompted for:

1. Path to the URL list file
2. Page limit per crawl
3. Resource types to block
4. Whether to wait for each crawl to complete

## Behavior

- Each URL gets its own crawl job with a separate job ID
- Jobs are labeled automatically as `batch 1/N`, `batch 2/N`, etc.
- By default, crawls run sequentially (waits for each to complete before starting the next)
- With `--no-wait`, all crawls are started immediately and run in parallel on the API side
- Failed crawls are logged but don't stop the batch

## Output

Each crawl saves results independently under `output/{job_id}/`. Use `python main.py list` to see all batch jobs and their status.
