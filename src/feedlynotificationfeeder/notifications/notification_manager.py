"""notification_manager.py - sends push notifications to the iPhone via ntfy.

Run `python notification_manager.py` to send a test notification.

Design notes
------------
* Messages are published as JSON (POST to the server root with the topic in
  the body). The alternative, putting the title in an HTTP header, breaks on
  headlines containing accents or curly quotes, because headers are not
  UTF-8 safe. JSON has no such problem.
* send_notification() never raises. It logs what went wrong and returns
  False, so one failed notification can't take the monitor down.
"""
import logging
import sys
from datetime import datetime

import requests

from feedlynotificationfeeder.config import config

log = logging.getLogger("notification_manager")

_MAX_TITLE_CHARS = 200
_MAX_MESSAGE_BYTES = 3500   # ntfy's hard limit is 4096 bytes; keep headroom

_session = requests.Session()


def _clip_bytes(text, limit):
    raw = text.encode("utf-8")
    if len(raw) <= limit:
        return text
    return raw[: limit - 3].decode("utf-8", errors="ignore") + "..."


def send_notification(title, message, click_url=None, priority=None, tags=None):
    """Send one push notification through ntfy.

    title      Bold first line on the lock screen.
    message    Body text.
    click_url  Optional. Tapping the notification opens this URL.
    priority   Optional. 1 (min) to 5 (max); ntfy's default is 3.
    tags       Optional list of tags; names matching emoji shortcodes
               (e.g. "newspaper") are shown as emoji.

    Returns True if ntfy accepted the message, False otherwise.
    Note: True means the server accepted it, not that the phone received it.
    """
    topic = (config.NTFY_TOPIC or "").strip()
    if not topic:
        log.error(
            "NTFY_TOPIC is not set. Create config_local.py next to config.py "
            "containing: NTFY_TOPIC = \"your-topic-name\""
        )
        return False

    title = str(title)
    if len(title) > _MAX_TITLE_CHARS:
        title = title[: _MAX_TITLE_CHARS - 3] + "..."

    payload = {
        "topic": topic,
        "title": title,
        "message": _clip_bytes(str(message), _MAX_MESSAGE_BYTES),
    }
    if click_url:
        payload["click"] = click_url
    if priority:
        payload["priority"] = int(priority)
    if tags:
        payload["tags"] = list(tags)

    headers = {}
    if config.NTFY_TOKEN:
        headers["Authorization"] = "Bearer " + config.NTFY_TOKEN

    server = config.NTFY_SERVER.rstrip("/")

    try:
        resp = _session.post(
            server, json=payload, headers=headers, timeout=config.NTFY_TIMEOUT
        )
    except requests.exceptions.Timeout:
        log.error("ntfy request timed out (server=%s)", server)
        return False
    except requests.exceptions.RequestException as exc:
        log.error("ntfy request failed (server=%s): %s", server, exc)
        return False

    if resp.status_code == 200:
        log.info("Notification sent: %s", title)
        return True

    if resp.status_code == 429:
        log.warning(
            "ntfy rate limit hit (HTTP 429). Retry-After=%s. Response: %s",
            resp.headers.get("Retry-After", "not provided"),
            resp.text[:200],
        )
        return False

    if resp.status_code in (401, 403):
        log.error(
            "ntfy refused the message (HTTP %s): check NTFY_TOKEN / topic "
            "permissions. Response: %s", resp.status_code, resp.text[:200],
        )
        return False

    log.error("ntfy returned HTTP %s: %s", resp.status_code, resp.text[:200])
    return False


if __name__ == "__main__":
    from feedlynotificationfeeder.utils.logger import setup_logging

    setup_logging()
    log.info("Sending test notification...")
    ok = send_notification(
        title="Feedly Monitor test \u2713 caf\u00e9 \u2014 \u201cquotes\u201d",
        message="Test source \u00b7 " + datetime.now().strftime("%H:%M:%S")
        + "\nIf you can read this on your lock screen, ntfy is working.",
        click_url="https://example.com",
        tags=["newspaper"],
    )
    sys.exit(0 if ok else 1)
