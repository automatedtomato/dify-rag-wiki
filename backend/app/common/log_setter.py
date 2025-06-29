import logging
import os
from logging import Formatter, StreamHandler, handlers
from typing import Any, Dict, Optional

from app.common.param_resolver import resolve_param

FORMAT = "%(levelname)-8s %(asctime)s - [%(filename)s:%(lineno)d]\t%(message)s"


def setup_logger(
    logger: logging.Logger,
    *,
    config: Optional[Dict[str, Any]] = None,
    log_level: Optional[str] = None,
    save_path: Optional[str] = None,
) -> logging.Logger:
    """
    Setup logger

    Args:
        logger (logging.Logger): Logger object

        ===== Either config or log_level and save_path should be provided =====
        config (Optional[Dict[str, Any]], optional): Config object. Defaults to None.
        log_level (Optional[str], optional): Log level. Defaults to None.
        save_path (Optional[str], optional): Save path. Defaults to None.

    Returns:
        logging.Logger: Configured logger object
    """

    _log_level = resolve_param(
        config_param=config.get("log_level") if config else None,
        dict_param=log_level,
        default="INFO",
        param_name="log_level",
    )

    _save_path = resolve_param(
        config_param=config.get("save_path") if config else None,
        dict_param=save_path,
        default=None,
        param_name="save_path",
    )

    if save_path is not None and not os.path.exists(_save_path):
        with open(_save_path, "w"):
            pass

    logger = _set_log_level(logger, _log_level)

    formatter = Formatter(FORMAT)

    st_handler = StreamHandler()
    st_handler.setFormatter(formatter)
    logger.addHandler(st_handler)

    if _save_path is not None:
        fl_handler = handlers.RotatingFileHandler(
            filename=_save_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )

        fl_handler.setFormatter(formatter)

        logger.addHandler(fl_handler)

    return logger


def _set_log_level(logger: logging.Logger, log_level: str) -> logging.Logger:

    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    upper_level = log_level.upper()

    if upper_level not in level_map:
        raise ValueError(f"Invalid log level: {log_level}")

    logger.setLevel(level_map[upper_level])

    return logger
