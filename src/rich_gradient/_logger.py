from typing import Optional, Union, List, Tuple, Dict, TYPE_CHECKING
from pathlib import Path

from rich import get_console
from rich.console import Console
from rich.text import Text
from rich.style import Style
from rich.traceback import install as tr_install
import loguru
from loguru import logger
if TYPE_CHECKING:
    from loguru import Record, Message, Logger

console: Console = get_console()
tr_install(console=console)

LOGS_DIR = Path.cwd() / "logs"
if not LOGS_DIR.exists():
    LOGS_DIR.mkdir(exist_ok=True)
TRACE_LOG_FILE = LOGS_DIR / "trace.log"

def get_logger():
    logger.remove()
    log = logger.bind(name="rich_gradient")
    log.add(
        TRACE_LOG_FILE,
        format="{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}",
        level="TRACE",
        rotation="10 MB",
        compression="zip",
    )
    log.add(
        lambda msg: console.log(
            Text(msg, style=Style(color="blue", bold=True)),
            markup=True,
        ),
    )
    return log
