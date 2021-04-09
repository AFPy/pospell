# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),

## [1.0.12] - 2021-04-10
### Fixed
- Support for docutils 0.17 thanks to mondeja and xi.

## [1.0.11] - 2020-10-14
### Fixed
- Better handling of FileNotFound, PermissionDenied, or IsADirectory errors.

## [1.0.10] - 2020-10-14
### Fixed
- Use `^` escape char on each line while invoking hunspell, avoiding
  it to think some line are comments.

## [1.0.9] - 2020-10-12
### Changed
- pospell now uses `hunspell -a` (was using `hunspell -l`), so
  hunspell can tell on which line an error is, instead of having
  pospell (wrongly) guess it.

## [1.0.8] - 2020-10-12
### Fixed
- Missing Sphinx option in hardcoded settings from 1.0.7.

## [1.0.7] - 2020-10-11
### Changed
- Hunspell is invoqued a single time.
- Avoid calling docutils.frontend.OptionParser, hardcode settings, saving lots of time.
- pospell is now twice faster on python-docs-fr.


## [1.0.6] - 2020-10-11
### Fixed
- Hunspell compounding mishandling caused some errors to be hidden by pospell.

## [1.0.5] - 2020-07-01
### Fixed
- Some errors were not reported due to [Hunspell not reporting them in
  Auto mode](https://github.com/hunspell/hunspell/issues/655).

## [1.0.4] - 2020-06-28
### Fixed
- Avoid glueing words together: "hello - world" was sent to hunspell as "helloworld".
- Don't pass placeholders like %s, %(foo)s, or {foo} to Hunspell.
- Don't pass Sphinx variables with underscores in them to Hunspell, like {days_since}.

## [1.0.3] - 2019-10-17
### Changed
- [Soft hyphens](https://en.wikipedia.org/wiki/Soft_hyphen) are now removed.

## [1.0.2] - 2019-10-16
### Fixed
- In POSIX.1, also drop the .1.

## [1.0.1] - 2019-10-16
### Fixed
- Drop prefixes while dropping accronyms, as in `non-HTTP`.
- Regression fixed while dropping plural form of accronyms like `PEPs`.
