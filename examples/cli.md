# rich-gradient CLI

The `rich-gradient` CLI uses Click + rich-click to mirror the library defaults. Use it to experiment quickly without writing code.

## Installation

```bash
pip install rich-gradient
```

From a clone:

```bash
pip install -e .
python -m rich_gradient.cli --help
```

## Commands & examples

### `print`

- `rich-gradient print "Hello [b]world[/b]!" -c magenta,cyan`
- `rich-gradient print "Rainbow!" --rainbow`
- `echo "stdin" | rich-gradient print --colors "#f00,#0ff"`

Options: `--colors/-c`, `--bgcolors`, `--rainbow`, `--hues`, `--style`, `--justify`, `--overflow`, `--no-wrap`, `--end`

### `rule`

- `rich-gradient rule --title "Section" -c red,blue`
- `rich-gradient rule -T 3 --bgcolors "#111,#333"`

Options: `--title`, `--title-style`, `--colors`, `--bgcolors`, `--rainbow`, `--hues`, `--thickness`, `--align`, `--end`

### `panel`

- `rich-gradient panel "Panel content" -c red,blue --title "Gradient Panel"`
- `rich-gradient panel "Centered" --text-justify center --justify center`
- `rich-gradient panel "Animate me" --rainbow -a -d 8`

Options: `--colors`, `--bgcolors`, `--rainbow`, `--hues`, `--title`, `--title-style`, `--title-align`, `--subtitle`, `--subtitle-style`, `--subtitle-align`, `--style`, `--border-style`, `--padding`, `--vertical-justify`, `--text-justify`, `--justify`, `--expand/--no-expand`, `--width`, `--height`, `--box`, `--end`, `--animate`, `--duration`

### `markdown`

- `rich-gradient markdown "# Title" --colors "#ff0,#0ff" --justify center`
- `rich-gradient markdown "**Bold** body" --rainbow --vertical-justify middle`
- `rich-gradient markdown "Live!" -a -d 6`

Options: `--colors`, `--bgcolors`, `--rainbow`, `--hues`, `--style`, `--justify`, `--vertical-justify`, `--overflow`, `--no-wrap`, `--end`, `--animate`, `--duration`

## Notes

- `rich-gradient --version` prints the version.
- `--help` on any command shows the rich-click styled usage.
