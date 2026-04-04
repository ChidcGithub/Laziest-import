# laziest-import

[![PyPI version](https://img.shields.io/pypi/v/laziest-import.svg)](https://pypi.org/project/laziest-import/)
[![Python](https://img.shields.io/pypi/pyversions/laziest-import.svg)](https://pypi.org/project/laziest-import/)
[![License](https://img.shields.io/github/license/ChidcGithub/Laziest-import.svg)](LICENSE)

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

</details>

## Key Features

| Feature | Description |
|---------|-------------|
| **Lazy loading** | Modules import only on first access, reducing startup overhead |
| **Submodule support** | `np.linalg.svd()` chains submodules automatically |
| **Auto-discovery** | Unregistered names search installed modules automatically |
| **Fuzzy matching** | Typo correction via Levenshtein distance algorithm |
| **Auto-install** | Optional: missing modules can be pip-installed automatically |
| **1000+ aliases** | Predefined aliases for common packages |

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

# Set custom cache directory
lz.set_cache_dir('./my_cache')

# Clear cache
lz.clear_file_cache()
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

</details>

## Configuration

Custom aliases can be configured in:

1. `~/.laziest_import/aliases.json` (user global)
2. `./.laziest_import.json` (project level)

```json
{
    "mylib": "my_awesome_library",
    "api": "my_api_client"
}
```

## How It Works

1. **Proxy objects**: Each alias maps to a `LazyModule` proxy
2. **On-demand import**: Real import triggers on first attribute access via `__getattr__`
3. **Caching**: Imported modules cache within the proxy object
4. **Chain proxies**: `LazySubmodule` handles recursive lazy loading
5. **Fuzzy search**: Levenshtein distance algorithm for fault-tolerant matching

## Requirements

- Python 3.8+

## License

[MIT](LICENSE)
