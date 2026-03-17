import os
import sys
import time
import json
import requests
import questionary
from dotenv import load_dotenv

load_dotenv()

JOBS_FILE = "crawl_jobs.json"
OUTPUT_DIR = "output"

account_id = os.environ.get("CF_ACCOUNT_ID")
api_token = os.environ.get("CF_API_TOKEN")

if not account_id or not api_token:
    print("Error: CF_ACCOUNT_ID and CF_API_TOKEN must be set in .env")
    sys.exit(1)

base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering/crawl"

headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json",
}


def load_jobs():
    if os.path.exists(JOBS_FILE):
        with open(JOBS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_jobs(jobs):
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)


def start_new_crawl():
    target_url = questionary.text(
        "URL to crawl:",
        default="https://example.com",
        validate=lambda val: True if val.startswith(("http://", "https://")) else "URL must start with http:// or https://",
    ).ask()

    if target_url is None:
        return

    limit = questionary.text(
        "Page limit:",
        default="100",
        validate=lambda val: True if val.isdigit() and int(val) > 0 else "Must be a positive number",
    ).ask()

    if limit is None:
        return

    resource_types = questionary.checkbox(
        "Resource types to reject:",
        choices=[
            questionary.Choice("image", checked=True),
            questionary.Choice("media", checked=True),
            questionary.Choice("font", checked=True),
            questionary.Choice("stylesheet", checked=True),
            questionary.Choice("script"),
        ],
    ).ask()

    if resource_types is None:
        return

    payload = {
        "url": target_url,
        "limit": int(limit),
        "rejectResourceTypes": resource_types,
    }

    print(f"\nStarting crawl for: {target_url}")
    response = requests.post(base_url, headers=headers, json=payload)

    if response.status_code != 200 or not response.json().get("success"):
        print(f"Failed to start crawl: {response.status_code}")
        print(response.json())
        return

    job_id = response.json()["result"]
    print(f"Job ID: {job_id}")

    # Save to master jobs file
    jobs = load_jobs()
    jobs.append({
        "job_id": job_id,
        "url": target_url,
        "limit": int(limit),
        "rejectResourceTypes": resource_types,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pending",
    })
    save_jobs(jobs)

    print("Waiting for crawl to complete...")
    while True:
        result_response = requests.get(f"{base_url}/{job_id}", headers=headers)
        data = result_response.json()

        if not data.get("success"):
            print(f"Error fetching results: {data}")
            return

        result = data["result"]
        status = result.get("status", "unknown")
        print(f"  Status: {status}")

        if status == "completed":
            break
        elif status in ("error", "failed"):
            print(f"Crawl failed: {result}")
            # Update status in master file
            jobs = load_jobs()
            for job in jobs:
                if job["job_id"] == job_id:
                    job["status"] = status
                    break
            save_jobs(jobs)
            return

        time.sleep(3)

    # Save full results to output/<job_id>.json
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = os.path.join(OUTPUT_DIR, f"{job_id}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Update master file
    jobs = load_jobs()
    for job in jobs:
        if job["job_id"] == job_id:
            job["status"] = "completed"
            job["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            job["page_count"] = len(result.get("records", []))
            break
    save_jobs(jobs)

    page_count = len(result.get("records", []))
    print(f"Crawl complete! {page_count} page(s) saved to {output_file}")


def list_previous_crawls():
    jobs = load_jobs()

    if not jobs:
        print("No previous crawls found.")
        return

    print(f"\nFound {len(jobs)} crawl(s):\n")
    for job in reversed(jobs):
        status = job.get("status", "unknown")
        print(f"  {job['job_id']}")
        print(f"    URL: {job['url']}  |  Status: {status}  |  Started: {job['started_at']}")
        if job.get("page_count") is not None:
            print(f"    Pages: {job['page_count']}")
        print()


def check_job_status():
    jobs = load_jobs()
    pending = [j for j in jobs if j.get("status") == "pending"]

    if not pending:
        print("No pending jobs to check.")
        return

    choices = [
        questionary.Choice(
            f"{j['job_id'][:8]}...  {j['url']}  (started {j['started_at']})",
            value=j["job_id"],
        )
        for j in reversed(pending)
    ]
    choices.append(questionary.Choice("Back", value=None))

    job_id = questionary.select("Select a job to check:", choices=choices).ask()
    if job_id is None:
        return

    print(f"\nChecking status for {job_id}...")
    result_response = requests.get(f"{base_url}/{job_id}", headers=headers)
    data = result_response.json()

    if not data.get("success"):
        print(f"Error fetching status: {data}")
        return

    result = data["result"]
    status = result.get("status", "unknown")
    print(f"  Status: {status}")

    if status == "completed":
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        output_file = os.path.join(OUTPUT_DIR, f"{job_id}.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        for job in jobs:
            if job["job_id"] == job_id:
                job["status"] = "completed"
                job["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                job["page_count"] = len(result.get("records", []))
                break
        save_jobs(jobs)
        page_count = len(result.get("records", []))
        print(f"  Crawl complete! {page_count} page(s) saved to {output_file}")

    elif status in ("error", "failed"):
        for job in jobs:
            if job["job_id"] == job_id:
                job["status"] = status
                break
        save_jobs(jobs)
        print(f"  Crawl failed.")

    else:
        print(f"  Job is still {status}. Try again later.")


def main():
    while True:
        action = questionary.select(
            "What would you like to do?",
            choices=["Start a new crawl", "Check job status", "List previous crawls", "Exit"],
        ).ask()

        if action is None or action == "Exit":
            break

        if action == "Start a new crawl":
            start_new_crawl()
        elif action == "Check job status":
            check_job_status()
        elif action == "List previous crawls":
            list_previous_crawls()


if __name__ == "__main__":
    main()
