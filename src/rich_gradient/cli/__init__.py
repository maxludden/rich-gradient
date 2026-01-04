"""rich-gradient CLI entry point."""

from __future__ import annotations

import sys
from typing import Any, Callable, MutableMapping, Sequence

import rich_click as click

from .common import VERSION
from .markdown_command import markdown_command
from .panel_command import panel_command
from .rule_command import rule_command
from .text_command import print_command


class DefaultCommandGroup(click.Group):
    """Route unknown commands/options to the default command."""

    def __init__(
        self,
        name: str | None = None,
        commands: MutableMapping[str, click.Command]
        | Sequence[click.Command]
        | None = None,
        invoke_without_command: bool = False,
        no_args_is_help: bool | None = None,
        subcommand_metavar: str | None = None,
        chain: bool = False,
        result_callback: Callable[..., Any] | None = None,
        *,
        default_cmd_name: str = "print",
        **kwargs: Any,
    ) -> None:
        super().__init__(
            name=name,
            commands=commands,
            invoke_without_command=invoke_without_command,
            no_args_is_help=no_args_is_help,
            subcommand_metavar=subcommand_metavar,
            chain=chain,
            result_callback=result_callback,
            **kwargs,
        )
        self.default_cmd_name = default_cmd_name

    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command | None, list[str]]:
        if args:
            cmd = click.Group.get_command(self, ctx, args[0])
            if cmd is None or args[0].startswith("-"):
                args.insert(0, self.default_cmd_name)
        return super().resolve_command(ctx, args)


@click.group(
    invoke_without_command=True,
    cls=DefaultCommandGroup,
    context_settings=dict(
        help_option_names=["-h", "--help"],
        allow_extra_args=True,
        ignore_unknown_options=True,
    ),
    default_cmd_name="print",
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
        if ctx.args or not sys.stdin.isatty():
            print_command.main(
                args=list(ctx.args),
                prog_name=ctx.command_path,
                standalone_mode=False,
            )
            return
        click.echo(ctx.get_help())


cli.add_command(print_command)
cli.add_command(panel_command)
cli.add_command(rule_command)
cli.add_command(markdown_command)

app = cli

__all__ = ["cli", "app"]


if __name__ == "__main__":  # pragma: no cover
    cli()
