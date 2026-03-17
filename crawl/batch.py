import json
import time
from crawl.api import start_crawl, poll_until_complete, get_crawl_results_paginated
from crawl.jobs import add_job, update_job
from crawl.output import save_results


def load_urls(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    # Try JSON array first
    try:
        urls = json.loads(content)
        if isinstance(urls, list):
            return [u.strip() for u in urls if isinstance(u, str) and u.strip()]
    except (json.JSONDecodeError, ValueError):
        pass

    # Fall back to line-by-line
    urls = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        urls.append(line)
    return urls


def run_batch(urls_file, base_payload, wait=True, formats=None):
    urls = load_urls(urls_file)

    if not urls:
        print("No URLs found in file.")
        return []

    print(f"Found {len(urls)} URL(s) to crawl.\n")
    job_ids = []

    for i, url in enumerate(urls, 1):
        payload = {**base_payload, "url": url}
        print(f"[{i}/{len(urls)}] Starting crawl for: {url}")

        job_id, err = start_crawl(payload)
        if err:
            print(f"  Failed: {err}")
            continue

        print(f"  Job ID: {job_id}")
        add_job(job_id, url, payload, label=f"batch {i}/{len(urls)}")
        job_ids.append(job_id)

        if wait:
            print("  Waiting for completion...")
            result, poll_err = poll_until_complete(job_id)

            if poll_err:
                status = poll_err.get("status", "failed") if isinstance(poll_err, dict) else "failed"
                print(f"  Ended with status: {status}")
                update_job(job_id, status=status)
            else:
                page_count = len(result.get("records", []))

                if result.get("total", page_count) > page_count:
                    result, _ = get_crawl_results_paginated(job_id)
                    page_count = len(result.get("records", []))

                save_results(job_id, result, formats)
                update_job(
                    job_id,
                    status="completed",
                    completed_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                    page_count=page_count,
                )
                print(f"  Complete! {page_count} page(s) saved.")
        print()

    print(f"\nBatch complete. {len(job_ids)}/{len(urls)} crawls started.")
    return job_ids
