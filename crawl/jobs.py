import os
import json
import time
from crawl.config import JOBS_FILE


def load_jobs():
    if os.path.exists(JOBS_FILE):
        with open(JOBS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_jobs(jobs):
    with open(JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)


def add_job(job_id, url, payload, label=None):
    jobs = load_jobs()
    job = {
        "job_id": job_id,
        "url": url,
        "label": label,
        "payload": payload,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "pending",
    }
    jobs.append(job)
    save_jobs(jobs)
    return job


def update_job(job_id, **fields):
    jobs = load_jobs()
    for job in jobs:
        if job["job_id"] == job_id:
            job.update(fields)
            break
    save_jobs(jobs)


def find_job(job_id):
    jobs = load_jobs()
    for job in jobs:
        if job["job_id"] == job_id:
            return job
    return None


def delete_jobs(job_ids):
    jobs = load_jobs()
    jobs = [j for j in jobs if j["job_id"] not in job_ids]
    save_jobs(jobs)


def get_jobs_by_status(status):
    jobs = load_jobs()
    return [j for j in jobs if j.get("status") == status]
