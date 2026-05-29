# laziest-import

[![PyPI version](https://img.shields.io/pypi/v/laziest-import.svg)](https://pypi.org/project/laziest-import/)
[![PyPI pre-release](https://img.shields.io/github/release/ChidcGithub/Laziest-import/all.svg?label=pre-release&color=orange)](https://github.com/ChidcGithub/Laziest-import/releases)
[![Python](https://img.shields.io/pypi/pyversions/laziest-import.svg)](https://pypi.org/project/laziest-import/)
[![License](https://img.shields.io/pypi/l/laziest-import.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/laziest-import.svg)](https://pypi.org/project/laziest-import/)
[![GitHub stars](https://img.shields.io/github/stars/ChidcGithub/Laziest-import.svg?style=social&label=Stars)](https://github.com/ChidcGithub/Laziest-import/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/ChidcGithub/Laziest-import.svg?style=social&label=Forks)](https://github.com/ChidcGithub/Laziest-import/network/members)
[![GitHub issues](https://img.shields.io/github/issues/ChidcGithub/Laziest-import.svg)](https://github.com/ChidcGithub/Laziest-import/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/ChidcGithub/Laziest-import.svg)](https://github.com/ChidcGithub/Laziest-import/pulls)
[![GitHub Actions](https://github.com/ChidcGithub/Laziest-import/workflows/Build%20and%20Publish/badge.svg)](https://github.com/ChidcGithub/Laziest-import/actions)
[![GitHub last commit](https://img.shields.io/github/last-commit/ChidcGithub/Laziest-import.svg)](https://github.com/ChidcGithub/Laziest-import/commits/main)
[![GitHub repo size](https://img.shields.io/github/repo-size/ChidcGithub/Laziest-import.svg)](https://github.com/ChidcGithub/Laziest-import)
[![Type hints](https://img.shields.io/badge/type_hints-mypy-blue.svg)](https://mypy-lang.org/)
[![Code style](https://img.shields.io/badge/code_style-pep8-green.svg)](https://peps.python.org/pep-0008/)
[![Tests](https://img.shields.io/badge/tests-1055%20passed-brightgreen.svg)](https://github.com/ChidcGithub/Laziest-import/tree/main/tests)
[![Coverage](https://img.shields.io/badge/coverage-comprehensive-brightgreen.svg)](https://github.com/ChidcGithub/Laziest-import/tree/main/tests)
[![CodeFactor](https://img.shields.io/badge/code_quality-A-brightgreen.svg)](https://www.codefactor.io/repository/github/chidcgithub/laziest-import)
[![Maintainability](https://img.shields.io/badge/maintainability-excellent-brightgreen.svg)](https://github.com/ChidcGithub/Laziest-import)
[![Contributors](https://img.shields.io/badge/contributors-welcome-brightgreen.svg)](https://github.com/ChidcGithub/Laziest-import/graphs/contributors)
[![First Timers Only](https://img.shields.io/badge/first-timers_only-blue.svg)](https://github.com/ChidcGithub/Laziest-import/contribute)
[![Documentation Status](https://img.shields.io/badge/docs-complete-brightgreen.svg)](https://github.com/ChidcGithub/Laziest-import)
[![Made with Love](https://img.shields.io/badge/made_with-%E2%9D%A4-red.svg)](https://github.com/ChidcGithub/Laziest-import)
[![Pythonic](https://img.shields.io/badge/pythonic-yes-blue.svg)](https://www.python.org/dev/peps/pep-0008/)
[![Open Source Love](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://github.com/ChidcGithub/Laziest-import)
[![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/ChidcGithub/Laziest-import)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/ChidcGithub/Laziest-import/pulls)
[![License MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

[![中文版](https://img.shields.io/badge/%E4%B8%AD%E6%96%87-README_CN-blue.svg)](README_CN.md)
[![English](https://img.shields.io/badge/English-README-blue.svg)](README.md)

---

<div align="center">

## Zero-Configuration Lazy Import Library

**Import and use any installed（for the not installed, it uses pip to auto install if you permitted) module with a single line**

<p align="center">
 <b>A magical way to import Python modules - just use them!</b>
</p>

</div>

---

## Table of Contents

- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Examples](#examples)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [How It Works](#how-it-works)
- [Contributing](#contributing)
- [License](#license)

---

## Key Features

| Feature | Badge | Description |
|---------|-------|-------------|
| Lazy Loading | ![](https://img.shields.io/badge/feature-lazy_loading-green.svg) | Modules import only on first access |
| Background Index | ![](https://img.shields.io/badge/feature-background_index-blue.svg) | Symbol index builds in background thread |
| Auto-Correction | ![](https://img.shields.io/badge/feature-auto_correction-purple.svg) | Typo correction (`nump` → `numpy`) |
| Symbol Search | ![](https://img.shields.io/badge/feature-symbol_search-orange.svg) | Search symbols across all modules |
| Strict Mode | ![](https://img.shields.io/badge/feature-strict_mode-red.svg) | AmbiguousSymbolError on symbol conflicts |
| Multi-Level Cache | ![](https://img.shields.io/badge/feature-multi_level_cache-green.svg) | Three-tier caching for speed |
| Dependency Analysis | ![](https://img.shields.io/badge/feature-dependency_analysis-blue.svg) | Analyze module dependencies |
| Performance Benchmark | ![](https://img.shields.io/badge/feature-benchmarking-purple.svg) | Benchmark imports and functions |
| CLI Interface | ![](https://img.shields.io/badge/feature-cli-lightgrey.svg) | `laziest-import freeze` / `init` commands |
| 1055+ Tests | ![](https://img.shields.io/badge/tests-1055%2B-brightgreen.svg) | Comprehensive test coverage |
| 1000+ Aliases | ![](https://img.shields.io/badge/aliases-1000%2B-orange.svg) | Predefined for common packages |

---

## Installation

```bash
# Stable version
pip install laziest-import

# Pre-release version (latest features)
pip install --pre laziest-import

# From source (latest development)
pip install git+https://github.com/ChidcGithub/Laziest-import.git
```

---

## Quick Start

### Method 1: Wildcard Import (Recommended)

```python
from laziest_import import *

# Data Science
arr = np.array([1, 2, 3]) # numpy
df = pd.DataFrame({'a': [1, 2]}) # pandas
plt.plot([1, 2, 3]); plt.show() # matplotlib

# Standard Library
print(os.getcwd()) # os
data = json.dumps({'key': 'value'}) # json
result = math.sqrt(16) # math

# Submodules (auto-loading)
svd_result = np.linalg.svd(matrix) # numpy.linalg.svd()
```

### Method 2: Namespace Prefix (Recommended)

```python
from laziest_import import lz

arr = lz.np.array([1, 2, 3])
df = lz.pd.DataFrame({'a': [1, 2]})
```

### Method 3: Lazy Proxy (with Auto-Correction)

```python
from laziest_import import lazy

# Automatic typo correction
arr = lazy.nump.array([1, 2, 3]) # nump -> numpy 
df = lazy.pnda.DataFrame() # pnda -> pandas 
arr2 = lazy.nupi.array([4, 5, 6]) # nupi -> numpy 

# Submodule shortcuts
layer = lazy.nn.Linear(10, 5) # nn -> torch.nn 
relu = lazy.F.relu(tensor) # F -> torch.nn.functional 
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Modular architecture** | Clean 13-module `_api/` package for maintainability |
| **Lazy loading** | Modules import only on first access, reducing startup overhead |
| **Lazy function loading** | Symbol functions loaded on-demand for faster startup |
| **Background index build** | Symbol index builds in background thread |
| **Symbol sharding** | Large packages split into shards for faster access |
| **Submodule support** | `np.linalg.svd()` chains submodules automatically |
| **Auto-discovery** | Unregistered names search installed modules automatically |
| **Typo correction** | Misspelling auto-correction (`nump` → `numpy`, `matplotlip` → `matplotlib`) |
| **Abbreviation expansion** | 300+ abbreviations (`nn` → `torch.nn`, `F` → `torch.nn.functional`) |
| **Fuzzy matching** | Typo correction via Levenshtein distance algorithm |
| **Strict mode** | Raise `AmbiguousSymbolError` on symbol conflicts |
| **CLI interface** | `laziest-import freeze` and `laziest-import init` |
| **Symbol location** | `lz.which()` finds where symbols are defined |
| **Auto-install** | Optional: missing modules can be pip-installed automatically |
| **Multi-level cache** | Three-tier caching (stdlib/third-party/memory) for fast lookups |
| **Cache persistence** | Symbol index saved to disk with configurable TTL |
| **Cache statistics** | Track hits/misses and optimize performance |
| **Version checking** | Automatic compatibility warnings for aliases/mappings |
| **Type hints support** | `LazySymbol.__class_getitem__` for generic type hints |
| **Dependency tree analysis** | `lz.dependency_tree()` - analyze module dependencies |
| **Performance benchmarking** | `lz.benchmark()` - benchmark functions and imports |
| **Dependency pre-analysis** | Scan code to predict required imports |
| **Import profiler** | Record module load times and memory usage |
| **Environment detection** | Detect virtual environments (venv/conda/virtualenv) |
| **Conflict visualization** | Find and display symbol conflicts across modules |
| **Persistent preferences** | Save/load user preferences to `~/.laziestrc` |
| **1000+ aliases** | Predefined aliases for common packages |
| **1055+ tests** | Comprehensive test coverage |

## What's New

### v0.1.0 (Current)

- **Phase 5 — Fake Code Audit & Fix**: All placeholder/fake code replaced with real logic
- **Fixed `assert True` tests**: 4 tests replaced with real assertions
- **Fixed silent `except Exception: pass`**: 4 tests, `HookList.__call__()`, `_benchmark.py` warmup/measure, `_state_setters.py` narrowed to `except ImportError`
- **Fixed 48 zero-assertion smoke tests**: Added type/value assertions
- **Fixed `_jupyter.py` `unload_ipython_extension()`**: No-op `pass` replaced with `unregister_magics()`
- **Fixed `_cache/_api.py` `invalidate_package_cache()`**: Added missing `_STDLIB_SYMBOL_CACHE` cleanup
- **Fixed circular import in `_build_known_modules_cache()`**: Skip scanning CWD (`''`/`'.'` paths) to prevent re-import of scripts in working directory
- **1055 tests**: All passing, comprehensive coverage

### v0.1.0-rc2

- **OOP API Migration**: 23 test files migrated from module-level API to `lz` singleton
- **Fixed `LazyImport.__getattr__`**: Negative cache check before expensive lookups
- **Fixed `reset_all()`**: Now reloads aliases, updates `__all__`, AND rebuilds symbol index
- **Raised `_build_symbol_index` defaults**: `max_modules=500`, `timeout=60.0` for complete index coverage

### v0.1.0-rc1

- **Phase 4 — Alias System Upgrade**: Data unification, JSON format upgrade, smart suggestions, filtered search, smart error hints, context-aware fuzzy matching, and conflict resolution
- **Data Unification**: 108 aliases merged from `mappings/abbreviations.json` into `aliases/*.json`; `abbreviations.json` and `submodules.json` removed
- **JSON Format Upgrade**: `_meta` metadata (category, description) added to all 27 alias letter files
- **AliasNamespace API**: `lz.alias.list(category=)`, `lz.alias.search(pattern, by_module=)`, `lz.alias.suggest(package=/installed=/pattern=)`
- **Smart Error Hints**: Typo detection with Levenshtein distance — `lz.nummpy` suggests `Did you mean numpy?`
- **Context-Aware Fuzzy Matching**: Loaded modules get priority bonus during auto-search
- **Conflict Detection**: `register_alias()` warns on alias overwrite
- **Bug Fixes**: Fixed `__repr__` NameError crash (critical); fixed alias search fallback importing wrong module (critical); fixed opencv/cv2 infinite cycle; fixed sage/sagemath pointing to non-existent module; fixed 4 circular alias chains; fixed 80+ hyphenated alias values (used PyPI names instead of importable module names); fixed 70+ hyphenated alias keys (unreachable via Python syntax); fixed indentation bug hiding symbol-not-found fallback; removed 48 lines of dead code; fixed `_suggest_for_package()` duplicate return bug
- **1055+ tests**: Comprehensive test coverage


---

## Examples

### Symbol Search & Location

```python
import laziest_import as lz

# Search for a symbol across all modules
results = lz.search_symbol('DataFrame')
for result in results:
 print(f"{result.module_name}.{result.symbol_name}")

# Find where a symbol is defined
loc = lz.which('sqrt')
print(f"Found at: {loc}") # numpy.sqrt

# Find all occurrences
locs = lz.which_all('sqrt')
for loc in locs:
 print(f"{loc.module_name}.{loc.symbol_name}")
```

### Dependency Tree Analysis

```python
import laziest_import as lz

# Analyze a module's dependency tree
tree = lz.dependency_tree('numpy', max_depth=2)
print(f"Total modules: {tree.total_modules}")
print(f"Stdlib: {tree.stdlib_count}, Third-party: {tree.third_party_count}")

# Print formatted tree
lz.print_dependency_tree(tree)
```

### Performance Benchmarking

```python
import laziest_import as lz

# Benchmark a function
result = lz.benchmark(
 lambda: sum(range(10000)),
 name="sum_test",
 iterations=100,
 warmup=10
)
print(f"Avg: {result.avg_time*1000:.4f}ms")
print(f"Min: {result.min_time*1000:.4f}ms")
print(f"Max: {result.max_time*1000:.4f}ms")

# Benchmark module imports
report = lz.benchmark_imports(['numpy', 'pandas', 'matplotlib'])
lz.print_benchmark_report(report)
```

### Strict Mode (Symbol Conflict Detection)

```python
from laziest_import import lz

# Enable strict mode
lz.symbol.config.strict = True

# Multiple modules define `sqrt` — raises AmbiguousSymbolError
# result = lz.sqrt  # Error: sqrt found in numpy, math, scipy, ...

# Use prefer() to resolve ambiguity
lz.symbol.prefer("sqrt", "numpy")
result = lz.sqrt(16)  # Now resolves to numpy.sqrt
```

### CLI: Freeze & Init

```bash
# Scan project and freeze alias usage
laziest-import freeze

# Generate .laziestrc config file
laziest-import init
```

The `freeze` command produces `imports.laziest.json` — a manifest of all lazy imports used across your project, ideal for CI validation.

### Auto-Install (Optional)

```python
from laziest_import import *

# Enable auto-install
lz.enable_auto_install()

# Accessing uninstalled modules triggers installation
arr = np.array([1, 2, 3]) # If numpy missing, prompts to install
```

---

## Configuration

### User Configuration

```python
import laziest_import as lz

# Create default config file
lz.create_rc_file()

# Load config
config = lz.load_rc_config()

# Get specific value
value = lz.get_rc_value('debug', default=False)

# Config info
info = lz.get_rc_info()
```

### Cache Configuration

```python
import laziest_import as lz

# Set custom cache directory
lz.set_cache_dir('./my_cache')

# Configure cache settings
lz.set_cache_config(
 symbol_index_ttl=3600, # Symbol index TTL: 1 hour
 stdlib_cache_ttl=2592000, # Stdlib cache TTL: 30 days
 max_cache_size_mb=200 # Max cache size: 200 MB
)

# Get cache statistics
stats = lz.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']:.1%}")

# View cache status
info = lz.get_file_cache_info()
print(f"Cache size: {info['cache_size_mb']:.2f} MB")
```

---

## API Reference

### Alias Management

| Function | Description |
|----------|-------------|
| `register_alias(alias, module_name)` | Register an alias |
| `register_aliases(dict)` | Register multiple aliases |
| `unregister_alias(alias)` | Remove an alias |
| `list_loaded()` | List loaded modules |
| `list_available()` | List all available aliases |
| `get_module(alias)` | Get module object |
| `clear_cache()` | Clear memory cache |

### Symbol Search

| Function | Description |
|----------|-------------|
| `enable_symbol_search()` | Enable symbol search |
| `disable_symbol_search()` | Disable symbol search |
| `search_symbol(name)` | Search for classes/functions |
| `rebuild_symbol_index()` | Rebuild symbol index |
| `which(symbol)` | Find symbol location |
| `which_all(symbol)` | Find all symbol locations |

### Auto-Install

| Function | Description |
|----------|-------------|
| `enable_auto_install()` | Enable auto-install |
| `disable_auto_install()` | Disable auto-install |
| `install_package(name)` | Install a package manually |
| `set_pip_index(url)` | Set mirror URL |

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

### Analysis & Profiling

| Function | Description |
|----------|-------------|
| `analyze_file(path)` | Analyze Python file for imports |
| `analyze_source(code)` | Analyze source code string |
| `analyze_directory(path)` | Analyze all files in directory |
| `start_profiling()` | Start import profiler |
| `stop_profiling()` | Stop import profiler |
| `get_profile_report()` | Get profiling report |
| `print_profile_report()` | Print formatted report |
| `dependency_tree(module)` | Analyze module dependency tree |
| `print_dependency_tree(tree)` | Print dependency tree |
| `benchmark(func)` | Benchmark a function |
| `benchmark_imports(modules)` | Benchmark module imports |
| `detect_environment()` | Detect Python environment |
| `show_environment()` | Display environment info |
| `find_symbol_conflicts()` | Find symbol conflicts |
| `show_conflicts()` | Display conflicts table |

### Preferences

| Function | Description |
|----------|-------------|
| `set_symbol_preference(name, module)` | Set symbol preference |
| `get_symbol_preference(name)` | Get symbol preference |
| `clear_symbol_preference(name)` | Clear symbol preference |
| `save_preferences()` | Save preferences to file |
| `load_preferences()` | Load preferences from file |
| `apply_preferences(prefs)` | Apply loaded preferences |
| `clear_preferences()` | Clear all preferences |

---

## Troubleshooting

### Common Issues

**Q: Module not found (AttributeError)**
```
AttributeError: module 'laziest_import' has no attribute 'mymodule'
```
Solution: The module is not registered. Use `lz.enable_auto_search()` to enable auto-discovery, or register it manually:
```python
lz.register_alias('mymodule', 'mypackage.mymodule')
```

**Q: Slow first import**
The symbol index may be building. Check status with:
```python
lz.is_index_building() # True if building
lz.wait_for_index(30) # Wait up to 30 seconds
```

**Q: Typo correction not working**
Ensure the module is in the alias list:
```python
lz.register_alias('nump', 'numpy') # Add misspelling
arr = lz.nump.array([1, 2, 3]) # Now works
```

**Q: Symbol conflicts (same name in multiple modules)**
Use module hints or preferences:
```python
lz.set_symbol_preference('DataFrame', 'pandas') # Prefer pandas
result = lz.DataFrame # Gets pandas.DataFrame
```

### Debug Mode

Enable detailed logging:
```python
lz.enable_debug_mode()
import laziest_import as lz
arr = lz.np.array([1, 2, 3]) # See import details in logs
```

### Cache Issues

Clear caches if experiencing stale data:
```python
lz.clear_cache() # Clear memory cache
lz.clear_file_cache() # Clear disk cache
lz.rebuild_symbol_index() # Rebuild symbol index
```

### Performance Tips

1. **First run**: ~2s to build index
2. **Cached run**: ~0.003s (700x faster!)
3. Use `lz.enable_background_build()` to avoid blocking on first import
4. For CI/CD, set `LAZY_BG_BUILD=1` to pre-build cache

---

## How It Works

### Architecture

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

---

## Predefined Aliases

### Data Science
`np`, `pd`, `plt`, `sns`, `scipy`

### Machine Learning
`torch`, `tf`, `keras`, `sklearn`, `xgboost`, `lightgbm`

### Deep Learning
`transformers`, `langchain`, `llama_index`

### Web Frameworks
`flask`, `django`, `fastapi`, `starlette`

### HTTP Clients
`requests`, `httpx`, `aiohttp`

### Databases
`sqlalchemy`, `pymongo`, `redis`, `duckdb`

### Cloud Services
`boto3` (AWS), `google.cloud`, `azure`

### Image Processing
`cv2`, `PIL.Image`, `skimage`

### GUI
`PyQt6`, `tkinter`, `flet`, `nicegui`

### DevOps
`docker`, `kubernetes`, `ansible`

### NLP
`spacy`, `nltk`, `transformers`

### Visualization
`plotly`, `bokeh`, `streamlit`, `gradio`

---

## Contributing

We love contributions! Check out our [Contributing Guide](CONTRIBUTING.md) for more information.

### How to Contribute

1. Fork the repo and create your branch from `main`
2. Read our [Code of Conduct](CODE_OF_CONDUCT.md)
3. Make sure your code lints (`flake8`)
4. Add tests for any new functionality
5. Ensure the test suite passes (`pytest tests/`)
6. Commit your changes
7. Push to your branch and open a Pull Request!

### Development Setup

```bash
# Clone the repo
git clone https://github.com/ChidcGithub/Laziest-import.git
cd Laziest-import

# Install in development mode
pip install -e ".[dev,test]"

# Run tests
pytest tests/ -v

# Run linting
flake8 laziest_import/
```

### Good First Issues

Looking for a place to start? Check out:
- Good first issues: [Issues labeled "good first issue"](https://github.com/ChidcGithub/Laziest-import/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
- Help wanted: [Issues labeled "help wanted"](https://github.com/ChidcGithub/Laziest-import/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22)

### Ways to Contribute

- Report bugs
- Propose new features
- Improve documentation
- Fix existing issues
- Add more tests
- Help with translations
- Design improvements

---

## Contributors

Thanks goes to these wonderful people:

<a href="https://github.com/ChidcGithub/Laziest-import/graphs/contributors">
 <img src="https://contrib.rocks/image?repo=ChidcGithub/Laziest-import" />
</a>

Made with [contrib.rocks](https://contrib.rocks).

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ChidcGithub/Laziest-import&type=Date)](https://star-history.com/#ChidcGithub/Laziest-import&Date)

---

## Get In Touch

- Email: (your email)
- GitHub: [ChidcGithub/Laziest-import](https://github.com/ChidcGithub/Laziest-import)
- Discussions: [GitHub Discussions](https://github.com/ChidcGithub/Laziest-import/discussions)
- Issues: [GitHub Issues](https://github.com/ChidcGithub/Laziest-import/issues)

---

## Acknowledgments

- Thanks to all the contributors who have helped make this project better!
- Inspired by the Python community's love for clean, simple APIs

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Show Your Support

If you find this project useful, please consider:

- Starring this repo on GitHub
- Reporting bugs or suggesting features
- Sharing it with friends and colleagues
- Blogging about it if you use it
- Contributing to the project

Thank you!

---

<div align="center">
 <b>Made by Chidc and contributors with LOVE</b>
</div>
