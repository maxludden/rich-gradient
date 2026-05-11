## Configuration

rich-gradient loads a small optional JSON configuration file. By default it
looks for:

```text
$HOME/.rich-gradient/config.json
```

Set `RICH_GRADIENT_HOME_DIR` to point at a different directory before import.
Tests and temporary environments can also call `rich_gradient.reload_config()`
with an explicit config path.

### Default bootstrap

If no file exists, rich-gradient uses its built-in defaults. A config file may
override those defaults with this shape:

```json
{
  "animate": true,
  "colors": {
    "red": "#FF0000",
    "tomato": "#FF5500",
    "orange": "#FF9900"
  }
}
```

- `animate` acts as the global kill-switch for animation. Setting the
  flag to `false` forces every animated helper (`AnimatedGradient`, `AnimatedPanel`,
  etc.) to start in static mode unless you explicitly pass `animate=True`.
- `colors` customises the named spectrum palette. Missing default colours are
  merged back in, so you can override only the entries you care about.

### Environment overrides

The loader also accepts environment overrides:

| Variable | Meaning |
| --- | --- |
| `RICH_GRADIENT_HOME_DIR` | Directory containing `config.json`. |
| `RICH_GRADIENT_ANIMATE` | `1`, `true`, `yes`, or `on` enables animation; any other value disables it. |
| `RICH_GRADIENT_COLORS` | JSON object merged into the named color palette. |
| `RICH_GRADIENT_EXE` | Preserved for compatibility with external wrappers; unused by the core library. |

### Format support

The current loader reads JSON only. TOML and YAML are not parsed by the core
library.
