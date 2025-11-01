# rich-gradient CLI

The `rich-gradient` package ships with a Typer-powered command line interface for
rendering colourful gradients, animated gradients, and themed Rich components
directly in your terminal. This document walks through installation, everyday
usage, and all supported options.

## Installation

```bash
pip install rich-gradient rich-color-ext
```

When working from a cloned repository you can also run the CLI in editable mode:

```bash
pip install -e .
python -m rich_gradient.cli --help
```

The CLI installs shell completions automatically via Typer:

```bash
rich-gradient --install-completion  # choose bash, zsh, or fish
rich-gradient --show-completion zsh # preview the generated script
```

## Core Commands

Every command accepts text directly as an argument, via `text=...`, or by piping
data into standard input using `-`. Invalid Rich markup is reported with a
clear error message.

### `print`

Render gradient text or an animated gradient in place.

Arguments:

- `text`: Text to render, `-` for stdin, or `text=...`.

Options:

- `-c, --colors COLORS`: Comma-separated colour stops. (e.g. `#f00,#f90,#ff0`).
- `-R/ -n, --rainbow/--no-rainbow`: Generate a rainbow gradient (default: off).
- `-h, --hues INTEGER`: Number of hues when auto-generating colours (default: 7).
- `-j, --justify [left|center|right]`: Align the output (default: left).
- `-a, --animated`: Run an animated gradient instead of a static render.
- `-d, --duration FLOAT`: Animation length in seconds (default: 5).

Examples:

```bash
rich-gradient "Hello, World!" -c "#f00,#ff0,#0f0" -j center
echo "streamed input" | rich-gradient print -
rich-gradient print text="Animated from env" -R -a -d 8
```

### `rule`

Draw a gradient or animated rule line, optionally with a title.

Options:

- `-t, --title TEXT`: Optional title shown in the rule.
- `-s, --title-style TEXT`: Rich style for the title (default: bold).
- `-j, --justify [left|center|right]`: Alignment for the title (default: center).
- `-c, --colors TEXT`: Comma-separated colour stops.
- `-R/ -n, --rainbow/--no-rainbow`: Toggle rainbow gradients.
- `-h, --hues INTEGER`: Number of hues for generated colour ramps (default: 7).
- `-T, --thickness INTEGER`: Line thickness between 0 and 3 (default: 1).
- `-a, --animated`: Animate the rule with Rich Live.
- `-d, --duration FLOAT`: Animation length in seconds (default: 5).

Examples:

```bash
rich-gradient rule -t "Section 1" -c green,yellow -T 2
rich-gradient rule -R -a -d 10
rich-gradient rule --title "Status" --title-style "bold italic cyan"
```

### `panel`

Produce a gradient panel around text or streamed content. Titles are aligned
with the `--justify` option and padding is configurable.

Arguments:

- `text`: panel content, `-` for stdin, or `text=...`.

Options:

- `-t, --title TEXT`: Optional panel title.
- `-s, --title-style TEXT`: Rich style for the panel title (default: bold).
- `-j, --justify [left|center|right]`: Title alignment (default: center).
- `-a, --align [left|center|right]`: Content alignment (default: left).
- `-c, --colors TEXT`: Comma-separated color stops.
- `-R/ -n, --rainbow/--no-rainbow`: Toggle rainbow gradients.
- `-h, --hues INTEGER`: Number of hues for generated gradients (default: 7).
- `-p, --padding TEXT`: Set padding as `N`, `V,H`, or `T,R,B,L`.
- `--expand / --no-expand`: Control width expansion (default: expand).
- `-a, --animated`: Animate the panel background.
- `-d, --duration FLOAT`: Animation length in seconds (default: 5).

Examples:

```bash
rich-gradient panel "Quick info" -t "Info" -c blue,cyan
printf "Markdown? *Yes!*\n" | rich-gradient panel -t "Stream" -R
rich-gradient panel -a -d 12 text="Animated background" -t "Live"
```

## Additional Features

- `-V, --version` prints the installed `rich-gradient` version and exits.
- All commands support `--help` for contextual usage.
- `--rainbow/--no-rainbow` flags allow quick toggling without clearing other
  options.
- When `--animated` is supplied, the CLI uses the appropriate animated class
  (`AnimatedGradient`, `AnimatedRule`, or `AnimatedPanel`) from the package.

With these commands you can script colourful terminal output, build demos, or
enhance dashboard tooling using the same gradient utilities available inside
the library.
