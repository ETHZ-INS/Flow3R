"""
Centralised logging setup for Flow3R.

Call ``setup_logging()`` once at application startup (in main.py) before
importing any other Flow3R modules.  Every subsequent module that wants to
log something just does::

    from flow3r.logger import get_logger
    logger = get_logger(__name__)

A new, timestamped log file is created on every application start so that
individual runs can be reviewed independently.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Module-level reference so callers can check whether setup has run.
_log_file: Path | None = None
_initialized: bool = False


def setup_logging(log_dir: Path | None = None) -> logging.Logger:
    global _log_file, _initialized
    if _initialized:
        return get_logger()

    if log_dir is None:
        log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    _log_file = log_dir / f"flow3r_{timestamp}.log"

    file_formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_formatter = logging.Formatter(fmt="[%(levelname)s] %(name)s: %(message)s")

    file_handler = logging.FileHandler(_log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # ── Root logger: catches everything from all libraries ──────────────
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # ── flow3r logger: stop propagation to avoid duplicate entries ──────
    flow3r_logger = logging.getLogger("flow3r")
    flow3r_logger.setLevel(logging.DEBUG)
    flow3r_logger.propagate = False
    flow3r_logger.addHandler(file_handler)
    flow3r_logger.addHandler(console_handler)

    _initialized = True
    flow3r_logger.info("Logging initialised — log file: %s", _log_file)
    return flow3r_logger


def get_logger(name: str = "flow3r") -> logging.Logger:
    """Return a child logger under the ``flow3r`` hierarchy.

    Parameters
    ----------
    name:
        Typically ``__name__`` of the calling module.  If the name does not
        already start with ``"flow3r"`` it is prepended automatically so that
        all loggers stay within the same hierarchy.
    """
    if not name.startswith("flow3r"):
        name = f"flow3r.{name}"
    return logging.getLogger(name)


