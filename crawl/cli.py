import argparse
import sys
import time
import json
from crawl.config import RESOURCE_TYPES, DEFAULT_REJECT_RESOURCES, TERMINAL_STATUSES, SUCCESS_STATUSES
from crawl.api import start_crawl, get_crawl_status, cancel_crawl, poll_until_complete, get_crawl_results_paginated
from crawl.jobs import load_jobs, add_job, update_job, find_job
from crawl.output import save_results, get_statistics, search_results, diff_crawls
from crawl.batch import run_batch


def build_parser():
    parser = argparse.ArgumentParser(
        prog="crawl-cli",
        description="Cloudflare Browser Rendering crawl CLI",
    )
    sub = parser.add_subparsers(dest="command")

    # crawl
    crawl_p = sub.add_parser("crawl", help="Start a new crawl")
    crawl_p.add_argument("--url", required=True, help="URL to crawl")
    crawl_p.add_argument("--limit", type=int, default=100, help="Page limit (default: 100)")
    crawl_p.add_argument("--formats", nargs="+", choices=["html", "markdown", "json"], help="Output formats")
    crawl_p.add_argument("--depth", type=int, help="Max crawl depth")
    crawl_p.add_argument("--source", choices=["all", "sitemaps", "links"], help="Crawl source")
    crawl_p.add_argument("--no-render", action="store_true", help="Disable JS rendering")
    crawl_p.add_argument("--external-links", action="store_true", help="Include external links")
    crawl_p.add_argument("--subdomains", action="store_true", help="Include subdomains")
    crawl_p.add_argument("--include-patterns", nargs="+", help="URL include patterns")
    crawl_p.add_argument("--exclude-patterns", nargs="+", help="URL exclude patterns")
    crawl_p.add_argument(
        "--reject-resources", nargs="+",
        default=DEFAULT_REJECT_RESOURCES,
        choices=RESOURCE_TYPES,
        help="Resource types to reject",
    )
    crawl_p.add_argument("--max-age", type=int, help="Max cache age in seconds")
    crawl_p.add_argument("--modified-since", help="Only pages modified since YYYY-MM-DD")
    crawl_p.add_argument("--wait-selector", help="CSS selector to wait for")
    crawl_p.add_argument("--no-wait", action="store_true", help="Don't wait for completion")
    crawl_p.add_argument("--label", help="Label for this crawl")
    crawl_p.add_argument("--json-prompt", help="AI extraction prompt for JSON format")
    crawl_p.add_argument("--json-schema", help="Path to JSON schema file for extraction")

    # list
    sub.add_parser("list", help="List all crawl jobs")

    # status
    status_p = sub.add_parser("status", help="Check job status")
    status_p.add_argument("job_id", nargs="?", help="Job ID (shows all pending if omitted)")

    # cancel
    cancel_p = sub.add_parser("cancel", help="Cancel a crawl")
    cancel_p.add_argument("job_id", help="Job ID to cancel")

    # stats
    stats_p = sub.add_parser("stats", help="View crawl statistics")
    stats_p.add_argument("job_id", help="Job ID")

    # search
    search_p = sub.add_parser("search", help="Search crawl results")
    search_p.add_argument("job_id", help="Job ID to search")
    search_p.add_argument("query", help="Search query")

    # diff
    diff_p = sub.add_parser("diff", help="Compare two crawls")
    diff_p.add_argument("job_a", help="First job ID (baseline)")
    diff_p.add_argument("job_b", help="Second job ID (comparison)")

    # batch
    batch_p = sub.add_parser("batch", help="Batch crawl from URL file")
    batch_p.add_argument("--file", required=True, help="Path to URL list file")
    batch_p.add_argument("--limit", type=int, default=100, help="Page limit per crawl")
    batch_p.add_argument("--formats", nargs="+", choices=["html", "markdown", "json"], help="Output formats")
    batch_p.add_argument(
        "--reject-resources", nargs="+",
        default=DEFAULT_REJECT_RESOURCES,
        choices=RESOURCE_TYPES,
        help="Resource types to reject",
    )
    batch_p.add_argument("--no-wait", action="store_true", help="Don't wait for completion")

    return parser


def _build_payload(args):
    payload = {
        "url": args.url,
        "limit": args.limit,
    }

    if args.reject_resources:
        payload["rejectResourceTypes"] = args.reject_resources
    if args.formats:
        payload["formats"] = args.formats

    if args.depth is not None:
        payload["depth"] = args.depth
    if args.source:
        payload["source"] = args.source
    if args.no_render:
        payload["render"] = False
    if args.external_links:
        payload["includeExternalLinks"] = True
    if args.subdomains:
        payload["includeSubdomains"] = True
    if args.include_patterns:
        payload["includePatterns"] = args.include_patterns
    if args.exclude_patterns:
        payload["excludePatterns"] = args.exclude_patterns
    if args.max_age is not None:
        payload["maxAge"] = args.max_age
    if args.modified_since:
        ts = int(time.mktime(time.strptime(args.modified_since, "%Y-%m-%d")))
        payload["modifiedSince"] = ts
    if args.wait_selector:
        payload["waitForSelector"] = {"selector": args.wait_selector}

    if args.json_prompt or args.json_schema:
        json_options = {}
        if args.json_prompt:
            json_options["prompt"] = args.json_prompt
        if args.json_schema:
            import os
            if os.path.exists(args.json_schema):
                with open(args.json_schema, "r", encoding="utf-8") as f:
                    json_options["schema"] = json.load(f)
        payload["jsonOptions"] = json_options

    return payload


def cmd_crawl(args):
    payload = _build_payload(args)
    formats = args.formats

    print(f"Starting crawl for: {args.url}")
    job_id, err = start_crawl(payload)

    if err:
        print(f"Failed to start crawl: {err}")
        sys.exit(1)

    print(f"Job ID: {job_id}")
    add_job(job_id, args.url, payload, label=args.label)

    if args.no_wait:
        print("Crawl started. Use 'status' command to monitor.")
        return

    print("Waiting for crawl to complete...")
    result, poll_err = poll_until_complete(job_id)

    if poll_err:
        status = poll_err.get("status", "failed") if isinstance(poll_err, dict) else "failed"
        print(f"Crawl ended with status: {status}")
        update_job(job_id, status=status)
        sys.exit(1)

    page_count = len(result.get("records", []))

    if result.get("total", page_count) > page_count:
        print("Fetching remaining pages...")
        result, fetch_err = get_crawl_results_paginated(job_id)
        if not fetch_err:
            page_count = len(result.get("records", []))

    output_path = save_results(job_id, result, formats)
    update_job(
        job_id,
        status="completed",
        completed_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        page_count=page_count,
    )
    print(f"Crawl complete! {page_count} page(s) saved to {output_path}")


def cmd_list(_args):
    jobs = load_jobs()
    if not jobs:
        print("No previous crawls found.")
        return

    print(f"\nFound {len(jobs)} crawl(s):\n")
    for job in reversed(jobs):
        label = f" [{job['label']}]" if job.get("label") else ""
        status = job.get("status", "unknown")
        print(f"  {job['job_id']}{label}")
        print(f"    URL: {job['url']}  |  Status: {status}  |  Started: {job['started_at']}")
        if job.get("page_count") is not None:
            print(f"    Pages: {job['page_count']}")
        print()


def cmd_status(args):
    if args.job_id:
        result, err = get_crawl_status(args.job_id)
        if err:
            print(f"Error: {err}")
            sys.exit(1)

        status = result.get("status", "unknown")
        print(f"Status: {status}")

        if status in SUCCESS_STATUSES:
            page_count = len(result.get("records", []))

            if result.get("total", page_count) > page_count:
                result, _ = get_crawl_results_paginated(args.job_id)
                page_count = len(result.get("records", []))

            job = find_job(args.job_id)
            job_formats = job.get("payload", {}).get("formats") if job else None
            output_path = save_results(args.job_id, result, job_formats)
            update_job(
                args.job_id,
                status="completed",
                completed_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                page_count=page_count,
            )
            print(f"Saved {page_count} page(s) to {output_path}")
        elif status in TERMINAL_STATUSES:
            update_job(args.job_id, status=status)
    else:
        jobs = load_jobs()
        pending = [j for j in jobs if j.get("status") not in TERMINAL_STATUSES]
        if not pending:
            print("No pending jobs.")
            return
        for j in pending:
            print(f"  {j['job_id'][:8]}...  {j['url']}  status={j.get('status')}")


def cmd_cancel(args):
    success, err = cancel_crawl(args.job_id)
    if success:
        print(f"Cancelled: {args.job_id}")
    else:
        print(f"Failed to cancel: {err}")
        sys.exit(1)


def cmd_stats(args):
    stats = get_statistics(args.job_id)
    if not stats:
        print("Could not load results for this job.")
        sys.exit(1)

    print(f"Job status: {stats['job_status']}")
    print(f"Total records: {stats['total_records']}")
    print(f"Content size: {stats['total_content_size_mb']} MB")
    print(f"Browser seconds: {stats['browser_seconds']}")
    if stats["status_breakdown"]:
        print("Status breakdown:")
        for status, count in stats["status_breakdown"].items():
            print(f"  {status}: {count}")


def cmd_search(args):
    matches = search_results(args.job_id, args.query)
    if not matches:
        print("No matches found.")
        return

    print(f"\nFound {len(matches)} match(es):\n")
    for m in matches:
        print(f"  {m['url']}")
        if m.get("snippet"):
            print(f"    {m['snippet']}")
        print()


def cmd_diff(args):
    result = diff_crawls(args.job_a, args.job_b)
    if not result:
        print("Could not load results for comparison.")
        sys.exit(1)

    print(f"Crawl A: {result['count_a']} URLs")
    print(f"Crawl B: {result['count_b']} URLs")
    print(f"Common: {len(result['common'])}")
    print(f"Added: {len(result['added'])}")
    for url in result["added"]:
        print(f"  + {url}")
    print(f"Removed: {len(result['removed'])}")
    for url in result["removed"]:
        print(f"  - {url}")


def cmd_batch(args):
    base_payload = {"limit": args.limit}
    if args.reject_resources:
        base_payload["rejectResourceTypes"] = args.reject_resources
    if args.formats:
        base_payload["formats"] = args.formats
    run_batch(args.file, base_payload, wait=not args.no_wait, formats=args.formats)


def run_cli(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        return False  # no subcommand → fall through to interactive

    commands = {
        "crawl": cmd_crawl,
        "list": cmd_list,
        "status": cmd_status,
        "cancel": cmd_cancel,
        "stats": cmd_stats,
        "search": cmd_search,
        "diff": cmd_diff,
        "batch": cmd_batch,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)

    return True  # handled
