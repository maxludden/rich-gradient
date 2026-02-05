# rich-gradient CLI

The `rich-gradient` CLI is built with Click + rich-click and ships the same rendering defaults as the library. Use it to experiment with gradients, panels, rules, or markdown directly in your terminal.

## Installation

```bash
pip install rich-gradient
```

From a clone:

```bash
pip install -e .
python -m rich_gradient.cli --help
```

## Quick usage

The CLI assumes `print` when no subcommand is provided, and it can read from stdin.

- `rich-gradient "Hello [b]world[/b]!" -c magenta,cyan`
- `echo "$SHELL" | rich-gradient`

## Commands

### `print`

Render gradient text.

- Argument: `text...` (required unless stdin is provided, accepts multiple words)
- Options: `-c/--colors`, `--bgcolors`, `-r/--rainbow`, `--hues`, `--style`, `-j/--justify`, `--overflow`, `--no-wrap`, `--end`

Examples:

- `rich-gradient "Hello [b]world[/b]!" -c magenta,cyan`
- `rich-gradient print "Hello [b]world[/b]!" -c magenta,cyan`
- `rich-gradient print "Rainbow!" --rainbow`
- `echo "stdin" | rich-gradient print --colors "#f00,#0ff"`

### `rule`

Draw a gradient rule.

- Options: `-t/--title`, `-s/--title-style`, `-c/--colors`, `--bgcolors`, `-r/--rainbow`, `--hues`, `--end`, `-T/--thickness`, `-a/--align`

Examples:

- `rich-gradient rule --title "Section" -c red,blue`
- `rich-gradient rule -T 3 --bgcolors "#111,#333"`

### `panel`

Wrap text in a gradient panel (supports animation).

- Argument: `renderable` (required)
- Options: `-c/--colors`, `--bgcolors`, `-r/--rainbow`, `--hues`, `-t/--title`, `--title-style`, `--title-align`, `-s/--subtitle`, `--subtitle-style`, `--subtitle-align`, `--style`, `--border-style`, `-p/--padding`, `-V/--vertical-justify`, `-J/--text-justify`, `-j/--justify`, `--expand/--no-expand`, `--width`, `--height`, `--end`, `--box`, `-a/--animate`, `-d/--duration`

Examples:

- `rich-gradient panel "Panel content" -c red,blue --title "Gradient Panel"`
- `rich-gradient panel "Centered" --text-justify center --justify center`
- `rich-gradient panel "Animate me" --rainbow -a -d 8`

### `markdown`

Render markdown with a gradient (supports animation).

- Argument: `MARKDOWN` (required)
- Options: `-c/--colors`, `--bgcolors`, `-r/--rainbow`, `--hues`, `--style`, `-j/--justify`, `--vertical-justify`, `--overflow`, `--no-wrap`, `--end`, `--animate`, `-d/--duration`

Examples:

- `rich-gradient markdown "# Title" --colors "#ff0,#0ff" --justify center`
- `rich-gradient markdown "**Bold** body" --rainbow --vertical-justify middle`
- `rich-gradient markdown "Live!" -a -d 6`

## General notes

- `rich-gradient --version` prints the CLI version.
- All commands support `--help` for contextual usage.
- Rich markup is enabled by default; invalid markup will surface a clear error.
