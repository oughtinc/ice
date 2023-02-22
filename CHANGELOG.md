# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2023-02-22

### Added

- Secrets are now optional. Any secrets needed to run a recipe will be prompted for
  and stored in `$OUGHT_ICE_DIR/.env`.
- ICE now supports Python 3.9 and 3.11.

## [0.4.0] - 2022-12-27

### Added

- [Toolbar to highlight all call nodes of a specific function/method](https://github.com/oughtinc/ice/wiki/ICE-UI-guide#highlighting-functions), expand their ancestors to reveal them, and hide other irrelevant nodes.
- [Integration](https://github.com/oughtinc/ice/wiki/ICE-UI-guide#transparent-f-strings-using-fvalues) with the new [fvalues](https://github.com/oughtinc/fvalues) library, highlighting dynamic parts of formatted strings in the detail pane.
- Show the total cost of OpenAI API calls in each call node, assuming a price of $0.02 per 1000 tokens.
- When running a recipe:
  - Automatically start the server in a background process if it's not already running. This can be disabled by setting the environment variable `OUGHT_ICE_AUTO_SERVER=0`. Run `python -m ice.server stop` to kill the process.
  - Automatically open the recipe in the browser. This can be disabled by setting the environment variable `OUGHT_ICE_AUTO_BROWSER=0`.
  - Log the URL instead of printing it.
- Environment variables `OUGHT_ICE_HOST` and `OUGHT_ICE_PORT` to configure the server host and port.

### Changed

- **Breaking trace file format change:** Traces are now stored in a directory with multiple files instead of one large file. This makes loading large traces in the UI much more efficient. Old trace files can no longer be loaded.
- Instances of dataclasses are serialized as JSON objects instead of strings using `dataclasses.asdict` so they have a readable structure in the detail pane.

### Fixed

- Fixed SQLite connection error which sometimes occurred when running async functions decorated with `@diskcache`.
- Replaced hardcoded `/code/papers/` path (which only made sense in the old docker container) with environment variable `PAPER_DIR`.
- Added empty `py.typed` file to the package for type checkers.

## [0.3.2] - 2022-11-28

### Fixed

Added missing `python_requires` to PyPI package.

## [0.3.1] - 2022-11-23

### Added

- Environment variable defaults are now read from `$OUGHT_ICE_DIR/.env`.

### Fixed

- When running a recipe, the trace url is no longer printed with the wrong port.

## [0.3.0] - 2022-11-23

### Added

- Allow running the trace server using `python -m ice.server`.

### Changed

- **Breaking change**: ICE no longer uses Docker.
- **Breaking change**: Python package dependencies are now listed in `setup.cfg`.
- **Breaking change**: ICE data is now stored in `~/.ought-ice` by default. This can be customized by setting the `OUGHT_ICE_DIR` environment variable.

### Removed

- **Breaking change**: Removed most of `scripts/`.

## [0.2.0] - 2022-10-07

### Added

- Added multi-format utilities to aid in prompt building.
- Added an extension mechanism: `ice/ice/contrib/`. Ask on Slack for details, or stay tuned for docs.
- Added a Python API server. In the future, this will be used for a prompt playground.

### Changed

- **Breaking change:** `Agent.answer()` has been replaced with `Agent.complete()`.

## [0.1.1] - 2022-10-04

### Changed

- Improved the design of the trace detail pane.

### Fixed

- Fixed a startup error for some users.
- Fixed how lines are rendered in the trace tree pane.

## [0.1.0] - 2022-09-28

### Added

- Initial release.
