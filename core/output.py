import os
import re
import json
from core.config import OUTPUT_DIR


def sanitize_filename(url):
    name = re.sub(r"https?://", "", url)
    name = re.sub(r"[^\w\-.]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name[:200] if name else "page"


def find_result_path(job_id):
    new_path = os.path.join(OUTPUT_DIR, job_id, "raw.json")
    if os.path.exists(new_path):
        return new_path

    old_path = os.path.join(OUTPUT_DIR, f"{job_id}.json")
    if os.path.exists(old_path):
        return old_path

    return None


def load_result(job_id):
    path = find_result_path(job_id)
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_results(job_id, result, formats=None):
    job_dir = os.path.join(OUTPUT_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    raw_path = os.path.join(job_dir, "raw.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    records = result.get("records", [])
    if not records or not formats:
        return raw_path

    pages_dir = os.path.join(job_dir, "pages")
    os.makedirs(pages_dir, exist_ok=True)

    all_markdown = []
    all_json_data = []

    for record in records:
        url = record.get("url", "unknown")
        slug = sanitize_filename(url)

        if "html" in (formats or []) and record.get("html"):
            html_path = os.path.join(pages_dir, f"{slug}.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(record["html"])

        if "markdown" in (formats or []) and record.get("markdown"):
            md_path = os.path.join(pages_dir, f"{slug}.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(record["markdown"])
            all_markdown.append(f"# {url}\n\n{record['markdown']}\n\n---\n\n")

        if "json" in (formats or []) and record.get("json"):
            json_path = os.path.join(pages_dir, f"{slug}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(record["json"], f, indent=2, ensure_ascii=False)
            all_json_data.append({"url": url, "data": record["json"]})

    if all_markdown:
        combined_md = os.path.join(job_dir, "combined.md")
        with open(combined_md, "w", encoding="utf-8") as f:
            f.writelines(all_markdown)

    if all_json_data:
        combined_json = os.path.join(job_dir, "combined.json")
        with open(combined_json, "w", encoding="utf-8") as f:
            json.dump(all_json_data, f, indent=2, ensure_ascii=False)

    return raw_path


def search_results(job_id, query):
    result = load_result(job_id)
    if not result:
        return []

    matches = []
    query_lower = query.lower()
    records = result.get("records", [])

    for record in records:
        url = record.get("url", "")

        searchable = ""
        if record.get("markdown"):
            searchable = record["markdown"]
        elif record.get("html"):
            searchable = record["html"]

        if query_lower in searchable.lower() or query_lower in url.lower():
            idx = searchable.lower().find(query_lower)
            snippet = ""
            if idx >= 0:
                start = max(0, idx - 80)
                end = min(len(searchable), idx + len(query) + 80)
                snippet = searchable[start:end].replace("\n", " ").strip()
                if start > 0:
                    snippet = "..." + snippet
                if end < len(searchable):
                    snippet = snippet + "..."

            matches.append({"url": url, "snippet": snippet})

    return matches


def get_statistics(job_id):
    result = load_result(job_id)
    if not result:
        return None

    records = result.get("records", [])
    status_counts = {}
    total_size = 0

    for record in records:
        status = record.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        for key in ("html", "markdown"):
            if isinstance(record.get(key), str):
                total_size += len(record[key].encode("utf-8"))

    return {
        "job_status": result.get("status", "unknown"),
        "total_records": len(records),
        "status_breakdown": status_counts,
        "total_content_size_bytes": total_size,
        "total_content_size_mb": round(total_size / (1024 * 1024), 2),
        "browser_seconds": result.get("browserSecondsUsed", 0),
    }


def diff_crawls(job_id_a, job_id_b):
    result_a = load_result(job_id_a)
    result_b = load_result(job_id_b)

    if not result_a or not result_b:
        return None

    urls_a = {r.get("url") for r in result_a.get("records", [])}
    urls_b = {r.get("url") for r in result_b.get("records", [])}

    return {
        "added": sorted(urls_b - urls_a),
        "removed": sorted(urls_a - urls_b),
        "common": sorted(urls_a & urls_b),
        "count_a": len(urls_a),
        "count_b": len(urls_b),
    }
