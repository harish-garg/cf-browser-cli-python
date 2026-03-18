import time
import requests
from core.config import get_api_config, TERMINAL_STATUSES, SUCCESS_STATUSES, FAILURE_STATUSES
from core.jobs import update_job


def start_crawl(payload):
    base_url, headers = get_api_config()
    response = requests.post(base_url, headers=headers, json=payload)

    if response.status_code != 200 or not response.json().get("success"):
        return None, response.json()

    job_id = response.json()["result"]
    return job_id, None


def get_crawl_status(job_id):
    base_url, headers = get_api_config()
    response = requests.get(f"{base_url}/{job_id}", headers=headers)
    data = response.json()

    if not data.get("success"):
        return None, data

    return data["result"], None


def get_crawl_results_paginated(job_id, limit_per_page=100, status_filter=None):
    base_url, headers = get_api_config()
    all_records = []
    cursor = None
    total = None

    while True:
        params = {"limit": limit_per_page}
        if cursor:
            params["cursor"] = cursor
        if status_filter:
            params["status"] = status_filter

        response = requests.get(f"{base_url}/{job_id}", headers=headers, params=params)
        data = response.json()

        if not data.get("success"):
            return None, data

        result = data["result"]
        records = result.get("records", [])
        all_records.extend(records)

        if total is None:
            total = result.get("total", len(records))

        if total > 0:
            print(f"  Fetched {len(all_records)}/{total} records...")

        cursor = result.get("cursor")
        if not cursor or not records:
            break

    result["records"] = all_records
    return result, None


def cancel_crawl(job_id):
    base_url, headers = get_api_config()
    response = requests.delete(f"{base_url}/{job_id}", headers=headers)
    data = response.json()

    if not data.get("success"):
        return False, data

    update_job(job_id, status="cancelled_by_user")
    return True, None


def poll_until_complete(job_id, interval=3, on_status=None):
    while True:
        result, err = get_crawl_status(job_id)

        if err:
            return None, err

        status = result.get("status", "unknown")

        if on_status:
            on_status(status, result)
        else:
            print(f"  Status: {status}")

        if status in TERMINAL_STATUSES:
            is_success = status in SUCCESS_STATUSES
            return result, None if is_success else {"status": status, "result": result}

        time.sleep(interval)
