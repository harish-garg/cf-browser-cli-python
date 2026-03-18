import os
import sys
from dotenv import load_dotenv

load_dotenv()

JOBS_FILE = "crawl_jobs.json"
OUTPUT_DIR = "output"

TERMINAL_STATUSES = {
    "completed",
    "cancelled_due_to_timeout",
    "cancelled_due_to_limits",
    "cancelled_by_user",
    "errored",
    "error",
    "failed",
}

SUCCESS_STATUSES = {"completed"}

FAILURE_STATUSES = TERMINAL_STATUSES - SUCCESS_STATUSES

RESOURCE_TYPES = [
    "image",
    "media",
    "font",
    "stylesheet",
    "script",
    "xhr",
    "fetch",
    "websocket",
    "eventsource",
    "manifest",
    "texttrack",
    "other",
]

DEFAULT_REJECT_RESOURCES = ["image", "media", "font", "stylesheet"]

CRAWL_SOURCES = ["all", "sitemaps", "links"]

OUTPUT_FORMATS = ["html", "markdown", "json"]

SCREENSHOT_FORMATS = ["png", "jpeg", "webp"]

WAIT_UNTIL_OPTIONS = ["load", "domcontentloaded", "networkidle0", "networkidle2"]


def _get_credentials():
    account_id = os.environ.get("CF_ACCOUNT_ID")
    api_token = os.environ.get("CF_API_TOKEN")

    if not account_id or not api_token:
        print("Error: CF_ACCOUNT_ID and CF_API_TOKEN must be set in .env")
        sys.exit(1)

    return account_id, api_token


def get_api_config():
    account_id, api_token = _get_credentials()
    base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering/crawl"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    return base_url, headers


def get_screenshot_api_config():
    account_id, api_token = _get_credentials()
    base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering/screenshot"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    return base_url, headers
