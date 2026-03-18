import requests
from core.config import get_screenshot_api_config


def take_screenshot(payload):
    base_url, headers = get_screenshot_api_config()
    response = requests.post(base_url, headers=headers, json=payload)

    content_type = response.headers.get("Content-Type", "")

    if "application/json" in content_type:
        data = response.json()
        error_msg = data.get("errors") or data.get("messages") or data
        return None, None, error_msg

    if response.status_code != 200:
        return None, None, f"HTTP {response.status_code}: {response.text[:200]}"

    return response.content, content_type, None
