# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2022-11-23

### Added

- Environment variable defaults are now read from `$OUGHT_ICE_DIR/.env`.

### Fixed

- When running a recipe, the trace url is no longer printed with the wrong port.

## [0.3.0] - 2022-11-23

### Added

- When running a recipe, the trace server now starts automatically.

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
