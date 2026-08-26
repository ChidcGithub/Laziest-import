# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1.0] - 2026-08-26

### Added
- **Type-stub (.pyi) symbol indexing**: the index builder now parses `.pyi` stub files first and only falls back to import-and-inspect scanning when no usable stub exists
  - Zero import side effects — modules are never executed during index building (safe against hostile code, works even when `__init__.py` would crash)
  - Order-of-magnitude faster on heavy packages (e.g. matplotlib: ~4ms stub parse vs ~160ms import scan)
  - Precise type signatures extracted for free (`(host: str, port: int = 5432) -> bool`)
  - Handles conditional guards (`if sys.version_info ...`, `try/except`) and overload deduplication
  - Toggle via `_config._STUB_INDEX_CONFIG["enabled"]`; stats exposed as `stub_scanned_modules` in `get_symbol_cache_info()`

## [1.0.0.7] - 2026-08-26

### Fixed
- Critical: auto-install fallback now respects `_AUTO_INSTALL_CONFIG["enabled"]` (default off) — import failures no longer trigger unexpected pip prompts or subprocesses
- Critical: module priorities loaded from bundled `mappings/priorities.json` at init; unlisted modules default to 80; single exact-match candidates no longer rejected by conflict logic
- Critical: incremental symbol build loads the complete on-disk index before merging, no longer overwriting the full index with partial data
- Critical: `FileCache.from_dict` whitelists fields so unknown JSON keys can no longer break `import laziest_import`
- High: snapshot iteration over shared symbol caches / `sys.modules` / lazy proxies eliminates `RuntimeError: dictionary changed size during iteration` during concurrent background builds
- High: cache size accounting and cleanup now match actual cache file names (`symbol_index_*`, `tracked_packages`, sha256 file caches)
- High: atomic tmp + `os.replace()` writes for all JSON caches (crash-safe persistence)
- Medium: `LazyProxy`/`LazySymbol` underscore guards prevent IPython/copy/pickle probes from triggering searches or imports and polluting `_ALIAS_MAP`
- Medium: auto-search fallback refuses to substitute a parent module for a missing submodule; `_ALIAS_MAP` writes unified under a shared lock
- Medium: `register_alias` remapping rebuilds stale proxies; `reload_aliases` swaps atomically and rebuilds outdated proxies
- Medium: pip subprocess forced UTF-8 decoding (CJK Windows locales misreported successful installs as failures)
- Medium: short-option install flags (`-r`, `-c`, `-f`, `-i`, `-e`) blocked; package name URL check casefolded
- Medium: profiler memory via `tracemalloc.get_traced_memory()` (was single-allocation-site size); benchmark excludes failed iterations, clears submodule caches, corrected speedup wording
- Medium: async imports honor retry config via non-blocking backoff (`asyncio.sleep`)
- Medium: `BackgroundIndexBuilder` start race fixed with state lock; `stop()` is cooperative (no premature flag reset causing double builds); timeout implemented via watchdog timer
- Low: state visibility unified between `_cache/_background.py` and `_lazy_index.BackgroundIndexBuilder`; event-based wait replaces busy polling
- Low: hook iteration snapshot; callback failures always logged with traceback instead of silently swallowed
- Low: dependency tree submodule ownership check (`attr.__module__`) stops re-exported attributes becoming bogus child nodes
- Low: relative imports excluded from third-party prediction in pre-analysis
- Low: `__name__` answered from slot metadata without importing the real module
- Low: Python version compatibility compares `(major, minor)` tuples instead of string prefixes
- Low: Windows `unlink()` protection when cache files are held by other processes
- Low: stale value-bound flags (`_DEBUG_MODE`, `_SYMBOL_INDEX_BUILT`) replaced with runtime attribute access

### Changed
- Cache version bumped so potentially corrupt partial indexes from 1.0.0.6 rebuild cleanly

## [1.0.0.6] - 2026-07-11

### Fixed
- Critical: `module_access_counts` reset bug causing lost access history
- Critical: `LazySymbol` infinite re-import loop when underlying symbol value is `None`
- Critical: `__hash__`/`__eq__` hash contract violation causing dict/set corruption
- Critical: `_scan_path_modules` returning after only first `sys.path` entry
- Critical: `reset_all()` reading `_BASE_EXPORTS` from wrong module
- Critical: `get_symbol_help()` accessing non-existent attributes on `SearchResult`
- Critical: `obj is None` conflating missing attribute with `None`-valued attribute
- High: `_compare_versions` prerelease comparison now correctly handles numeric suffixes
- High: `_rcconfig.py` environment variables now have highest priority
- High: `_install.py` interactive override parameter now respected
- High: Cache cleanup limited to `laziest_*.json` files; `max_cache_size_mb=0` treated as unlimited
- High: Distribution name to import name mapping (e.g., `beautifulsoup4` → `bs4`)
- High: Partial cache load no longer prevents full rebuild (`or` → `and`)
- High: `catch_warnings` scope now covers submodule scanning
- High: AST scanner supports chained attribute access (`lz.np.array()`)
- Medium: `LazySubmodule` fallback path now caches all attribute types
- Medium: Thread lock on `_ALIAS_MAP` writes in `LazyProxy`
- Medium: TOCTOU fixed in negative cache, alias iteration, and hook removal
- Medium: `which()` returns `None` on module hint mismatch instead of silent fallback
- Medium: `invalidate_package_cache` now holds `_SYMBOL_CACHE_LOCK`
- Broad `except Exception` narrowed to specific exceptions in 10+ locations
- `sys.path.insert(0, ".")` removed from 3 test files
- Trivially-true test assertions (`is True or is False`) replaced with `isinstance(bool)`
- Redundant `x as x` imports removed from `_symbol/` redirect files
- `import time` moved to top of `_cache/_file_cache.py`
- Duplicated `SymbolIndexCache` eliminated (consolidated to `_cache/_symbol_index.py`)
- `_is_stdlib_module` set promoted to module-level constant

### Added
- Reflected operators on `LazySymbol`: `__radd__`, `__rsub__`, `__rmul__`, `__rtruediv__`, `__rfloordiv__`, `__rmod__`, `__rpow__`, `__rmatmul__`, `__neg__`, `__pos__`, `__abs__`, `__invert__`
- Retry logic in `_async_ops.py` based on `_RETRY_CONFIG`
- `fix` CLI command generating standard `import` statements from lazy alias usage
- `which_all` now performs live search even after index built
- `unregister()` and `list_registered()` in `_lazy_registry.py`
- `get_progress()` public API in `BackgroundIndexBuilder`
- `symbol_autocomplete(prefix)` for symbol name prefix completion
- Test count and version unified across READMEs

## [0.1.0.2] - 2026-06-21

### Fixed
- `list_module_symbols(..., include_private=False)` no longer returns private submodule names like `__main__`
- Removed invalid alias `3d` -> `vedo` which is not a legal Python identifier
- `pyproject.toml` classifiers now match `requires-python = ">=3.9"` (dropped Python 3.8)
- README test count badge updated to 1065

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
