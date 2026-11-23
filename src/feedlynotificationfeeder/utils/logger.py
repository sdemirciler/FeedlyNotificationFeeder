"""logger.py - logging setup (console + rotating file).

Call setup_logging() once at startup. Every other module then just does:

    log = logging.getLogger("module_name")
"""
import logging
import sys
import threading
from logging.handlers import RotatingFileHandler

from feedlynotificationfeeder.config import config

_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_configured = False


def _log_uncaught(exc_type, exc_value, exc_tb):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    logging.getLogger("uncaught").critical(
        "Unhandled exception", exc_info=(exc_type, exc_value, exc_tb)
    )


def _log_uncaught_thread(args):
    if issubclass(args.exc_type, KeyboardInterrupt):
        return
    logging.getLogger("uncaught").critical(
        "Unhandled exception in thread %s",
        getattr(args.thread, "name", "?"),
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


def setup_logging():
    global _configured
    if _configured:
        return

    # Windows consoles often use a legacy code page; headlines contain curly
    # quotes, accents, etc. Make the console tolerant instead of erroring.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    formatter = logging.Formatter(_FORMAT)

    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(config.LOG_LEVEL)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    # Third-party libraries are chatty at INFO/DEBUG.
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Anything that escapes our own error handling still ends up in the log.
    sys.excepthook = _log_uncaught
    threading.excepthook = _log_uncaught_thread

    _configured = True
