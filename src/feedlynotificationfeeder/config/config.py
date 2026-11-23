"""config.py - central configuration.

Defaults live here. Anything personal (your ntfy topic, access tokens) goes in
a file called config_local.py that you create yourself. Later updates to this
file will never overwrite it, and values in it win over the defaults below.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]

# ----------------------------------------------------------------- ntfy
NTFY_SERVER = os.getenv("NTFY_SERVER", "https://ntfy.sh")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "")    # set this in config_local.py
NTFY_TOKEN = os.getenv("NTFY_TOKEN", "")    # only needed if your server requires auth
NTFY_TIMEOUT = (5, 10)                      # (connect, read) timeouts in seconds

# ----------------------------------------------------------------- files
OPML_FILE = BASE_DIR / "feedly.opml"
SEEN_FILE = BASE_DIR / "seen_articles.json"
LOG_FILE = BASE_DIR / "feedly_monitor.log"

# ----------------------------------------------------------------- logging
LOG_LEVEL = "INFO"                          # DEBUG for more detail
LOG_MAX_BYTES = 5 * 1024 * 1024             # rotate at 5 MB...
LOG_BACKUP_COUNT = 5                        # ...and keep 5 old files

# ----------------------------------------------------------------- local overrides
try:
    from .config_local import *  # noqa: F401,F403
except ImportError:
    pass
