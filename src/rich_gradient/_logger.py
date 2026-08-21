"""
Logger utility for rich-gradient.
Provides a Rich-styled, rotating, compressed log file and console output via loguru.

This module follows loguru's library convention: rich-gradient's log records
are disabled by default and the package never removes or shadows handlers the
host application has configured. Enabling logging adds sinks that are filtered
to ``rich_gradient`` records only, and only those sinks are ever removed again.
"""

from pathlib import Path
from threading import Lock
from typing import Any

from loguru import logger
from rich import get_console
from rich.console import Console
from rich.style import Style
from rich.text import Text

# Imported as a module (not `from ... import config`) so get_logger resolves
# the config at call time and honors reload_config().
import rich_gradient.config as _config_module

console: Console = get_console()

# Handler ids for sinks this module has added, so repeated calls (or a later
# disable) remove only rich-gradient's own sinks — never the application's.
_handler_ids: list[int] = []
# Serializes the remove-then-add sequence so concurrent get_logger calls
# cannot interleave and leak duplicate sinks.
_handler_lock = Lock()


def _remove_own_handlers() -> None:
    """Remove only the sinks previously added by this module."""
    while _handler_ids:
        handler_id = _handler_ids.pop()
        try:
            logger.remove(handler_id)
        except ValueError:
            # Already removed (e.g., the application reset loguru itself).
            pass


def get_logger(
    enabled: bool = True,
    log_level: str = "TRACE",
    log_dir: Path | None = None,
    style: str = "blue",
) -> Any:
    """
    Enable and configure rich-gradient's loguru logging.

    When enabled, this activates the ``rich_gradient`` record namespace and
    adds two sinks — a rotating, compressed trace file and a Rich-styled
    console sink — both filtered to rich-gradient's own records. Handlers
    configured by the host application are never removed or modified, and
    application log records never leak into rich-gradient's sinks. Because
    the sinks are filtered by record origin, only records emitted from
    ``rich_gradient.*`` modules reach them; route application logging through
    your own loguru handlers instead. Calling this repeatedly replaces only
    the sinks it previously added.

    Args:
        enabled (bool): If False, disable rich-gradient logging and remove any
            sinks this function previously added.
        log_level (str): Log level for file output.
        log_dir (Path | None): Directory for log files. Defaults to
            ``<config home>/logs`` (``~/.rich-gradient/logs``).
        style (str): Rich style for console log output.

    Returns:
        Logger: The loguru logger.
    """
    if not enabled:
        with _handler_lock:
            _remove_own_handlers()
        logger.disable("rich_gradient")
        return logger

    logger.enable("rich_gradient")
    log_dir = log_dir or (_config_module.config.home_dir / "logs")
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        console.log(f"Failed to create log directory: {e}", style="bold red")
    trace_log_file = log_dir / "trace.log"

    def rich_console_sink(msg: object) -> None:
        try:
            # If msg is already a string, wrap it in Text for styled console output.
            if isinstance(msg, Text):
                console.log(msg)
            else:
                console.log(Text(str(msg), style=Style(color=style, bold=True)))
        except (TypeError, ValueError, OSError, UnicodeError, AttributeError) as e:
            console.log(f"Logger console sink error: {e}", style="bold red")

    with _handler_lock:
        _remove_own_handlers()
        _handler_ids.append(
            logger.add(
                trace_log_file,
                format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
                level=log_level,
                rotation="10 MB",
                compression="zip",
                filter="rich_gradient",
            )
        )
        _handler_ids.append(logger.add(rich_console_sink, filter="rich_gradient"))
    return logger
