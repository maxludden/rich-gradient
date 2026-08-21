"""Regression tests for v0.4.0 side-effect and constructor fixes.

Covers: import-time excepthook hygiene, the install_tracebacks opt-in paths,
get_logger's library-safe handler management, and the Panel/Rule/AnimatedRule
constructor fixes.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, cast

import pytest
from loguru import logger
from rich.console import Console
from rich.style import Style


def _run_python(code: str, extra_env: dict[str, str] | None = None) -> str:
    """Run a snippet in a clean subprocess and return stdout."""
    env = {**os.environ, **(extra_env or {})}
    env.pop("RICH_GRADIENT_TRACEBACKS", None)
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=env,
        check=True,
        cwd=str(Path(__file__).resolve().parents[1]),
    )
    return result.stdout.strip()


SRC_PATH_PREFIX = "import sys; sys.path.insert(0, 'src'); "


def test_import_does_not_touch_excepthook() -> None:
    """Importing rich_gradient must not replace sys.excepthook."""
    out = _run_python(
        SRC_PATH_PREFIX
        + "before = sys.excepthook; import rich_gradient; "
        + "print(sys.excepthook is before)"
    )
    assert out == "True"


def test_install_tracebacks_helper_installs_hook() -> None:
    """install_tracebacks() must replace sys.excepthook when called."""
    out = _run_python(
        SRC_PATH_PREFIX
        + "before = sys.excepthook; import rich_gradient; "
        + "rich_gradient.install_tracebacks(); "
        + "print(sys.excepthook is not before)"
    )
    assert out == "True"


def test_tracebacks_env_var_opt_in() -> None:
    """RICH_GRADIENT_TRACEBACKS=1 restores the automatic install."""
    out = _run_python(
        SRC_PATH_PREFIX
        + "before = sys.excepthook; import rich_gradient; "
        + "print(sys.excepthook is not before)",
        extra_env={"RICH_GRADIENT_TRACEBACKS": "1"},
    )
    assert out == "True"


class TestGetLoggerHandlerSafety:
    """get_logger must never disturb application loguru handlers."""

    def test_app_handler_survives_and_sinks_do_not_stack(self) -> None:
        import rich_gradient._logger as logger_module

        get_logger = logger_module.get_logger

        records: list[str] = []
        app_id = logger.add(lambda m: records.append(str(m)), level="DEBUG")
        tmp = Path(tempfile.mkdtemp())
        try:
            get_logger(enabled=True, log_dir=tmp)
            get_logger(enabled=True, log_dir=tmp)
            assert logger_module._file_handler_id is not None
            assert logger_module._console_handler_id is not None

            logger.info("app message")
            assert any("app message" in r for r in records)

            trace = tmp / "trace.log"
            content = trace.read_text() if trace.exists() else ""
            assert "app message" not in content  # filtered out of our sink

            # Library-origin records do reach the trace file.
            logger.patch(
                lambda r: cast(Any, r).update(name="rich_gradient.test")
            ).info("library message")
            assert "library message" in trace.read_text()
        finally:
            get_logger(enabled=False)
            logger.remove(app_id)  # must not raise: our disable left it alone
        assert logger_module._file_handler_id is None
        assert logger_module._console_handler_id is None

    def test_disable_removes_only_own_sinks(self) -> None:
        import rich_gradient._logger as logger_module

        get_logger = logger_module.get_logger

        app_id = logger.add(lambda m: None, level="INFO")
        tmp = Path(tempfile.mkdtemp())
        get_logger(enabled=True, log_dir=tmp)
        get_logger(enabled=False)
        assert logger_module._file_handler_id is None
        assert logger_module._console_handler_id is None
        logger.remove(app_id)  # would raise ValueError if we had removed it


def test_panel_accepts_style_instance() -> None:
    """Panel(style=Style(...)) must construct and render (was a crash)."""
    from rich_gradient.panel import Panel

    with open(os.devnull, "w", encoding="utf-8") as output:
        console = Console(width=40, file=output, force_terminal=True)
        console.print(Panel("hi", style=Style(bold=True), colors=["#f00", "#00f"]))


def test_rule_constructs_without_title() -> None:
    """Rule() with no arguments must construct and render."""
    from rich_gradient.rule import Rule

    with open(os.devnull, "w", encoding="utf-8") as output:
        console = Console(width=40, file=output, force_terminal=True)
        console.print(Rule())


def test_rule_thickness_error_message() -> None:
    """Out-of-range thickness reports an accurate, integer-based message."""
    from rich_gradient.rule import Rule

    with pytest.raises(ValueError, match=r"integer between 0 and 3"):
        Rule(title="x", thickness=9)


def test_animated_rule_config_driven_phase_speed() -> None:
    """animate=None + config animation enabled must use the faster phase."""
    from rich_gradient.animated_rule import AnimatedRule

    rule = AnimatedRule(title="t", animate=True)
    assert rule._phase_per_second == 0.25

    resolved = AnimatedRule(title="t", animate=None)
    if resolved.animate:  # global config enabled (the default)
        assert resolved._phase_per_second == 0.25
