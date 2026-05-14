# Laziest-Import 0.1.0 Migration Guide

> **Version**: 0.1.0-pre7 → 0.1.0
> **Date**: 2026-05-14

## Overview

Laziest-import has been refactored from a procedural API to an **object-oriented API** while maintaining full backward compatibility. All old functions still work but emit `FutureWarning` deprecation notices.

## Quick Start

```python
# Old way (still works, but deprecated):
from laziest_import import lz
import numpy as np  # via lz.np

# New way (recommended):
from laziest_import import LazyImport
lz = LazyImport()

# Or use the module-level singleton:
from laziest_import import lz
lz.module.numpy      # → LazyModule for numpy
lz.config.debug = True
lz.hooks.pre += my_hook
```

## Old API → New API Mapping

### Module Loading

| Old API | New API |
|---------|---------|
| `lz.numpy` | `lz.module.numpy` |
| `lz.os` | `lz.module.os` |
| `lz.os.path` | `lz.module.os.path` |
| `get_module("math")` | `lz.module.get("math")` |
| `list_loaded()` | `lz.module.list_loaded()` |
| `list_available()` | `lz.module.list_available()` |
| `reload_module("numpy")` | `lz.module.reload("numpy")` |

### Configuration

| Old API | New API |
|---------|---------|
| `enable_debug_mode()` | `lz.config.debug = True` |
| `disable_debug_mode()` | `lz.config.debug = False` |
| `is_debug_mode()` | `lz.config.debug` |
| `enable_auto_search()` | `lz.config.auto_search = True` |
| `disable_auto_search()` | `lz.config.auto_search = False` |
| `is_auto_search_enabled()` | `lz.config.auto_search` |

### Symbol Search

| Old API | New API |
|---------|---------|
| `search_symbol("DF")` | `lz.symbol.search("DF")` |
| `search_class("DataFrame")` | `lz.symbol.search("DataFrame", symbol_type="class")` |
| `which("sqrt")` | `lz.symbol.which("sqrt")` |
| `which_all("Path")` | `lz.symbol.which_all("Path")` |
| `enable_symbol_search()` | `lz.symbol.config.enable()` |
| `disable_symbol_search()` | `lz.symbol.config.enabled = False` |
| `is_symbol_search_enabled()` | `lz.symbol.config.enabled` |
| `rebuild_symbol_index()` | `lz.symbol.index.rebuild()` |
| `set_symbol_preference("DF", "pandas")` | `lz.symbol.prefer("DF", "pandas")` |
| `get_symbol_preference("DF")` | `lz.symbol.preference("DF")` |
| `clear_symbol_preference("DF")` | `lz.symbol.clear_preference("DF")` |
| `search_with_sharding("Foo")` | `lz.symbol.sharded("Foo")` |

### Aliases

| Old API | New API |
|---------|---------|
| `register_alias("np", "numpy")` | `lz.alias.register("np", "numpy")` |
| `register_aliases({"np": "numpy"})` | `lz.alias.register_many({"np": "numpy"})` |
| `unregister_alias("np")` | `lz.alias.unregister("np")` |
| `validate_aliases()` | `lz.alias.validate()` |
| `validate_aliases_importable(...)` | `lz.alias.validate(...)` |
| `get_config_paths()` | `lz.alias.paths` |
| `get_config_dirs()` | `lz.alias.dirs` |
| `reload_aliases()` | `lz.alias.reload()` |
| `export_aliases()` | `lz.alias.export()` |

### Cache

| Old API | New API |
|---------|---------|
| `clear_cache()` | `lz.cache.clear()` |
| `get_cache_stats()` | `lz.cache.stats` |
| `reset_cache_stats()` | `lz.cache.stats.reset()` |
| `set_cache_config(...)` | `lz.cache.config.max_size_mb = 200` |
| `get_cache_config()` | `lz.cache.config` |
| `clear_symbol_cache()` | `lz.cache.symbols.clear()` |
| `invalidate_package_cache("numpy")` | `lz.cache.invalidate("numpy")` |
| `enable_cache_compression()` | `lz.cache.compression = True` |

### File Cache

| Old API | New API |
|---------|---------|
| `enable_file_cache()` | `lz.cache.files.enabled = True` |
| `disable_file_cache()` | `lz.cache.files.enabled = False` |
| `is_file_cache_enabled()` | `lz.cache.files.enabled` |
| `clear_file_cache()` | `lz.cache.files.clear()` |
| `get_file_cache_info()` | `lz.cache.files.info()` |
| `force_save_cache()` | `lz.cache.files.force_save()` |

### Hooks

| Old API | New API |
|---------|---------|
| `add_pre_import_hook(fn)` | `lz.hooks.pre += fn` |
| `add_post_import_hook(fn)` | `lz.hooks.post += fn` |
| `remove_pre_import_hook(fn)` | `lz.hooks.pre -= fn` |
| `remove_post_import_hook(fn)` | `lz.hooks.post -= fn` |
| `clear_import_hooks()` | `lz.hooks.clear()` |

### Async

| Old API | New API |
|---------|---------|
| `import_async("numpy")` | `await lz.async.get("numpy")` |
| `import_multiple_async([...])` | `await lz.async.fetch("numpy", "pandas")` |
| `enable_retry()` | `lz.config.retry.enabled = True` |
| `disable_retry()` | `lz.config.retry.enabled = False` |
| `is_retry_enabled()` | `lz.config.retry.enabled` |

### Install

| Old API | New API |
|---------|---------|
| `install_package("numpy")` | `lz.install.package("numpy")` |
| `enable_auto_install()` | `lz.install.enable()` |
| `disable_auto_install()` | `lz.install.disable()` |
| `is_auto_install_enabled()` | `lz.install.enabled` |
| `set_pip_index(url)` | `lz.install.index = url` |
| `set_pip_extra_args(args)` | `lz.install.extra_args = args` |
| `rebuild_module_cache()` | `lz.install.rebuild_cache()` |

### Analysis & Profiling

| Old API | New API |
|---------|---------|
| `analyze_file(path)` | `lz.analyze.file(path)` |
| `analyze_source(code)` | `lz.analyze.code(code)` |
| `analyze_directory(dir)` | `lz.analyze.dir(dir)` |
| `start_profiling()` | `lz.profile.start()` |
| `stop_profiling()` | `lz.profile.stop()` |
| `get_profile_report()` | `lz.profile.report()` |
| `print_profile_report()` | `lz.profile.print_report()` |
| `dependency_tree(...)` | `lz.analyze.dep_tree(...)` |
| `benchmark(func, ...)` | `lz.profile.benchmark(func, ...)` |

### Environment & Preferences

| Old API | New API |
|---------|---------|
| `detect_environment()` | `lz.analyze.environment()` |
| `show_environment()` | `lz.analyze.show_environment()` |
| `save_preferences()` | `lz.preferences.save()` |
| `load_preferences()` | `lz.preferences.load()` |
| `apply_preferences()` | `lz.preferences.apply()` |
| `clear_preferences()` | `lz.preferences.clear()` |

### Version

| Old API | New API |
|---------|---------|
| `get_version("numpy")` | `lz.version.of("numpy")` |
| `get_package_version("numpy")` | `lz.version.of("numpy")` |
| `get_all_package_versions()` | `lz.version.all_packages()` |
| `get_laziest_import_version()` | `lz.version.current` |

## New Data Classes

```python
from laziest_import import AutoInstallConfig, RetryConfig, CacheConfig

# Configure auto-install
lz.config.auto_install = AutoInstallConfig(
    interactive=True,
    index=None,
    prefer_uv=False,
    silent=True,
)

# Configure retry behavior
lz.config.retry = RetryConfig(
    max_retries=5,
    retry_delay=1.0,
    modules={"torch", "tensorflow"},
)

# Configure cache
lz.cache.config = CacheConfig(
    max_size_mb=500,
    compression=True,
)
```

## New Context Manager

```python
from laziest_import import ConfigContext

# Temporarily override config
with ConfigContext(debug=True, auto_search=False):
    # debug=True only within this block
    import numpy as np
```

## Key Behavioral Changes

1. **`lz` is an instance, not a module**: `from laziest_import import lz` gives you a `LazyImport()` singleton. Access sub-namespaces as attributes: `lz.module`, `lz.config`, `lz.cache`, etc.

2. **`from laziest_import import *`** still exports all old functions for backward compatibility, each with `FutureWarning`.

3. **`from laziest_import import help`** works both as a direct import and via `lz.help()`.

4. **State is centralized** in `_config.py` — all sub-namespaces read from and write to the same global state.

## Migration Checklist

- [ ] Replace `enable_debug_mode()` → `lz.config.debug = True`
- [ ] Replace `clear_cache()` → `lz.cache.clear()`
- [ ] Replace `list_loaded()` → `lz.module.list_loaded()`
- [ ] Replace `register_alias()` → `lz.alias.register()`
- [ ] Replace `add_pre_import_hook(fn)` → `lz.hooks.pre += fn`
- [ ] Replace `search_symbol("X")` → `lz.symbol.search("X")`
- [ ] Replace `get_cache_stats()` → `lz.cache.stats`
- [ ] Replace `import_async()` → `await lz.async.get()`
- [ ] Replace `install_package()` → `lz.install.package()`
- [ ] Replace `analyze_file()` → `lz.analyze.file()`
- [ ] Switch to new data classes for configuration