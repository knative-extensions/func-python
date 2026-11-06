# Changelog

All notable changes to this project should be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Automatically raise the soft `RLIMIT_NOFILE` to the hard limit at
  `serve()` startup, matching Go and Java runtime behaviour. Finite hard
  limits are honoured in full; when the hard limit is `RLIM_INFINITY` the
  soft limit is capped at 65536 to stay within kernel constraints.
  Failures are logged as warnings and never fatal (knative/func#3513).

### Changed
### Deprecated
### Removed
### Fixed
### Security

## 0.8.1 - 2026-04-14

### Fixed

- Set SO_REUSEADDR on pre-bound sockets to prevent bind failures on restart

## 0.8.0 - 2026-04-13

### Changed

- Bumping cloudevents dep to 2.0

## 0.7.0 - 2025-11-19

### Added

- Support for IPv4-only environments

## 0.6.1 - 2025-08-27

### Changed

- Improved test function to cover additional CloudEvent cases

### Fixed

- CloudEvent handler gracefully fails on non-cloudevent requests

## [0.5.1] - 2025-03-10

### Changed

- Choose python version compatible with S2I

### Fixed

- Fixed CloudEvent raw http send (missing await)

## [0.4.2] - 2025-03-02

- CloudEvent Middleware
- Deployment and Release Automation Updates

## [0.3.0] - 2025-02-10

### Added

- Instanced handlers now support OnStop events

### Changed

- Simplified instanced functions by expecting a named 'handle' method.
- Tests support specifying test service listen address

## [0.2.0] - 2024-11-06

### Added

- optional message returns from lifeycle methods "alive" and "ready"
- expanded development and release documentation

## [0.1.0] - 2024-10-28

### Added

- Initial Implementation of the Python HTTP Functions Middleware


