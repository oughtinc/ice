from ice.logging import init_logging

init_logging()

try:
    from .version import __version__
except ImportError:
    # version.py is auto-generated with the git tag when building
    __version__ = ""
