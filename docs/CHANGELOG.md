# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]



### v0.3.11 - 2026-02-10 | <span style="color: rgb(215, 255, 100)">Highlight configs, CLI refactor, Gradient/Rule fixes</span>

#### Added / Changed

- Added explicit highlight configuration helpers (`HighlightWords`, `HighlightRegex`) and updated `Gradient` to accept the new highlight inputs.
- Refactored CLI command structure and removed deprecated CLI command modules/files.
- Improved documentation and examples to cover the new highlighting workflow.
- Added `GradientTheme` tests and tightened gradient test coverage (including single background color handling).
- See [rich-gradient-cli](https://github.com/maxludden/rich-gradient-cli) for the new CLI implementation.

#### Fixed

- Improved Gradient color parsing and handling of highlight inputs.
- Corrected Rule thickness/character mapping behavior.
- Streamlined Text background color parsing and ensured theme initialization is consistent.

### v0.3.10 - 2026-01-04 | <span style="color: rgb(215, 255, 100)">AnimatedText, CLI defaults, Live persistence</span>

#### Added / Changed

- Added `AnimatedText` for live gradient `rich.text.Text`, plus `update_text` helpers, package export, reference docs, and an example script.
- AnimatedGradient family (`AnimatedGradient`, `AnimatedPanel`, `AnimatedMarkdown`, `AnimatedRule`) no longer clears the console on stop; unless `transient=True`, the final gradient render persists.
- CLI defaults to the `print` command when no subcommand is provided and can read input from stdin.
  - For example:

    <code>echo "Hello, World!" | rich-gradient</code>

   - Docs refreshed to note the behavior.
- Animation/text guides and the mkdocs navigation now include AnimatedText coverage.
- Added tests for AnimatedText behavior and CLI default/stdin handling.

#### Fixed

- Silenced `rich-color-ext` `get_css_map` type checker mismatch for older releases.

### v0.3.9 - 2025-12-15 | <span style="color: rgb(215, 255, 100)">CLI doc refresh, import/test stability, CSS fix</span>

#### Added / Changed

- CLI docs and README now describe the Click + rich-click subcommands (`print`, `panel`, `rule`, `markdown`) with current options and examples; removed stale Typer references.
- CLI option help text across commands uses the rich markup formatting introduced in `text_command.py` for consistent help output.
- Contributor note documents that `pytest` runs without an editable install because `tests/conftest.py` adds `src/` to `sys.path`.
- Documentation CSS now anchors `html, body` to the theme background to avoid a black flash/transparent top before styles load.

#### Fixed

- Test collection no longer fails with `ModuleNotFoundError: rich_gradient` when the package isn't installed editable, thanks to the path shim in `tests/conftest.py`.

### v0.3.7 - 2025-10-24 |  <span style="color: rgb(215, 255, 100)">Documentation refresh, reproducible assets & CLI polish</span>

#### Added

- Docs
    - New user-guide pages for panels, the CLI, and animation (`docs/panel.md`, `docs/cli.md`, `docs/animation.md`) linked from the main navigation.
    - API reference stubs for `AnimatedPanel` and `Panel` via `mkdocstrings`.
    - Hero quick-start, palette, background, panel, rule, spectrum, and CLI images generated from checked-in example scripts.
- Examples
    - Added reproducible scripts under `examples/` to render all user-guide screenshots, including quick-start `Text`, palette variations, background gradients, gradient/table showcases, panel gallery, rule gallery, spectrum table, CLI help, and updated `hello_world.py`.

#### Changed

- Docs
    - Rewrote the landing page plus Text, Gradient, Rule, and Spectrum guides for clearer positioning and accurate option coverage.
    - Updated index code snippets to import `Text` from the package root and refreshed installation guidance.
    - Refined `docs/animated_gradient_ref.md` to point at the public module path.
    - Regenerated SVG/GIF assets with consistent naming (e.g., `hello_world.svg`, `text-quickstart.svg`, `gradient-panel.svg`, `cli-help.svg`) and removed legacy images.
- Library
    - Exported `Text` from `rich_gradient/__init__.py` so examples, docs, and the CLI can rely on the top-level import.
- Tooling
    - Expanded `mkdocs.yml` navigation to surface the new pages and verified the build with `uv run mkdocs build`.

#### Removed

- Docs
    - Dropped the obsolete `base_gradient_ref.md` page and deprecated image assets that the refreshed guides no longer reference.

### v0.3.6 - 2025-09-10 |  <span style="color: rgb(215, 255, 100)">Consolidated Gradient, RNG fix, gamma-correct Text, docs/tests</span>

#### Added / Changed

- Gradient
    - Consolidated to a single public factory (`rich_gradient.gradient.Gradient`) that returns `BaseGradient` or `AnimatedGradient` internally.
    - Kept test helper methods by adding equivalents to `BaseGradient` (`_color_at`, `_styled`, `_interpolated_color`) and `_active_stops` initialization.
    - Added `background=` support to `BaseGradient`/`AnimatedGradient` for parity with previous API.
- Text
    - Interpolates colors with gamma-correct blending for visual consistency with `Gradient`.
- Spectrum
    - Uses a dedicated `random.Random(seed)` instance to avoid mutating global RNG state; behavior is deterministic per seed without side effects.
- Rule
    - Normalized invalid color errors to `ValueError` for consistency.
- Package Init
    - Centralized `rich-color-ext` install to package init; removed duplicate installs from other modules.
- Repo Hygiene
    - Removed committed build artifacts (`dist/`) and static site (`site/`) from source; they remain in `.gitignore`.
- Docs / Examples / Tests
    - README basic example fixed (missing parenthesis).
    - Benchmark test now measures actual console printing safely.
- CLI
    - Relaxed `--justify` and `--overflow` option annotations from `Literal[...]` to `str` with explicit validation for broader Typer/Click compatibility.
    - Pinned dependencies to stabilize CLI behavior: `typer>=0.12.5,<0.13` and `click>=8.1.7,<9.0.0`.
- Tests
    - Made CLI tests portable across Click/Typer versions by removing `mix_stderr` usage and accepting warnings from stdout or stderr.
- Cleanup
    - Removed duplicate internal `Gradient` factory leftover in `_animated_gradient.py`; the public factory now lives in `rich_gradient/gradient.py`.
- Docs
    - Added _base_gradient_ref.md for referencing BaseGradient
    - Added _animated_gradient_ref.md for referencing AnimatedGradient


#### Fixed

- Eliminated duplicate Gradient implementations that could drift out of sync.
- Avoided global RNG seeding in `Spectrum` that could affect host applications.


### v0.3.4 - 2025-09-03 | <span style="color: rgb(215, 255, 100)">Text.as_rich(), background gradients, spectrum + docs</span>

#### v0.3.4 Added

- Text
  - `.as_rich()` method to return a plain `rich.text.Text` with all spans/styles preserved.
  - `.rich` convenience property wrapping `as_rich()`.
  - Background gradients via `bgcolors=`; multiple bg stops interpolate alongside foreground.
  - Robust color normalization supporting `Color`, `ColorTriplet`, `(r,g,b)` tuples, CSS names, 3/6‑digit hex, and `rgb()` strings.
- Spectrum
  - Deterministic `seed`, color names, styles, hex accessors, and a rich preview table renderable.
- Docs/Examples
  - New SVG/PNG assets for gradient text examples under `docs/img/v0.3.4/` and updated spectrum preview.

#### v0.3.4 Updated

- Text
  - Improved error types/messages and comprehensive module documentation.
  - Single‑color fast‑path applies one composed `Style` across content for performance.
  - Empty text rendering no longer emits a trailing newline/segment; nested renderables filtered accordingly.
- Gradient and BaseGradient
  - Gamma‑corrected color interpolation, smoother stop wrapping, explicit alignment validation, and safer measurement when no renderables.
  - Support for `repeat_scale`/`phase` used by animated variants.
- Rule
  - Accepts colors as strings, `Color`, `ColorTriplet`, or RGB tuples with clearer validation and messages.
  - Title style applied after gradient generation for accurate highlighting.
- Package Init / Theme
  - Install `rich-color-ext` on import and monkey‑patch `Console._collect_renderables` to suppress empty `Text` trailing newline.
  - Theme helpers for consistent docs SVG generation (`GRADIENT_TERMINAL_THEME`).
- README/Docs
  - Expanded examples and color‑format visuals; refreshed links and images.

#### v0.3.4 Fixed

- Suppressed stray newline output when rendering empty gradient `Text` (affects console capture/recorded SVGs).

### v0.3.3 - 2025-08-27 | <span style="color: rgb(215, 255, 100)"> Added tests and Fixed Bugs</span>

#### v0.3.3 Updated

- Enhanced rendering and color handling in gradient components
- Refactored rich-gradient for improved structure and functionality
  - Reorganized imports in `__init__.py` for clarity.
  - Updated AnimatedGradient to ensure color extension is installed at package import time.
  - Enhanced BaseGradient to improve gradient wrapping logic and error handling.
  - Improved logger utility with better error handling and configuration options.
  - Adjusted Gradient class to ensure quit panel behavior is consistent and intuitive.
  - Added comprehensive tests for edge cases in Gradient and Text classes, including long text, unicode handling, and color validation.
  - Enhanced Spectrum class to support color generation with optional seed for reproducibility.
  - Improved Text class to ensure proper initialization and color parsing.
  - Updated test suites for Gradient and Spectrum to cover additional scenarios and edge cases.

### v0.3.2 <span style="color: rgb(215, 255, 100)"> Added tests and Fixed Bugs</span>

#### v0.3.2 Removed

- Dev Dependencies
  - `snoop`
  - `cheap-repr`

#### v0.3.2 Updated

- Removed instances that were imported from:
  - `snoop`
    - `@snoop()`
  - `cheap-repr`
    - `register_repr(f"{class})(normal_repr)`
- Renamed GradientRule -> Rule
  -  to match the naming of the other modules in `rich-gradient`

#### v0.3.2 Added

- Tests
  - `tests/benchmark_perf.py`: To benchmark the performance of generating gradients that span large amounts of characters.
  - `tests/test_edge_cases.py`: To cover edge cases that may otherwise break `rich-gradient`.


### v0.3.0 - 2025-06-20 | <span style="color: rgb(215, 255, 100)"> Working Rewrite</span>

#### <span style="color: rgb(215, 255, 100)">v0.3.0 Added</span>

- Validated working and added tests for:
  - `rich_gradient.text.Text`
  - `rich_gradient.gradient.Gradient`
  - `rich_gradient.rule.GradientRule`
  - `rich_gradient.spectrum.Spectrum`
  - `rich-color-ext` acting as adequate replacement for previous color logic
- Added examples directory containing:
  - `animated_gradient_example.py`
  - `gradient_example.py`
  - `hello_world.py`
  - `rainbow_gradient.py`
  - `specific_color_gradient.py`
  - `text_markup.py`
  - `two_color_gradients.py`
- Generated updated exports for examples for documentation (still in the works)

#### <span style="color: rgb(215, 255, 100)">v0.3.0 Updated</span>

- `docs/index.md`

#### <span style="color: rgb(215, 255, 100)">v0.3.0 TODO</span>

- Update Documentation
- Expand Tests
- Work on Gradient Panel and Table Renderables

#### <span style="color: rgb(215, 255, 100)">v0.3.0 Removed</span>

Removed all of the the archived modules from rich_gradient/archive/*

### v0.2.1 <span style="color: rgb(215, 255, 100)">Rewrite</span>

There was a lot of overhead in rich-gradient so I rewrote it from the ground up with an actual goal. I created [rich-color-ext](https://github.com/maxludden/rich-color-ext) to wrap around rich's color parsing removing the need for the` _rgb.py`, `color.py`, `color_data.py`, `_colors.py`, and all of their tests.

### v0.2.0 - 2025-3-13 | <span style="color:rgb(215, 255, 100)">[uv](https://github.com/astral-sh/uv)</span>, pure python, and 3.13.2

There are a number of significant changes in v0.2.0:

#### <span style="color: rgb(215, 255, 100)">`rye` → `uv`</span>

Astral has done a hell of a job making python dev tools. [ruff](https://github.com/astral-sh/ruff) blew the existing python linters out of the water and uv pretty much did the same thing to package managers. Rich-gradient was started on [rye](https://github.com/astral-sh/rye) but as Astral has since depreciated it, it's moved to their current rust powered python package manager, [uv](https://github.com/astral-sh/uv).

#### <span style="color: rgb(215, 255, 100)">Pure Python</span>

Rich-gradient is now a pure-python package. This allows it to be more easily used regardless of platform. As rich-gradient previously had pydantic as a dependency, it now just borrows the logic from [`pydantic-extra-types.color`](https://github.com/pydantic/pydantic-extra-types/blob/889319b7825331c18cedd16b80a09c2).

#### <span style="color: rgb(215, 255, 100)">3.13.2</span>

After switching to [uv](https://github.com/astral-sh/uv), the package has been updated to python 3.13.2.

### v0.2.0 Updated

- Switched rich-gradient package manager from [astral/rye](https://github.com/astral-sh/rye) to [astral/uv](https://github.com/astral-sh/uv)
- Updated python to `3.13.2`

### v0.2.0 Changed

- Removed [`pydantic`](https://github.com/pydantic/pydantic) and [`pydantic-extra-types`](https://github.com/pydantic/pydantic-extra-types) dependencies.
- Updated the names of some of the colors. For example <span style="color: #7CFF00">greenyellow</span> became <span style="color: #7CFF00">lawngreen</span>.
- Updated `README.md`, `CHANGELOG`, and documentation.

### v0.2.0 Added

- `src/rich_gradient/_base_color.py`: stores the color logic from pydantic-extra-types.color modules stripped of the pydantic framwork.

## v0.1.7 - 2024-7-16 | Added support for Two-Color Gradients

### v0.1.7 Updated

- Updated Gradient.generate_subgradients() to default to returning a list containing a single simple gradient to allow
Gradients to work when only supplied with two colors.

![Two Color Gradient](https://raw.githubusercontent.com/maxludden/rich-gradient/3b6e2cb013eda3bcba9dbcdd14c65179d28532da/docs/img/simple_gradient_example.svg)

### v0.1.7 Added

- Added len, int, str, and repr dunder methods to `rich-gradient.gradient.Gradient` (will simply refer to as `Gradient` from here on out).
- Added a tests/test_gradient.py for Gradient to test two color gradiets

## v0.1.6 - 2024-6-28 | Updated Rev

- Updated rev to 0.1.6.

## v0.1.5 - 2024-6-28 | Added Tests

### v0.1.5 Updated

- Updated requirements for minimum versions of python from 3.8 -> 3.10.
- Added `pytest` to dev-dependancies.

### v0.1.5 Added

- Tests for:
  - Color
  - Specturm
  - SimpleGradient

## v0.1.4 | 2024-6-28 | Resolved Dependancies

### v0.1.4 Updated

- This release is primarily to prune unnecessary dependancies.
- Removed `numpy` to avoid issues of `numpy` version 2.0.0 conflicting with `torch`.

## v0.1.3 - 2021-10-10

### v0.1.3 Fixed

- Updated README to use GitHub pages for example gradient image.

## v0.1.2 - 2021-10-10

### v0.1.2 Updated

- Updated PyProject.toml description.
- Moved MKDocs and related dependancies to dev-dependancies.

### v0.1.2 Fixed

- Updated README to use GitHub pages for banner image.
- Updated README to use GitHub pages for docs url.

## v0.1.1 - 2021-10-10

### v0.1.1 Fixed

- Updated README to use GitHub pages for images.

## v0.1.0 - 2021-10-10

Initial release. Based off of MaxGradient with a simplified color model based on pydantic-extra-types.color.Color. Re-released as rich-gradient to avoid confusion with MaxGradient.
