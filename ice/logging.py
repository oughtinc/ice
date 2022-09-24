import logging
import sys

from structlog import configure
from structlog import get_logger
from structlog import make_filtering_bound_logger
from structlog import PrintLoggerFactory
from structlog.dev import ConsoleRenderer
from structlog.dev import set_exc_info
from structlog.processors import add_log_level
from structlog.processors import format_exc_info
from structlog.processors import TimeStamper
from structlog.types import Processor


def init_logging():
    processors: list[Processor] = [
        add_log_level,
        TimeStamper(fmt="%Y-%m-%d %H:%M.%S.%f", utc=False),
        set_exc_info,
        format_exc_info,
        ConsoleRenderer(colors=sys.stdout is not None and sys.stdout.isatty()),
    ]
    configure(
        processors,
        cache_logger_on_first_use=True,
        logger_factory=PrintLoggerFactory(),
        wrapper_class=make_filtering_bound_logger(logging.INFO),
    )

    log = get_logger()
    log.debug("Logging initialized")
