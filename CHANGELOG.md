# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.5-pre8] - 2026-05-13

### Added
- Comprehensive documentation with Chinese (README_CN.md) and English (README.md) versions
- CONTRIBUTING.md guide for contributors
- CODE_OF_CONDUCT.md for community guidelines
- Improved README with 30+ badges for project status
- Added sections for Contributors, Star History, and Acknowledgments
- Enhanced API documentation and examples
- 933+ comprehensive tests covering all features
- Dependency tree analysis feature
- Performance benchmarking feature

### Fixed
- Symbol index not building automatically on startup
- Fixed background thread construction of symbol index
- Improved symbol search and discovery
- Added file-based caching persistence

### Updated
- Main README with comprehensive features and usage
- Added many new examples and use cases
- Enhanced configuration documentation
- Improved troubleshooting guide
- Added multi-language support

## [0.0.5-pre7] - 2026-05-12

### Added
- Improved type hints for better IDE support
- Enhanced error handling for module resolution
- More comprehensive test coverage

### Fixed
- Minor bugs in alias registration
- Performance improvements in symbol lookup

## [0.0.4] - 2026-05-10

### Added
- Background index building for faster startup
- Symbol sharding for large packages
- Symbol location finder with `lz.which()`
- Interactive help system with `lz.help()`
- Jupyter magics support with `%lazy` and `%%lazy`
- User configuration file support (~/.laziestrc)
- Generic type hints support
- Dependency pre-analysis feature
- Import profiler for performance monitoring
- Environment detection for venv/conda/virtualenv
- Conflict visualization for symbols
- Persistent preferences system

### Enhanced
- Lazy loading function performance
- Multi-level cache architecture
- Overall documentation

## [0.0.3] - 2026-05-08

### Added
- Typo correction with Levenshtein distance
- Abbreviation expansion for common packages
- Symbol search across modules
- Auto-install feature
- File-based caching
- 1000+ predefined aliases

### Fixed
- Module resolution issues
- Performance improvements

## [0.0.2] - 2026-05-05

### Added
- Lazy proxy functionality
- Submodule support
- Cache persistence
- More comprehensive test coverage

### Enhanced
- Lazy module proxy implementation
- Overall performance

## [0.0.1] - 2026-05-01

### Added
- Initial release
- Basic lazy loading functionality
- Wildcard import support
- Namespace prefix support
- 100+ predefined aliases
- Basic testing

---

## Unreleased

### Planned
- More predefined aliases
- Better IDE integration
- Additional documentation
- Performance improvements
- More examples and tutorials

[0.0.5-pre8]: https://github.com/ChidcGithub/Laziest-import/compare/v0.0.5-pre7...v0.0.5-pre8
[0.0.5-pre7]: https://github.com/ChidcGithub/Laziest-import/compare/v0.0.4...v0.0.5-pre7
[0.0.4]: https://github.com/ChidcGithub/Laziest-import/compare/v0.0.3...v0.0.4
[0.0.3]: https://github.com/ChidcGithub/Laziest-import/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/ChidcGithub/Laziest-import/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/ChidcGithub/Laziest-import/releases/tag/v0.0.1
