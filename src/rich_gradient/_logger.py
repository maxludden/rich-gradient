"""
Logger utility for rich-gradient.
Provides a Rich-styled, rotating, compressed log file and console output via loguru.
"""

from pathlib import Path
from typing import Optional

from loguru import logger
from rich import get_console
from rich.console import Console
from rich.style import Style
from rich.text import Text
from rich.traceback import install as tr_install

console: Console = get_console()
tr_install(console=console)


def get_logger(
    enabled: bool = True,
    log_level: str = "TRACE",
    log_dir: Optional[Path] = None,
    style: str = "blue",
):
    """
    Create and configure a loguru Logger for rich-gradient.

    Args:
        enabled (bool): If False, disables logging.
        log_level (str): Log level for file output.
        log_dir (Optional[Path]): Directory for log files. Defaults to ./logs.
        style (str): Rich style for console log output.

    Returns:
        Logger: Configured loguru logger.
    """
    if not enabled:
        logger.disable("rich_gradient")
        return logger

    log_dir = log_dir or (Path.cwd() / "logs")
    try:
        log_dir.mkdir(exist_ok=True)
    except Exception as e:
        console.log(f"Failed to create log directory: {e}", style="bold red")
    trace_log_file = log_dir / "trace.log"

    logger.remove()
    log = logger.bind(name="rich_gradient")
    log.add(
        trace_log_file,
        format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
        level=log_level,
        rotation="10 MB",
        compression="zip",
    )

    def rich_console_sink(msg):
        try:
            # If msg is already a string, wrap it in Text for styled console output.
            if isinstance(msg, Text):
                console.log(msg)
            else:
                console.log(Text(str(msg), style=Style(color=style, bold=True)))
        except Exception as e:
            console.log(f"Logger console sink error: {e}", style="bold red")

    log.add(rich_console_sink)
    return log
