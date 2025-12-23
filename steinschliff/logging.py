"""
Логирование проекта.

Выделено в отдельный модуль, чтобы `utils.py` не был "свалкой" и чтобы
логирование не тянуло за собой I/O и UI.
"""

import logging

from rich.logging import RichHandler
from rich.traceback import install as rich_traceback_install

logger = logging.getLogger("steinschliff.logging")


def setup_logging(level: int = logging.INFO) -> None:
    """Настраивает логирование для приложения (консоль через RichHandler)."""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    rich_traceback_install(show_locals=True)
    console_handler: logging.Handler = RichHandler(rich_tracebacks=True, tracebacks_show_locals=True)
    console_handler.setLevel(level)
    formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(formatter)

    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)

    logger.setLevel(level)
    logger.info("Логирование настроено с уровнем %s", logging.getLevelName(level))
