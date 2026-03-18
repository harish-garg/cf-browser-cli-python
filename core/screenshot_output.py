import os
import json
import time
from core.config import OUTPUT_DIR
from core.output import sanitize_filename

SCREENSHOTS_DIR = os.path.join(OUTPUT_DIR, "screenshots")
SCREENSHOT_LOG = os.path.join(SCREENSHOTS_DIR, "screenshot_log.json")


def save_screenshot(url, image_bytes, content_type="image/png", label=None):
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    ext_map = {
        "image/png": "png",
        "image/jpeg": "jpeg",
        "image/webp": "webp",
    }
    ext = ext_map.get(content_type, "png")

    slug = sanitize_filename(url)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    label_part = f"_{sanitize_filename(label)}" if label else ""
    filename = f"{slug}{label_part}_{timestamp}.{ext}"

    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(image_bytes)

    return filepath


def log_screenshot(url, filepath, payload=None):
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    entries = []
    if os.path.exists(SCREENSHOT_LOG):
        with open(SCREENSHOT_LOG, "r", encoding="utf-8") as f:
            entries = json.load(f)

    entries.append({
        "url": url,
        "filepath": filepath,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "payload": payload,
    })

    with open(SCREENSHOT_LOG, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
