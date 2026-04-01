"""Application logger setup.

This configures a single `setup_logger` entrypoint. It prefers the
application data directory when available (via `utils.get_data_dir()`),
but falls back to a `logs/` folder next to the module.
"""
import logging
import os


def setup_logger(log_dir="logs", log_file="app.log"):
    """Initialize root logger once and return it.

    The function is safe to call multiple times; handlers will only be
    added on the first call.
    """
    # Prefer using the configured data directory when possible
    try:
        # import lazily to avoid circular import at startup
        from .utils import get_data_dir
        base = get_data_dir()
        path = os.path.join(base, log_dir)
    except Exception:
        base = os.path.dirname(__file__)
        path = os.path.join(base, log_dir)

    os.makedirs(path, exist_ok=True)
    full_path = os.path.join(path, log_file)

    logger = logging.getLogger()
    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        fh = logging.FileHandler(full_path, encoding="utf-8")
        fh.setFormatter(formatter)
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)

        logger.setLevel(logging.INFO)
        logger.addHandler(fh)
        logger.addHandler(ch)

    logging.info("Logger initialized at %s", full_path)
    return logger
