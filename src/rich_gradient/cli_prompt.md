I would like you to create a new Typer CLI for rich-gradient. It must be able to parse basic
flags like: version and help. It should also print help panels similar to the rich-cli help
panels but use rich-gradient panels instead of rich panels.

# Commands

## `print`

Print text in gradient color to a rich console that is able to accept markup.

### Print Arguments

- `text`: The text to print in gradient color.

### Print 2Options

- colors:
  - '-c', '--colors',
  - metavar='COLORS'
  - help='parse a comma separated string of colors'
  - type=str
  - parses a string like 'red,#ff9900,yellow' into a list of colors.
- rainbow:
  - '-r', '--rainbow',
  - help='print text in rainbow colors'
  - is_flag=True
  - default=False
  - overrides colors if set.
- hues:
  - '-h', '--hues',
  - metavar='HUES'
  - help='The number of hues to use for a random gradient'
  - type=int
  - default=7
- style:
  - '--style',
  - metavar='STYLE'
  - help='The style to apply to the text'
  - type=str
  - default=None
- justify:
  - '-j', '--justify',
  - metavar='JUSTIFY'
  - help='Justification of the text'
  - default='left'
  - choices=['left', 'center', 'right']
  - type=str
- overflow:
  - '--overflow',
  - metavar='OVERFLOW'
  - help='How to handle overflow of text'
  - default='fold'
  - choices=['crop', 'fold', 'ellipsis']
  - type=str
- no_wrap:
  - '--no-wrap',
  - help='Disable wrapping of text',
  - is_flag=True
  - default=False
- end:
  - '--end',
  - metavar='END'
  - help='String appended after the text is printed'
  - default='\n'
  - type=str
- bgcolors:
  - '--bgcolors',
  - metavar='BGCOLORS'
  - help='parse a comma separated string of background colors'
  - type=str
  - parses a string like 'red,#ff9900,yellow' into a list of background colors.
  - default=None
- animate:
  - '--animate',
  - help='Animate the gradient text'
  - is_flag=True
  - default=False
  - if set, the text will animate.
- duration:
  - '-d', '--duration',
  - metavar='DURATION'
  - help='Duration of the animation in seconds'
  - type=float
  - default=5.0
  - only used if animate is set.

## `panel`

Display text inside a gradient panel.

### Panel Arguments

- `renderable`: The renderable to display inside the panel or '-' for stdin.

### Panel Options

- colors:
  - '-c', '--colors',
  - metavar='COLORS'
  - help='Comma-separated list of colors for the gradient (e.g., `red,#ff9900,yellow`)'
  - type=str
- bgcolors:
  - '--bgcolors',
  - metavar='BGCOLORS'
  - help='Comma-separated list of background colors for the gradient (e.g., `red,#ff9900,yellow`)'
  - type=str
  - default=None
  - if set applies background gradient to the panel
  - if a single color is provided it is used as the background color for the panel.
- rainbow:
  - '-r', '--rainbow',
  - help='Use rainbow colors for the gradient. Overrides -c/--colors if set.'
  - is_flag=True
  - default=False
  - overrides colors if set.
- hues:
  - '--hues',
  - metavar='HUES'
  - help='Number of hues for rainbow gradient'
  - type=int
  - default=5
- title:
  - '-t', '--title',
  - metavar='TITLE'
  - help='Title of the panel'
  - type=str
- title_style:
  - '--title-style',
  - metavar='TITLE_STYLE'
  - help='Style of the panel title text (requires -t/--title)'
  - type=str
  - default='bold'
  - requires title if set.
- title_align:
  - '--title-align',
  - metavar='TITLE_ALIGN'
  - help='Alignment of the panel title (requires -t/--title)'
  - type=str
  - choices=['left', 'center', 'right']
  - default='center'
  - requires title if set.
- subtitle:
  - '--subtitle',
  - metavar='SUBTITLE'
  - help='Subtitle of the panel'
  - type=str
- subtitle_style:
  - '--subtitle-style',
  - metavar='SUBTITLE_STYLE'
  - help='Style of the panel subtitle text (requires -s/--subtitle)'
  - type=str
  - default=None
  - requires subtitle if set.
- subtitle_align:
  - '--subtitle-align',
  - metavar='SUBTITLE_ALIGN'
  - help='Alignment of the panel subtitle (requires -s/--subtitle)'
  - type=str
  - choices=['left', 'center', 'right']
  - default='right'
  - requires subtitle if set.
- style:
  - '--style',
  - metavar='STYLE'
  - help='The style to apply to the panel'
  - type=str
  - default=None
- border_style:
  - '--border-style',
  - metavar='BORDER_STYLE'
  - help='The style to apply to the panel border'
  - type=str
  - default=None
- padding:
  - '-p', '--padding',
  - metavar='PADDING'
  - help='Padding inside the panel (1, 2, or 4 comma-separated integers).'
  - type=tuple of ints
- vertical_justify:
  - '-V', '--vertical-justify',
  - metavar='VERTICAL_JUSTIFY'
  - help='Vertical justification of the panel inner text'
  - type=str
  - choices=['top', 'middle', 'bottom']
  - default='top'
- text_justify:
  - '-J','--text-justify',
  - metavar='TEXT_JUSTIFY'
  - help='Justification of the text inside the panel'
  - type=str
  - choices=['left', 'center', 'right']
  - default='left'
- justify:
  - '-j', '--justify',
  - metavar='JUSTIFY'
  - help='Justification of the panel itself'
  - type=str
  - choices=['left', 'center', 'right']
  - default='left'
- expand:
  - '-e/-E', '--expand/--no-expand',
  - help='Whether to expand the panel to fill the width of the console'
  - is_flag=True
  - default=True
- width:
  - '--width',
  - metavar='WIDTH'
  - help='Width of the panel. (requires -E/--no-expand)'
  - type=int
  - requires expand to be False if set.
  - default=None
- height:
  - '--height',
  - metavar='HEIGHT'
  - help='Height of the panel. If not set, height is determined by content.'
  - type=int
  - default=None
- end:
  - '--end',
  - metavar='END'
  - help='String appended after the panel is printed'
  - default='\n'
  - type=str
- box:
  - '--box',
  - metavar='BOX'
  - help='Box style for the panel border'
  - type=str
  - choices=['SQUARE', 'ROUNDED', 'HEAVY', 'DOUBLE', 'ASCII']
  - default='ROUNDED'
- animate:
  - '--animate',
  - help='Animate the panel gradient'
  - is_flag=True
  - default=False
  - if set, the panel gradient will animate.
- duration:
  - '-d', '--duration',
  - metavar='DURATION'
  - help='Duration of the panel animation in seconds'
  - type=float
  - default=5.0
  - only used if animate is set.

## `rule`

Display a gradient rule in the console.

### Rule Options

- title:
  - '-t', '--title',
  - metavar='TITLE'
  - help='Title of the rule'
  - type=str
- title_style:
  - '-s' '--title-style',
  - metavar='TITLE_STYLE'
  - help='The style of the rule's title'
  - type=str
  - default=None
- colors:
  - '-c', '--colors',
  - metavar='COLORS'
  - help='Comma-separated list of colors for the gradient (e.g., `red,#ff9900,yellow`)'
  - type=str
- bgcolors:
  - '--bgcolors',
  - metavar='BGCOLORS'
  - help='Comma-separated list of background colors for the gradient (e.g., `red,#ff9900,yellow`)'
  - type=str
  - default=None
    - if set applies background gradient to the rule
    - if a single color is provided it is used as the background color for the rule.
- rainbow:
  - '-r', '--rainbow',
  - help='Use rainbow colors for the gradient. Overrides -c/--colors if set.'
  - is_flag=True
  - default=False
  - overrides colors if set.
- hues:
  - '--hues',
  - metavar='HUES'
  - help='Number of hues for rainbow gradient'
  - type=int
  - default=10
- end:
  - '--end',
  - metavar='END'
  - help='String appended after the rule is printed'
  - default='\n'
  - type=str
- thickness:
  - '-T', '--thickness',
  - metavar='THICKNESS'
  - help='Thickness of the rule line'
  - type=int
  - default=2
  - choices=[0, 1, 2, 3]
- align:
  - '-a', '--align',
  - metavar='ALIGN'
  - help='Alignment of the rule in the console'
  - type=str
  - choices=['left', 'center', 'right']
  - default='center'
- animate:
  - '--animate',
  - help='Animate the panel gradient'
  - is_flag=True
  - default=False
  - if set, the panel gradient will animate.
- duration:
  - '-d', '--duration',
  - metavar='DURATION'
  - help='Duration of the panel animation in seconds'
  - type=float
  - default=5.0
  - only used if animate is set.

## Markdown

Render markdown text with gradient colors in a rich console.

### Markdown Arguments

- `markdown`: The markdown text to render with gradient colors or Path of a markdown file.

### Markdown Options

- colors:
  - '-c', '--colors',
  - metavar='COLORS'
  - help='Comma-separated list of colors for the gradient (e.g., `red,#ff9900,yellow`)'
  - type=str
- bgcolors:
  - '--bgcolors',
  - metavar='BGCOLORS'
  - help='Comma-separated list of background colors for the gradient (e.g., `red,#ff9900,yellow`)'
  - type=str
  - default=None
  - if set applies background gradient to the markdown text
- rainbow:
  - '-r', '--rainbow',
  - help='Use rainbow colors for the gradient. Overrides -c/--colors if set.'
  - is_flag=True
  - default=False
  - overrides colors if set.
- hues:
  - '--hues',
  - metavar='HUES'
  - help='Number of hues for rainbow gradient'
  - type=int
  - default=7
- style:
  - '--style',
  - metavar='STYLE'
  - help='The style to apply to the markdown text'
  - type=str
  - default=None
- justify:
  - '-j', '--justify',
  - metavar='JUSTIFY'
  - help='Justification of the markdown text'
  - type=str
  - choices=['left', 'center', 'right']
  - default='left'
- overflow:
  - '--overflow',
  - metavar='OVERFLOW'
  - help='How to handle overflow of markdown text'
  - default='fold'
  - choices=['crop', 'fold', 'ellipsis']
  - type=str
- no_wrap:
  - '--no-wrap',
  - help='Disable wrapping of markdown text',
  - is_flag=True
  - default=False
- end:
  - '--end',
  - metavar='END'
  - help='String appended after the markdown text is printed'
  - default='\n'
  - type=str
- animate:
  - '--animate',
  - help='Animate the gradient markdown text'
  - is_flag=True
  - default=False
  - if set, the markdown text will animate.
- duration:
  - '-d', '--duration',
  - metavar='DURATION'
  - help='Duration of the animation in seconds'
  - type=float
  - default=5.0
  - only used if animate is set.
