# laziest-import

[![PyPI version](https://img.shields.io/pypi/v/laziest-import.svg)](https://pypi.org/project/laziest-import/)
[![PyPI pre-release](https://img.shields.io/github/release/ChidcGithub/Laziest-import/all.svg?label=pre-release&color=orange)](https://github.com/ChidcGithub/Laziest-import/releases)
[![Python](https://img.shields.io/pypi/pyversions/laziest-import.svg)](https://pypi.org/project/laziest-import/)
[![License](https://img.shields.io/pypi/l/laziest-import.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/laziest-import.svg)](https://pypi.org/project/laziest-import/)
[![GitHub stars](https://img.shields.io/github/stars/ChidcGithub/Laziest-import.svg?style=social)](https://github.com/ChidcGithub/Laziest-import/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/ChidcGithub/Laziest-import.svg?style=social)](https://github.com/ChidcGithub/Laziest-import/network/members)
[![GitHub issues](https://img.shields.io/github/issues/ChidcGithub/Laziest-import.svg)](https://github.com/ChidcGithub/Laziest-import/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/ChidcGithub/Laziest-import.svg)](https://github.com/ChidcGithub/Laziest-import/pulls)
[![GitHub Actions](https://github.com/ChidcGithub/Laziest-import/workflows/Build%20and%20Publish/badge.svg)](https://github.com/ChidcGithub/Laziest-import/actions)
[![GitHub last commit](https://img.shields.io/github/last-commit/ChidcGithub/Laziest-import.svg)](https://github.com/ChidcGithub/Laziest-import/commits/main)
[![GitHub repo size](https://img.shields.io/github/repo-size/ChidcGithub/Laziest-import.svg)](https://github.com/ChidcGithub/Laziest-import)
[![Type hints](https://img.shields.io/badge/type_hints-mypy-blue.svg)](https://mypy-lang.org/)
[![Code style](https://img.shields.io/badge/code_style-pep8-green.svg)](https://peps.python.org/pep-0008/)
[![Tests](https://img.shields.io/badge/tests-222_passed-brightgreen.svg)](https://github.com/ChidcGithub/Laziest-import/tree/main/tests)

A zero-configuration lazy import library. Import and use any installed module with a single line.

```python
from laziest_import import *

arr = np.array([1, 2, 3])      # numpy
df = pd.DataFrame({'a': [1]})  # pandas
plt.plot([1, 2, 3])            # matplotlib
```

No `import numpy as np`, no `import pandas as pd` required.

## Installation

```bash
pip install laziest-import
```

## Quick Start

<details>
<summary>Show examples</summary>

**Method 1: Wildcard import (recommended)**

```python
from laziest_import import *

# Common libraries work immediately
arr = np.array([1, 2, 3])           # numpy
df = pd.DataFrame({'a': [1, 2]})    # pandas
plt.plot([1, 2, 3]); plt.show()     # matplotlib

# Standard library
print(os.getcwd())                  # os
data = json.dumps({'key': 'value'}) # json

# Submodules load automatically
result = np.linalg.svd(matrix)      # numpy.linalg
```

**Method 2: Namespace prefix**

```python
import laziest_import as lz

arr = lz.np.array([1, 2, 3])
df = lz.pd.DataFrame({'a': [1, 2]})
```

**Method 3: Lazy proxy (with auto-correction)**

```python
from laziest_import import lazy

# Automatic typo correction
arr = lazy.nump.array([1, 2, 3])    # nump -> numpy ✅
df = lazy.pnda.DataFrame()          # pnda -> pandas ✅

# Submodule shortcuts
layer = lazy.nn.Linear(10, 5)       # nn -> torch.nn ✅
```

</details>

## Key Features

| Feature | Description |
|---------|-------------|
| **Modular architecture** | Clean 9-module codebase for maintainability |
| **Lazy loading** | Modules import only on first access, reducing startup overhead |
| **Submodule support** | `np.linalg.svd()` chains submodules automatically |
| **Auto-discovery** | Unregistered names search installed modules automatically |
| **Typo correction** | Misspelling auto-correction (`nump` → `numpy`, `matplotlip` → `matplotlib`) |
| **Abbreviation expansion** | 300+ abbreviations (`nn` → `torch.nn`, `F` → `torch.nn.functional`) |
| **Fuzzy matching** | Typo correction via Levenshtein distance algorithm |
| **Auto-install** | Optional: missing modules can be pip-installed automatically |
| **Multi-level cache** | Three-tier caching (stdlib/third-party/memory) for fast lookups |
| **Cache persistence** | Symbol index saved to disk with configurable TTL |
| **Cache statistics** | Track hits/misses and optimize performance |
| **Version checking** | Automatic compatibility warnings for aliases/mappings |
| **1000+ aliases** | Predefined aliases for common packages |
| **222 tests** | Comprehensive test coverage |

## What's New in v0.0.3

- **Modular Architecture**: Refactored from single 5800-line file to 9 clean modules
- **Version Compatibility**: Centralized version management with `version.json` and range checking
- **LazyProxy**: New `lazy` object for automatic typo correction
- **300+ abbreviations**: Expanded library shortcuts in `mappings/abbreviations.json`
- **Submodule mappings**: `nn` → `torch.nn`, `optim` → `torch.optim`, etc.
- **Misspelling correction**: 150+ common typos auto-corrected via fuzzy matching
- **Folder-based config**: Organize aliases in `~/.laziest_import/aliases/A.json`, `B.json`, etc.
- **JSON-based mappings**: All mappings stored in `mappings/` directory for easy customization
- **222 tests**: Comprehensive test coverage with pytest

## Auto-Install

When enabled, accessing an uninstalled module triggers automatic installation:

```python
from laziest_import import *

# Enable auto-install with interactive confirmation
enable_auto_install()

# Use a mirror for faster downloads
enable_auto_install(index="https://pypi.org/simple")

# Now accessing uninstalled modules prompts for installation
arr = np.array([1, 2, 3])  # If numpy is missing, prompts to install
```

<details>
<summary>Auto-install API</summary>

| Function | Description |
|----------|-------------|
| `enable_auto_install(interactive=True, index=None)` | Enable auto-install |
| `disable_auto_install()` | Disable auto-install |
| `is_auto_install_enabled()` | Check status |
| `install_package(name)` | Manually install a package |
| `set_pip_index(url)` | Set mirror URL |

</details>

## Predefined Aliases

<details>
<summary>Show full list</summary>

| Category | Aliases |
|----------|---------|
| Data Science | `np`, `pd`, `plt`, `sns`, `scipy` |
| Machine Learning | `torch`, `tf`, `keras`, `sklearn`, `xgboost`, `lightgbm` |
| Deep Learning | `transformers`, `langchain`, `llama_index` |
| Web Frameworks | `flask`, `django`, `fastapi`, `starlette` |
| HTTP Clients | `requests`, `httpx`, `aiohttp` |
| Databases | `sqlalchemy`, `pymongo`, `redis`, `duckdb` |
| Cloud Services | `boto3` (AWS), `google.cloud`, `azure` |
| Image Processing | `cv2`, `PIL.Image`, `skimage` |
| GUI | `PyQt6`, `tkinter`, `flet`, `nicegui` |
| DevOps | `docker`, `kubernetes`, `ansible` |
| NLP | `spacy`, `nltk`, `transformers` |
| Visualization | `plotly`, `bokeh`, `streamlit`, `gradio` |

</details>

## Advanced Features

<details>
<summary>File-based cache</summary>

Cache imported modules for faster subsequent runs:

```python
import laziest_import as lz

# View cache status
info = lz.get_file_cache_info()
# {'cache_size_bytes': 12345, 'cache_size_mb': 0.01, 'max_cache_size_mb': 100, ...}

# Set custom cache directory
lz.set_cache_dir('./my_cache')

# Clear cache
lz.clear_file_cache()
```

</details>

<details>
<summary>Cache configuration</summary>

```python
import laziest_import as lz

# Get cache version
version = lz.get_cache_version()  # '0.0.2.3'

# Configure cache settings
lz.set_cache_config(
    symbol_index_ttl=3600,       # Symbol index TTL: 1 hour
    stdlib_cache_ttl=2592000,    # Stdlib cache TTL: 30 days
    max_cache_size_mb=200        # Max cache size: 200 MB
)

# Get cache statistics
stats = lz.get_cache_stats()
# {'symbol_hits': 10, 'symbol_misses': 2, 'module_hits': 5, 
#  'module_misses': 1, 'hit_rate': 0.875, ...}

# Reset statistics
lz.reset_cache_stats()

# Invalidate cache for a specific package (after upgrade)
lz.invalidate_package_cache('numpy')

# Rebuild symbol index
lz.rebuild_symbol_index()
```

</details>

<details>
<summary>Debug and statistics</summary>

```python
import laziest_import as lz

# Enable debug mode
lz.enable_debug_mode()

# Get import statistics
stats = lz.get_import_stats()
# {'total_imports': 3, 'total_time': 0.15, 'module_times': {...}}

# Reset statistics
lz.reset_import_stats()
```

</details>

<details>
<summary>Import hooks</summary>

```python
import laziest_import as lz

def before_import(module_name):
    print(f"About to import: {module_name}")

def after_import(module_name, module):
    print(f"Imported: {module_name}")

lz.add_pre_import_hook(before_import)
lz.add_post_import_hook(after_import)
```

</details>

<details>
<summary>Async import</summary>

```python
import laziest_import as lz
import asyncio

async def main():
    # Import multiple modules in parallel
    modules = await lz.import_multiple_async(['numpy', 'pandas', 'torch'])
    np, pd = modules['numpy'], modules['pandas']

asyncio.run(main())
```

</details>

<details>
<summary>Custom aliases</summary>

```python
from laziest_import import *

# Register a single alias
register_alias("mylib", "my_awesome_library")

# Register multiple aliases
register_aliases({
    "api": "my_api_client",
    "db": "my_database_lib",
})
```

</details>

## API Reference

<details>
<summary>Show full API</summary>

### Alias Management

| Function | Description |
|----------|-------------|
| `register_alias(alias, module_name)` | Register an alias |
| `register_aliases(dict)` | Register multiple aliases |
| `unregister_alias(alias)` | Remove an alias |
| `list_loaded()` | List loaded modules |
| `list_available()` | List all available aliases |
| `get_module(alias)` | Get module object |
| `clear_cache()` | Clear cache |

### Auto-Search

| Function | Description |
|----------|-------------|
| `enable_auto_search()` | Enable auto-discovery |
| `disable_auto_search()` | Disable auto-discovery |
| `search_module(name)` | Search for a module |
| `search_class(class_name)` | Search by class name |
| `rebuild_module_cache()` | Rebuild cache |

### Symbol Search

| Function | Description |
|----------|-------------|
| `enable_symbol_search()` | Enable symbol search |
| `search_symbol(name)` | Search for classes/functions |
| `rebuild_symbol_index()` | Rebuild index |

### Auto-Install

| Function | Description |
|----------|-------------|
| `enable_auto_install()` | Enable auto-install |
| `disable_auto_install()` | Disable auto-install |
| `install_package(name)` | Install manually |
| `set_pip_index(url)` | Set mirror URL |

### Other

| Function | Description |
|----------|-------------|
| `get_version(alias)` | Get module version |
| `reload_module(alias)` | Reload a module |
| `enable_retry()` | Enable retry mechanism |
| `enable_file_cache()` | Enable file cache |

### Cache Management

| Function | Description |
|----------|-------------|
| `get_cache_version()` | Get cache version |
| `set_cache_config(...)` | Configure cache settings |
| `get_cache_config()` | Get cache configuration |
| `get_cache_stats()` | Get cache statistics |
| `reset_cache_stats()` | Reset cache statistics |
| `invalidate_package_cache(pkg)` | Invalidate package cache |
| `get_file_cache_info()` | Get file cache info |
| `clear_file_cache()` | Clear file cache |
| `set_cache_dir(path)` | Set cache directory |

</details>

## Configuration

Custom aliases can be configured in:

1. `~/.laziest_import/aliases/A.json`, `B.json`, ... (user global, letter-based)
2. `./.laziest_import/A.json`, `B.json`, ... (project level)

```json
// ~/.laziest_import/aliases/M.json
{
    "mylib": "my_awesome_library",
    "mpl": "matplotlib"
}
```

Letter-based files load faster - only the relevant file is loaded on demand.

### JSON Mappings

All mappings are stored in `laziest_import/mappings/` directory:

| File | Description |
|------|-------------|
| `abbreviations.json` | Module abbreviations (`np` → `numpy`) |
| `misspellings.json` | Common misspellings (`numpi` → `numpy`) |
| `submodules.json` | Submodule shortcuts (`nn` → `torch.nn`) |
| `package_rename.json` | Package rename mappings (`sklearn` → `scikit-learn`) |
| `symbol_misspellings.json` | Symbol misspellings (`dataframe` → `DataFrame`) |
| `priorities.json` | Module priorities for conflict resolution |

### Version Management

Version compatibility is managed centrally in `version.json`:

```json
{
    "_current_version": "0.0.3.1",
    "_cache_version": "0.0.3.1",
    "aliases": {
        "_min_version": "0.0.3",
        "_max_version": "0.0.4"
    },
    "mappings": {
        "_min_version": "0.0.3",
        "_max_version": "0.0.4"
    }
}
```

If the current version is outside the specified range, a warning is issued:

```
UserWarning: [laziest-import] aliases: Version 0.0.4 is at or above maximum 0.0.4. 
Some alias features may not work correctly.
```

## How It Works

1. **Proxy objects**: Each alias maps to a `LazyModule` proxy
2. **On-demand import**: Real import triggers on first attribute access via `__getattr__`
3. **Caching**: Imported modules cache within the proxy object
4. **Chain proxies**: `LazySubmodule` handles recursive lazy loading
5. **Fuzzy search**: Levenshtein distance algorithm for fault-tolerant matching

### Multi-Level Cache Architecture

The library uses a three-tier caching system for optimal performance:

| Cache Level | Description | Default TTL |
|-------------|-------------|-------------|
| **Stdlib cache** | Standard library symbols | 7 days |
| **Third-party cache** | Installed package symbols | 24 hours |
| **Memory cache** | Hot cache for current session | Session |

Cache files are stored in `~/.laziest_import/cache/` and automatically:
- Expire based on TTL settings
- Clean up when exceeding size limit (default: 100 MB)
- Invalidate on Python version changes

## Requirements

- Python 3.8+

## License

[MIT](LICENSE)
