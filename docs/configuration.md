## Configuration

rich-gradient automatically discovers a small configuration file that lives
alongside your shell environment. The loader recognises JSON, TOML, and YAML
documents, and searches the following paths in order:

1. `$HOME/.config/.rich-gradient`
2. `$HOME/local/bin/.rich-gradient`
3. `$HOME/.rich-gradient`

> **Note**  
> The first path that exists wins. A personalised file in
> `$HOME/.config/.rich-gradient.{json,toml,yaml}` overrides the default that is
> bootstrapped in `$HOME/.rich-gradient`.

### Default bootstrap

On first import, rich-gradient writes a default JSON document to
`$HOME/.rich-gradient` (or to the directory pointed at by
`RICH_GRADIENT_CONFIG_HOME` if the environment variable is set – handy for
tests and ephemeral environments). The file looks like this:

```json
{
  "executable_path": "/path/to/rich-gradient",
  "animation_enabled": true,
  "spectrum_colors": [
    "#FF0000",
    "#FF5500",
    "#FF9900",
    "... trimmed for brevity ..."
  ]
}
```

- `executable_path` records the CLI that should be invoked for helper tooling.
- `animation_enabled` acts as the global kill-switch for animation. Setting the
  flag to `false` forces every animated helper (`AnimatedGradient`, `AnimatedPanel`,
  etc.) to start in static mode unless you explicitly pass `animate=True`.
- `spectrum_colors` seeds the default colour palette and mirrors the manual
  values hard-coded inside `Spectrum`.

### Environment export

After the configuration is loaded, the following environment variables are
exported so that sub-processes and CLI wrappers can reuse the settings:

| Variable                          | Meaning                                         |
| -------------------------------- | ----------------------------------------------- |
| `RICH_GRADIENT_CONFIG_PATH`      | Absolute path to the file that was loaded.      |
| `RICH_GRADIENT_EXECUTABLE_PATH`  | Path stored in `executable_path`.               |
| `RICH_GRADIENT_ANIMATION_ENABLED`| `"1"` when animation is enabled, else `"0"`.    |
| `RICH_GRADIENT_SPECTRUM_COLORS`  | Comma separated list of configured colours.     |

### Format support

rich-gradient determines which parser to use from the file suffix:

| Suffix        | Parser                                        |
| ------------- | --------------------------------------------- |
| none / `.json`| Python `json` module                          |
| `.toml`       | `tomllib` (or `tomli` when installed)         |
| `.yaml`/`.yml`| PyYAML (install `pyyaml` to enable this)      |

If you prefer YAML or TOML, create one of the supported files in
`$HOME/.config/` or `$HOME/local/bin/` and rich-gradient will pick it up on the
next import. The bootstrapped JSON in `$HOME/.rich-gradient` acts as a safe
fallback and is never overwritten once created.
