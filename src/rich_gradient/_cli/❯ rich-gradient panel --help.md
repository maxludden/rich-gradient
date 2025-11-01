---
title: "rich-gradient panel --help"
slug: "rich-gradient-panel-help"
tags:
  - cli
  - rich-gradient
  - help
  - panel
---

# rich-gradient Panel Help

## Usage

```shell
Usage: rich-gradient panel [OPTIONS] [TEXT]
```

Display the line above in the follow markup:

```python
f"Usage: [bold gradient]rich-gradient[/bold gradient] [bold white]panel[/bold white] [i #ccc][[/i #ccc][i #ff0]OPTIONS[/i #ff0][i #ccc]][/i #ccc] [i #ccc][TEXT][/i #ccc]"
```

```html
<f"Usage: <span style='background: linear-gradient(to right, #ff7e5f, #feb47b); -webkit-background-clip: text; color: transparent;'>rich-gradient</span> <span style='font-weight: bold; color: white;'>panel</span> <span style='font-style: italic; color: #ccc;'>[</span><span style='font-style: italic; color: #ff0;'>OPTIONS</span><span style='font-style: italic; color: #ccc;'>]</span> <span style='font-style: italic; color: #ccc;'>[TEXT]</span>"
```

## Structure of Help Panels

```shell

❯ rich-gradient panel --help

 Usage: rich-gradient panel [OPTIONS] [TEXT]

 Display text inside a gradient panel

╭─ Arguments ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│        text                                   [TEXT]                   The text to display inside the panel or '-' for stdin                                                  │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Color Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ -c   --colors                                 TEXT                     Comma-separated list of colors for the gradient (e.g., `red,#ff9900,yellow`)                           │
│ -r   --rainbow           -R   --no-rainbow                             Use rainbow colors for the gradient. Overrides -c/--colors if set. [default: R]                        │
│ -h   --hues                                   INTEGER                  Number of hues for rainbow gradient [default: 7]                                                       │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Title Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ -t   --title                                  TEXT                     Title of the panel                                                                                     │
│      --title-style                            TEXT                     Style of the panel title text (requires -t/--title) [default: bold]                                    │
│      --title-align                            [left|center|right]      Alignment of the panel title (requires -t/--title) [default: center]                                   │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Panel Inner Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ -p   --padding                                TEXT                     Padding inside the panel (1, 2, or 4 comma-separated integers).                                        │
│ -J   --text-justify                           TEXT                     Justification of the panel inner text [default: left]                                                  │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Panel Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ -j   --justify                                TEXT                     Justification of the panel itself [default: left]                                                      │
│ -e   --expand            -E   --no-expand                              Whether to expand the panel to fill the width of the console [default: expand]                         │
│ -w   --width                                  INTEGER                  Width of the panel. (requires -E/--no-expand)                                                          │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Panel Subtitle Options ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ -s   --subtitle                               TEXT                     Subtitle of the panel                                                                                  │
│      --subtitle-style                         TEXT                     Style of the panel subtitle text (requires -S/--subtitle)                                              │
│      --subtitle-align                         [left|center|right]      Alignment of the panel subtitle (requires -S/--subtitle) [default: right]                              │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Panel Animation Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ -a   --animated                                                        Animate the gradient panel.                                                                            │
│ -d   --duration                               FLOAT                    Length of the animation in seconds (requires --animated). [default: 10.0]                              │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│      --help                                                            Show this message and exit.                                                                            │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

```
