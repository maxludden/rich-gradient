# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
