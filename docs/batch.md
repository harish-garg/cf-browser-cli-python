# Batch Operations

Process multiple URLs from a single file — for crawling, screenshots, and PDFs.

## URL File Format

The file can be either **plain text** (one URL per line) or a **JSON array**. The same format works for batch crawls, screenshots, and PDFs.

### Plain text

```
# urls.txt
https://harishgarg.com
https://docs.harishgarg.com
https://blog.harishgarg.com

# Lines starting with # are ignored
# Blank lines are ignored
```

### JSON array

```json
[
  "https://harishgarg.com",
  "https://docs.harishgarg.com",
  "https://blog.harishgarg.com"
]
```

## Batch Crawling

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
4. Output formats
5. Whether to wait for each crawl to complete

### Behavior

- Each URL gets its own crawl job with a separate job ID
- Jobs are labeled automatically as `batch 1/N`, `batch 2/N`, etc.
- By default, crawls run sequentially (waits for each to complete before starting the next)
- With `--no-wait`, all crawls are started immediately and run in parallel on the API side
- Failed crawls are logged but don't stop the batch

### Output

Each crawl saves results independently under `output/{job_id}/`. Use `python main.py list` to see all batch jobs and their status.

## Batch Screenshots

### CLI

```bash
# Basic batch screenshots
python main.py screenshot-batch --file urls.txt

# Full-page WebP screenshots
python main.py screenshot-batch --file urls.txt --full-page --format webp

# Custom viewport
python main.py screenshot-batch --file urls.txt --width 1920 --height 1080
```

### Interactive

Select **"Batch screenshots from file"** from the menu. You'll be prompted for:

1. Path to the URL list file
2. Image format
3. Full-page capture toggle
4. Viewport dimensions

### Behavior

- Screenshots are taken sequentially, one URL at a time
- Failed screenshots are logged but don't stop the batch
- Each screenshot is saved individually and logged in `screenshot_log.json`

### Output

All screenshots are saved under `output/screenshots/`. A summary is printed at the end showing how many succeeded.

## Batch PDFs

### CLI

```bash
# Basic batch PDFs
python main.py pdf-batch --file urls.txt

# A4 landscape with background graphics
python main.py pdf-batch --file urls.txt --format a4 --landscape --print-background

# Custom viewport
python main.py pdf-batch --file urls.txt --width 1920 --height 1080
```

### Interactive

Select **"Batch PDFs from file"** from the menu. You'll be prompted for:

1. Path to the URL list file
2. Page format
3. Landscape orientation toggle
4. Print background graphics toggle
5. Viewport dimensions

### Behavior

- PDFs are generated sequentially, one URL at a time
- Failed PDFs are logged but don't stop the batch
- Each PDF is saved individually and logged in `pdf_log.json`

### Output

All PDFs are saved under `output/pdfs/`. A summary is printed at the end showing how many succeeded.
