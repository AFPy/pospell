# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),


## [Unreleased]

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
