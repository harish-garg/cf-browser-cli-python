import os
import time
import questionary
from core.config import (
    RESOURCE_TYPES,
    DEFAULT_REJECT_RESOURCES,
    CRAWL_SOURCES,
    OUTPUT_FORMATS,
    TERMINAL_STATUSES,
    SUCCESS_STATUSES,
    SCREENSHOT_FORMATS,
    WAIT_UNTIL_OPTIONS,
)
from core.jobs import load_jobs, add_job, update_job, delete_jobs, get_jobs_by_status, find_job
from core.api import start_crawl, get_crawl_status, cancel_crawl, poll_until_complete, get_crawl_results_paginated
from core.output import save_results, search_results, get_statistics, diff_crawls, find_result_path
from core.screenshot_api import take_screenshot
from core.screenshot_output import save_screenshot, log_screenshot


def _validate_url(val):
    if val.startswith(("http://", "https://")):
        return True
    return "URL must start with http:// or https://"


def _validate_positive_int(val):
    if val.isdigit() and int(val) > 0:
        return True
    return "Must be a positive number"


def _validate_non_negative_int(val):
    if val.isdigit() and int(val) >= 0:
        return True
    return "Must be a non-negative number"


def _validate_date_or_empty(val):
    if not val:
        return True
    try:
        time.strptime(val, "%Y-%m-%d")
        return True
    except ValueError:
        return "Use YYYY-MM-DD format or leave empty"


def _job_display(job):
    label = f" [{job['label']}]" if job.get("label") else ""
    job_id_short = job["job_id"][:8]
    return f"{job_id_short}...{label}  {job['url']}  ({job.get('status', '?')}, {job['started_at']})"


def _build_advanced_options():
    groups = questionary.checkbox(
        "Select advanced option groups to configure:",
        choices=[
            questionary.Choice("Crawl scope (depth, source, subdomains, external links)", value="scope"),
            questionary.Choice("URL patterns (include/exclude wildcards)", value="patterns"),
            questionary.Choice("Output formats (html, markdown, json, AI extraction)", value="formats"),
            questionary.Choice("Page rendering (render toggle, waitForSelector)", value="rendering"),
            questionary.Choice("Cache control (maxAge, modifiedSince)", value="cache"),
            questionary.Choice("Authentication (basic auth, custom headers)", value="auth"),
        ],
    ).ask()

    if groups is None:
        return {}

    payload = {}

    if "scope" in groups:
        payload.update(_prompt_scope())

    if "patterns" in groups:
        payload.update(_prompt_patterns())

    if "formats" in groups:
        payload.update(_prompt_formats())

    if "rendering" in groups:
        payload.update(_prompt_rendering())

    if "cache" in groups:
        payload.update(_prompt_cache())

    if "auth" in groups:
        payload.update(_prompt_auth())

    return payload


def _prompt_scope():
    opts = {}

    depth = questionary.text(
        "Max crawl depth (0 = only seed URL):",
        default="",
        validate=lambda v: True if not v else (_validate_non_negative_int(v)),
    ).ask()
    if depth:
        opts["depth"] = int(depth)

    source = questionary.select(
        "Crawl source:",
        choices=["all (links + sitemaps)", "sitemaps", "links"],
        default="all (links + sitemaps)",
    ).ask()
    if source and source != "all (links + sitemaps)":
        opts["source"] = source
    elif source == "all (links + sitemaps)":
        opts["source"] = "all"

    flags = questionary.checkbox(
        "Additional scope options:",
        choices=[
            questionary.Choice("Include subdomains", value="includeSubdomains"),
            questionary.Choice("Include external links", value="includeExternalLinks"),
        ],
    ).ask()
    if flags:
        for flag in flags:
            opts[flag] = True

    return opts


def _prompt_patterns():
    opts = {}

    include = questionary.text(
        "Include URL patterns (comma-separated wildcards, e.g. /blog/*, /docs/*):",
        default="",
    ).ask()
    if include:
        opts["includePatterns"] = [p.strip() for p in include.split(",") if p.strip()]

    exclude = questionary.text(
        "Exclude URL patterns (comma-separated wildcards, e.g. /admin/*, /api/*):",
        default="",
    ).ask()
    if exclude:
        opts["excludePatterns"] = [p.strip() for p in exclude.split(",") if p.strip()]

    return opts


def _prompt_formats():
    opts = {}

    formats = questionary.checkbox(
        "Output formats to request:",
        choices=[
            questionary.Choice("markdown", checked=True),
            questionary.Choice("html"),
            questionary.Choice("json (AI extraction)"),
        ],
    ).ask()

    if formats:
        fmt_list = []
        for f in formats:
            if f == "json (AI extraction)":
                fmt_list.append("json")
            else:
                fmt_list.append(f)
        opts["formats"] = fmt_list

    if formats and "json (AI extraction)" in formats:
        prompt_text = questionary.text(
            "AI extraction prompt (describe what data to extract):",
            default="",
        ).ask()

        schema_path = questionary.text(
            "JSON schema file path (optional, leave empty to skip):",
            default="",
        ).ask()

        json_options = {}
        if prompt_text:
            json_options["prompt"] = prompt_text
        if schema_path and os.path.exists(schema_path):
            import json
            with open(schema_path, "r", encoding="utf-8") as f:
                json_options["schema"] = json.load(f)

        if json_options:
            opts["jsonOptions"] = json_options

    return opts


def _prompt_rendering():
    opts = {}

    render = questionary.confirm("Enable JavaScript rendering?", default=True).ask()
    if render is not None:
        opts["render"] = render

    if render:
        selector = questionary.text(
            "Wait for CSS selector (leave empty to skip):",
            default="",
        ).ask()
        if selector:
            wait_obj = {"selector": selector}
            timeout = questionary.text(
                "Selector timeout in ms:",
                default="5000",
                validate=_validate_positive_int,
            ).ask()
            if timeout:
                wait_obj["timeout"] = int(timeout)
            opts["waitForSelector"] = wait_obj

    return opts


def _prompt_cache():
    opts = {}

    max_age = questionary.text(
        "Max cache age in seconds (leave empty to skip):",
        default="",
        validate=lambda v: True if not v else _validate_non_negative_int(v),
    ).ask()
    if max_age:
        opts["maxAge"] = int(max_age)

    modified_since = questionary.text(
        "Only pages modified since (YYYY-MM-DD, leave empty to skip):",
        default="",
        validate=_validate_date_or_empty,
    ).ask()
    if modified_since:
        ts = int(time.mktime(time.strptime(modified_since, "%Y-%m-%d")))
        opts["modifiedSince"] = ts

    return opts


def _prompt_auth():
    opts = {}

    use_basic = questionary.confirm("Use basic authentication?", default=False).ask()
    if use_basic:
        username = questionary.text("Username:").ask()
        password = questionary.password("Password:").ask()
        if username and password:
            opts["basicAuth"] = {"username": username, "password": password}

    custom_headers = questionary.text(
        "Custom HTTP headers (key:value pairs, comma-separated, leave empty to skip):",
        default="",
    ).ask()
    if custom_headers:
        headers_dict = {}
        for pair in custom_headers.split(","):
            pair = pair.strip()
            if ":" in pair:
                key, value = pair.split(":", 1)
                headers_dict[key.strip()] = value.strip()
        if headers_dict:
            opts["headers"] = headers_dict

    return opts


def prompt_start_crawl():
    target_url = questionary.text(
        "URL to crawl:",
        default="https://example.com",
        validate=_validate_url,
    ).ask()
    if target_url is None:
        return

    limit = questionary.text(
        "Page limit:",
        default="100",
        validate=_validate_positive_int,
    ).ask()
    if limit is None:
        return

    resource_choices = [
        questionary.Choice(rt, checked=(rt in DEFAULT_REJECT_RESOURCES))
        for rt in RESOURCE_TYPES
    ]
    resource_types = questionary.checkbox(
        "Resource types to reject:",
        choices=resource_choices,
    ).ask()
    if resource_types is None:
        return

    format_choices = questionary.checkbox(
        "Output formats to request:",
        choices=[
            questionary.Choice("markdown", checked=True),
            questionary.Choice("html"),
            questionary.Choice("json (AI extraction)"),
        ],
    ).ask()

    formats = None
    json_options = {}
    if format_choices:
        formats = []
        for f in format_choices:
            if f == "json (AI extraction)":
                formats.append("json")
            else:
                formats.append(f)

        if "json (AI extraction)" in format_choices:
            prompt_text = questionary.text(
                "AI extraction prompt (describe what data to extract):",
                default="",
            ).ask()
            schema_path = questionary.text(
                "JSON schema file path (optional, leave empty to skip):",
                default="",
            ).ask()
            if prompt_text:
                json_options["prompt"] = prompt_text
            if schema_path and os.path.exists(schema_path):
                import json
                with open(schema_path, "r", encoding="utf-8") as f:
                    json_options["schema"] = json.load(f)

    label = questionary.text("Label for this crawl (optional):", default="").ask()

    payload = {
        "url": target_url,
        "limit": int(limit),
    }
    if resource_types:
        payload["rejectResourceTypes"] = resource_types
    if formats:
        payload["formats"] = formats
    if json_options:
        payload["jsonOptions"] = json_options

    advanced = questionary.confirm("Configure advanced options?", default=False).ask()
    if advanced:
        adv_opts = _build_advanced_options()
        payload.update(adv_opts)
        formats = payload.get("formats", formats)

    print(f"\nStarting crawl for: {target_url}")
    job_id, err = start_crawl(payload)

    if err:
        print(f"Failed to start crawl: {err}")
        return

    print(f"Job ID: {job_id}")
    add_job(job_id, target_url, payload, label=label or None)

    wait = questionary.confirm("Wait for crawl to complete?", default=True).ask()
    if not wait:
        print("Crawl started in background. Use 'Check job status' to monitor.")
        return

    print("Waiting for crawl to complete...")
    result, err = poll_until_complete(job_id)

    if err:
        status = err.get("status", "failed") if isinstance(err, dict) else "failed"
        print(f"Crawl ended with status: {status}")
        update_job(job_id, status=status)
        return

    page_count = len(result.get("records", []))

    if result.get("total", page_count) > page_count:
        print("Fetching remaining pages...")
        result, fetch_err = get_crawl_results_paginated(job_id)
        if fetch_err:
            print(f"Warning: Could not fetch all pages: {fetch_err}")
        else:
            page_count = len(result.get("records", []))

    output_path = save_results(job_id, result, formats)
    update_job(
        job_id,
        status="completed",
        completed_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        page_count=page_count,
    )
    print(f"Crawl complete! {page_count} page(s) saved to {output_path}")


def prompt_check_status():
    jobs = load_jobs()
    non_terminal = [j for j in jobs if j.get("status") not in TERMINAL_STATUSES]

    if not non_terminal:
        print("No pending/active jobs to check.")
        return

    choices = [
        questionary.Choice(_job_display(j), value=j["job_id"])
        for j in reversed(non_terminal)
    ]
    choices.append(questionary.Choice("Back", value=None))

    job_id = questionary.select("Select a job to check:", choices=choices).ask()
    if job_id is None:
        return

    print(f"\nChecking status for {job_id}...")
    result, err = get_crawl_status(job_id)

    if err:
        print(f"Error fetching status: {err}")
        return

    status = result.get("status", "unknown")
    print(f"  Status: {status}")

    if status in SUCCESS_STATUSES:
        page_count = len(result.get("records", []))

        if result.get("total", page_count) > page_count:
            print("Fetching all pages...")
            result, fetch_err = get_crawl_results_paginated(job_id)
            if not fetch_err:
                page_count = len(result.get("records", []))

        job = find_job(job_id)
        job_formats = job.get("payload", {}).get("formats") if job else None
        output_path = save_results(job_id, result, job_formats)
        update_job(
            job_id,
            status="completed",
            completed_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            page_count=page_count,
        )
        print(f"  Crawl complete! {page_count} page(s) saved to {output_path}")

    elif status in TERMINAL_STATUSES:
        update_job(job_id, status=status)
        print(f"  Crawl ended: {status}")

    else:
        print(f"  Job is still {status}. Try again later.")


def prompt_list_crawls():
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


def prompt_cancel_crawl():
    jobs = load_jobs()
    active = [j for j in jobs if j.get("status") not in TERMINAL_STATUSES]

    if not active:
        print("No active crawls to cancel.")
        return

    choices = [
        questionary.Choice(_job_display(j), value=j["job_id"])
        for j in reversed(active)
    ]
    choices.append(questionary.Choice("Back", value=None))

    job_id = questionary.select("Select a crawl to cancel:", choices=choices).ask()
    if job_id is None:
        return

    confirm = questionary.confirm(f"Cancel job {job_id[:8]}...?", default=False).ask()
    if not confirm:
        return

    success, err = cancel_crawl(job_id)
    if success:
        print(f"Crawl {job_id[:8]}... cancelled.")
    else:
        print(f"Failed to cancel: {err}")


def prompt_delete_jobs():
    jobs = load_jobs()

    if not jobs:
        print("No jobs to delete.")
        return

    choices = [
        questionary.Choice(_job_display(j), value=j["job_id"])
        for j in reversed(jobs)
    ]

    selected = questionary.checkbox("Select jobs to delete:", choices=choices).ask()
    if not selected:
        return

    delete_files = questionary.confirm("Also delete output files?", default=False).ask()

    if delete_files:
        import shutil
        for job_id in selected:
            result_path = find_result_path(job_id)
            if result_path:
                parent = os.path.dirname(result_path)
                if os.path.basename(parent) == job_id:
                    shutil.rmtree(parent, ignore_errors=True)
                else:
                    os.remove(result_path)

    delete_jobs(selected)
    print(f"Deleted {len(selected)} job(s).")


def prompt_rerun_crawl():
    jobs = load_jobs()
    rerunnable = [j for j in jobs if j.get("payload")]

    if not rerunnable:
        print("No jobs with stored payloads to re-run.")
        return

    choices = [
        questionary.Choice(_job_display(j), value=j["job_id"])
        for j in reversed(rerunnable)
    ]
    choices.append(questionary.Choice("Back", value=None))

    job_id = questionary.select("Select a crawl to re-run:", choices=choices).ask()
    if job_id is None:
        return

    job = find_job(job_id)
    if not job or not job.get("payload"):
        print("No payload found for this job.")
        return

    payload = job["payload"]
    print(f"\nRe-running crawl for: {payload.get('url')}")
    print(f"  Payload: limit={payload.get('limit')}")

    new_id, err = start_crawl(payload)
    if err:
        print(f"Failed to start crawl: {err}")
        return

    print(f"New Job ID: {new_id}")
    label = f"re-run of {job_id[:8]}"
    add_job(new_id, payload.get("url", "unknown"), payload, label=label)

    wait = questionary.confirm("Wait for crawl to complete?", default=True).ask()
    if not wait:
        print("Crawl started in background.")
        return

    print("Waiting for crawl to complete...")
    result, poll_err = poll_until_complete(new_id)

    if poll_err:
        status = poll_err.get("status", "failed") if isinstance(poll_err, dict) else "failed"
        print(f"Crawl ended with status: {status}")
        update_job(new_id, status=status)
        return

    page_count = len(result.get("records", []))
    rerun_formats = payload.get("formats")
    output_path = save_results(new_id, result, rerun_formats)
    update_job(
        new_id,
        status="completed",
        completed_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        page_count=page_count,
    )
    print(f"Crawl complete! {page_count} page(s) saved to {output_path}")


def prompt_search_results():
    jobs = load_jobs()
    completed = [j for j in jobs if j.get("status") in SUCCESS_STATUSES]

    if not completed:
        print("No completed crawls to search.")
        return

    choices = [
        questionary.Choice(_job_display(j), value=j["job_id"])
        for j in reversed(completed)
    ]
    choices.append(questionary.Choice("Back", value=None))

    job_id = questionary.select("Select a crawl to search:", choices=choices).ask()
    if job_id is None:
        return

    query = questionary.text("Search query:").ask()
    if not query:
        return

    matches = search_results(job_id, query)
    if not matches:
        print("No matches found.")
        return

    print(f"\nFound {len(matches)} match(es):\n")
    for m in matches:
        print(f"  {m['url']}")
        if m.get("snippet"):
            print(f"    ...{m['snippet']}...")
        print()


def prompt_statistics():
    jobs = load_jobs()
    completed = [j for j in jobs if j.get("status") in SUCCESS_STATUSES]

    if not completed:
        print("No completed crawls to analyze.")
        return

    choices = [
        questionary.Choice(_job_display(j), value=j["job_id"])
        for j in reversed(completed)
    ]
    choices.append(questionary.Choice("Back", value=None))

    job_id = questionary.select("Select a crawl:", choices=choices).ask()
    if job_id is None:
        return

    stats = get_statistics(job_id)
    if not stats:
        print("Could not load results for this job.")
        return

    print(f"\n  Job status: {stats['job_status']}")
    print(f"  Total records: {stats['total_records']}")
    print(f"  Content size: {stats['total_content_size_mb']} MB")
    print(f"  Browser seconds: {stats['browser_seconds']}")
    if stats["status_breakdown"]:
        print("  Status breakdown:")
        for status, count in stats["status_breakdown"].items():
            print(f"    {status}: {count}")
    print()


def prompt_diff_crawls():
    jobs = load_jobs()
    completed = [j for j in jobs if j.get("status") in SUCCESS_STATUSES]

    if len(completed) < 2:
        print("Need at least 2 completed crawls to compare.")
        return

    choices = [
        questionary.Choice(_job_display(j), value=j["job_id"])
        for j in reversed(completed)
    ]

    job_a = questionary.select("Select first crawl (baseline):", choices=choices).ask()
    if job_a is None:
        return

    choices_b = [c for c in choices if c.value != job_a]
    job_b = questionary.select("Select second crawl (comparison):", choices=choices_b).ask()
    if job_b is None:
        return

    result = diff_crawls(job_a, job_b)
    if not result:
        print("Could not load results for comparison.")
        return

    print(f"\n  Crawl A: {result['count_a']} URLs")
    print(f"  Crawl B: {result['count_b']} URLs")
    print(f"  Common: {len(result['common'])}")
    print(f"  Added (in B, not A): {len(result['added'])}")
    for url in result["added"][:20]:
        print(f"    + {url}")
    if len(result["added"]) > 20:
        print(f"    ... and {len(result['added']) - 20} more")

    print(f"  Removed (in A, not B): {len(result['removed'])}")
    for url in result["removed"][:20]:
        print(f"    - {url}")
    if len(result["removed"]) > 20:
        print(f"    ... and {len(result['removed']) - 20} more")
    print()


def prompt_batch_crawl():
    from core.batch import run_batch

    file_path = questionary.path(
        "Path to URL list file:",
        validate=lambda v: True if os.path.isfile(v) else "File not found",
    ).ask()
    if not file_path:
        return

    limit = questionary.text(
        "Page limit per crawl:",
        default="100",
        validate=_validate_positive_int,
    ).ask()
    if limit is None:
        return

    resource_choices = [
        questionary.Choice(rt, checked=(rt in DEFAULT_REJECT_RESOURCES))
        for rt in RESOURCE_TYPES
    ]
    resource_types = questionary.checkbox(
        "Resource types to reject:",
        choices=resource_choices,
    ).ask()

    formats = questionary.checkbox(
        "Output formats to request:",
        choices=[
            questionary.Choice("markdown", checked=True),
            questionary.Choice("html"),
            questionary.Choice("json"),
        ],
    ).ask()

    base_payload = {"limit": int(limit)}
    if resource_types:
        base_payload["rejectResourceTypes"] = resource_types
    if formats:
        base_payload["formats"] = formats

    wait = questionary.confirm("Wait for each crawl to complete?", default=True).ask()

    run_batch(file_path, base_payload, wait=wait, formats=formats)


def prompt_screenshot():
    url = questionary.text(
        "URL to screenshot:",
        default="https://example.com",
        validate=_validate_url,
    ).ask()
    if url is None:
        return

    full_page = questionary.confirm("Capture full scrollable page?", default=False).ask()

    fmt = questionary.select(
        "Image format:",
        choices=SCREENSHOT_FORMATS,
        default="png",
    ).ask()
    if fmt is None:
        return

    payload = {"url": url}
    if full_page:
        payload["fullPage"] = True
    if fmt != "png":
        payload["type"] = fmt

    if fmt in ("jpeg", "webp"):
        quality = questionary.text(
            "Image quality (0-100, leave empty for default):",
            default="",
            validate=lambda v: True if not v else (
                _validate_non_negative_int(v) if v.isdigit() and int(v) <= 100
                else "Must be 0-100"
            ),
        ).ask()
        if quality:
            payload["quality"] = int(quality)

    width = questionary.text(
        "Viewport width:",
        default="1280",
        validate=_validate_positive_int,
    ).ask()
    height = questionary.text(
        "Viewport height:",
        default="720",
        validate=_validate_positive_int,
    ).ask()
    payload["viewport"] = {"width": int(width), "height": int(height)}

    advanced = questionary.confirm("Configure advanced options?", default=False).ask()
    if advanced:
        selector = questionary.text(
            "CSS selector to capture (leave empty for full page):",
            default="",
        ).ask()
        if selector:
            payload["selector"] = selector

        wait_for = questionary.text(
            "Wait for CSS selector before capture (leave empty to skip):",
            default="",
        ).ask()
        if wait_for:
            payload["waitForSelector"] = {"selector": wait_for}

        wait_until = questionary.select(
            "Navigation wait event:",
            choices=["(default)"] + WAIT_UNTIL_OPTIONS,
            default="(default)",
        ).ask()
        if wait_until and wait_until != "(default)":
            payload["gotoOptions"] = {"waitUntil": wait_until}

        omit_bg = questionary.confirm("Transparent background?", default=False).ask()
        if omit_bg:
            payload["omitBackground"] = True

        user_agent = questionary.text(
            "Custom user agent (leave empty to skip):",
            default="",
        ).ask()
        if user_agent:
            payload["userAgent"] = user_agent

        device_scale = questionary.text(
            "Device scale factor (leave empty for default):",
            default="",
            validate=lambda v: True if not v else (
                True if v.replace(".", "", 1).isdigit() and float(v) > 0
                else "Must be a positive number"
            ),
        ).ask()
        if device_scale:
            payload["viewport"]["deviceScaleFactor"] = float(device_scale)

    label = questionary.text("Label for this screenshot (optional):", default="").ask()

    print(f"\nTaking screenshot of: {url}")
    image_bytes, content_type, err = take_screenshot(payload)

    if err:
        print(f"Screenshot failed: {err}")
        return

    filepath = save_screenshot(url, image_bytes, content_type, label=label or None)
    log_screenshot(url, filepath, payload)
    print(f"Screenshot saved to: {filepath}")


def prompt_screenshot_batch():
    from core.batch import load_urls

    file_path = questionary.path(
        "Path to URL list file:",
        validate=lambda v: True if os.path.isfile(v) else "File not found",
    ).ask()
    if not file_path:
        return

    fmt = questionary.select(
        "Image format:",
        choices=SCREENSHOT_FORMATS,
        default="png",
    ).ask()
    if fmt is None:
        return

    full_page = questionary.confirm("Capture full scrollable page?", default=False).ask()

    width = questionary.text(
        "Viewport width:",
        default="1280",
        validate=_validate_positive_int,
    ).ask()
    height = questionary.text(
        "Viewport height:",
        default="720",
        validate=_validate_positive_int,
    ).ask()

    urls = load_urls(file_path)
    if not urls:
        print("No URLs found in file.")
        return

    print(f"\nFound {len(urls)} URL(s) to screenshot.\n")
    success_count = 0

    for i, url in enumerate(urls, 1):
        payload = {
            "url": url,
            "viewport": {"width": int(width), "height": int(height)},
        }
        if full_page:
            payload["fullPage"] = True
        if fmt != "png":
            payload["type"] = fmt

        print(f"[{i}/{len(urls)}] Screenshotting: {url}")
        image_bytes, content_type, err = take_screenshot(payload)

        if err:
            print(f"  Failed: {err}")
            continue

        filepath = save_screenshot(url, image_bytes, content_type)
        log_screenshot(url, filepath, payload)
        print(f"  Saved: {filepath}")
        success_count += 1

    print(f"\nBatch complete. {success_count}/{len(urls)} screenshots saved.")


def interactive_menu():
    menu_choices = [
        questionary.Separator("--- Crawling ---"),
        questionary.Choice("Start a new crawl", value="start"),
        questionary.Choice("Batch crawl from file", value="batch"),
        questionary.Choice("Re-run a previous crawl", value="rerun"),
        questionary.Separator("--- Screenshots ---"),
        questionary.Choice("Take a screenshot", value="screenshot"),
        questionary.Choice("Batch screenshots from file", value="screenshot_batch"),
        questionary.Separator("--- Jobs ---"),
        questionary.Choice("Check job status", value="status"),
        questionary.Choice("Cancel a crawl", value="cancel"),
        questionary.Choice("List previous crawls", value="list"),
        questionary.Choice("Delete old jobs", value="delete"),
        questionary.Separator("--- Results ---"),
        questionary.Choice("Search crawl results", value="search"),
        questionary.Choice("View crawl statistics", value="stats"),
        questionary.Choice("Compare two crawls", value="diff"),
        questionary.Separator("---"),
        questionary.Choice("Exit", value="exit"),
    ]

    handlers = {
        "start": prompt_start_crawl,
        "batch": prompt_batch_crawl,
        "rerun": prompt_rerun_crawl,
        "screenshot": prompt_screenshot,
        "screenshot_batch": prompt_screenshot_batch,
        "status": prompt_check_status,
        "cancel": prompt_cancel_crawl,
        "list": prompt_list_crawls,
        "delete": prompt_delete_jobs,
        "search": prompt_search_results,
        "stats": prompt_statistics,
        "diff": prompt_diff_crawls,
    }

    while True:
        action = questionary.select(
            "What would you like to do?",
            choices=menu_choices,
        ).ask()

        if action is None or action == "exit":
            break

        handler = handlers.get(action)
        if handler:
            handler()
