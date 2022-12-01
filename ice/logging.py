import logging
import os
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

# Prevent logging the warning 'None of PyTorch...' at the end of transformers/__init__.py.
# This depends on this being the first place that transformers is imported.
# It also assumes that transformers will be imported eventually
# so eagerly importing it now doesn't have an extra cost.
previous_verbosity = os.environ.get("TRANSFORMERS_VERBOSITY", None)
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
import transformers  # noqa

# Allow using the TRANSFORMERS_VERBOSITY env var normally to still work,
# and avoid suppressing other warnings.
if previous_verbosity:  # Setting to None raises an error
    os.environ["TRANSFORMERS_VERBOSITY"] = previous_verbosity


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
