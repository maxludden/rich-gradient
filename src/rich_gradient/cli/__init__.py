"""rich-gradient CLI entry point."""

from __future__ import annotations

import rich_click as click

from .common import VERSION
from .markdown_command import markdown_command
from .panel_command import panel_command
from .rule_command import rule_command
from .text_command import print_command


@click.group(
    invoke_without_command=True,
    context_settings=dict(help_option_names=["-h", "--help"]),
    help="Create gradient-rich text, panels, and markdown.",
)
@click.version_option(version=VERSION, message="%(prog)s version %(version)s")
@click.pass_context
def cli(ctx: click.Context | None = None) -> None:
    """rich-gradient CLI tool. Use subcommands to print gradients, panels, rules, or markdown."""
    if ctx is None:
        ctx = click.get_current_context()
    assert ctx is not None
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


cli.add_command(print_command)
cli.add_command(panel_command)
cli.add_command(rule_command)
cli.add_command(markdown_command)

app = cli

__all__ = ["cli", "app"]


if __name__ == "__main__":  # pragma: no cover
    cli()
