# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--## [Unreleased]-->


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
