# laziest-import

A Python library for automatic lazy importing. Import the library once, then use any installed module without explicit import statements.

## Installation

```bash
pip install laziest-import
```

Or install from source:

```bash
git clone https://github.com/ChidcGithub/Laziest-import.git
cd laziest-import
pip install -e .
```

## Quick Start

### Method 1: Wildcard Import (Recommended)

```python
from laziest_import import *

# Use common libraries without import statements
arr = np.array([1, 2, 3])           # numpy
df = pd.DataFrame({'a': [1, 2]})    # pandas
plt.plot([1, 2, 3])                 # matplotlib.pyplot
plt.show()

# Standard library modules
print(os.getcwd())                  # os
data = json.dumps({'key': 'value'}) # json

# Submodule lazy loading
result = np.linalg.svd(matrix)      # numpy.linalg
```

### Method 2: Namespace Prefix

```python
import laziest_import as lz

arr = lz.np.array([1, 2, 3])
df = lz.pd.DataFrame({'a': [1, 2]})

# Submodule access
norm = lz.np.linalg.norm([1, 2, 3])
```

## Features

### Lazy Loading

Modules are only imported when first accessed, not at import time. This reduces startup overhead and memory usage.

### Submodule Lazy Loading

Access submodules without explicit imports - they're loaded on demand:

```python
from laziest_import import *

# All these work without explicit imports
np.linalg.svd(matrix)        # numpy.linalg
pd.read_csv('file.csv')      # pandas
torch.nn.Linear(10, 5)       # torch.nn
sklearn.ensemble.RandomForestClassifier()  # sklearn.ensemble
```

### Module Caching

Each module is imported exactly once. Subsequent accesses return the cached module object.

### Auto-Discovery with Fuzzy Matching

When accessing an unregistered name, the library automatically searches for matching installed modules:

```python
import laziest_import as lz

# flask is not pre-registered, but auto-discovered
app = lz.flask.Flask(__name__)
```

Auto-discovery matching rules:
- Exact match (case-insensitive)
- **Levenshtein distance** fuzzy matching for typos
- Abbreviation expansion (`np` → `numpy`)
- Package rename mapping (`sklearn` → `scikit-learn`)
- Underscore/hyphen variants (`my_lib` matches `mylib`)
- Prefix match for names with 4+ characters

### 1000+ Predefined Aliases

Built-in aliases for popular packages across 50+ categories:

| Category | Examples |
|----------|----------|
| Data Science | `np`, `pd`, `plt`, `sns`, `scipy` |
| Machine Learning | `torch`, `tf`, `keras`, `sklearn`, `xgboost` |
| Deep Learning | `transformers`, `langchain`, `llama_index` |
| Web Frameworks | `flask`, `django`, `fastapi`, `starlette` |
| HTTP Clients | `requests`, `httpx`, `aiohttp` |
| Database | `sqlalchemy`, `pymongo`, `redis`, `duckdb` |
| Cloud | `boto3` (AWS), `google.cloud`, `azure` |
| Image Processing | `cv2`, `PIL.Image`, `skimage` |
| GUI | `PyQt6`, `tkinter`, `flet`, `nicegui` |
| DevOps | `docker`, `kubernetes`, `ansible` |
| NLP | `spacy`, `nltk`, `transformers` |
| Visualization | `plotly`, `bokeh`, `streamlit`, `gradio` |

### File-Level Caching

Cache module imports per file for faster subsequent runs:

```python
import laziest_import as lz

# Check cache status
info = lz.get_file_cache_info()
print(info)  # {'enabled': True, 'cached_modules': ['numpy', 'pandas'], ...}

# Configure cache directory
lz.set_cache_dir('./my_cache')

# Clear cache
lz.clear_file_cache()
```

### Debug Mode & Import Statistics

Track import performance:

```python
import laziest_import as lz

# Enable debug mode
lz.enable_debug_mode()

# After some imports...
arr = lz.np.array([1, 2, 3])

# Get statistics
stats = lz.get_import_stats()
print(stats)
# {'total_imports': 1, 'total_time': 0.023, 'module_times': {'numpy': 0.023}, ...}

# Reset statistics
lz.reset_import_stats()
```

### Import Hooks

Add custom callbacks before/after imports:

```python
import laziest_import as lz

def before_import(module_name):
    print(f"About to import: {module_name}")

def after_import(module_name, module):
    print(f"Imported: {module_name}")

lz.add_pre_import_hook(before_import)
lz.add_post_import_hook(after_import)
```

### Async Import

Import modules asynchronously:

```python
import laziest_import as lz
import asyncio

async def main():
    # Import multiple modules in parallel
    modules = await lz.import_multiple_async(['numpy', 'pandas', 'matplotlib'])
    np, pd, plt = modules['numpy'], modules['pandas'], modules['matplotlib']

asyncio.run(main())
```

### Retry Mechanism

Retry failed imports automatically:

```python
import laziest_import as lz

# Enable retry with custom settings
lz.enable_retry(max_retries=3, retry_delay=0.5)

# Now imports will be retried on failure
import laziest_import as lz
arr = lz.np.array([1, 2, 3])  # Will retry up to 3 times if import fails
```

### Custom Aliases

Register your own module aliases:

```python
from laziest_import import *

register_alias("mylib", "my_awesome_library")

# Now you can use it directly
result = mylib.some_function()

# Register multiple at once
register_aliases({
    "api": "my_api_client",
    "db": "my_database_lib",
})
```

## API Reference

### Alias Management

| Function | Description |
|----------|-------------|
| `register_alias(alias, module_name)` | Register a custom alias |
| `register_aliases(aliases_dict)` | Register multiple aliases |
| `unregister_alias(alias)` | Remove a registered alias |
| `list_loaded()` | Return list of loaded module aliases |
| `list_available()` | Return list of all registered aliases |
| `get_module(alias)` | Get a loaded module object |
| `clear_cache()` | Clear module cache |

### Version & Reload

| Function | Description |
|----------|-------------|
| `get_version(alias)` | Get version of a loaded module |
| `reload_module(alias)` | Reload a module |

### Auto-Search

| Function | Description |
|----------|-------------|
| `enable_auto_search()` | Enable auto-discovery |
| `disable_auto_search()` | Disable auto-discovery |
| `is_auto_search_enabled()` | Check auto-discovery status |
| `search_module(name)` | Search for a module by name |
| `search_class(class_name)` | Search module by class name |
| `rebuild_module_cache()` | Rebuild the module cache |

### Debug & Statistics

| Function | Description |
|----------|-------------|
| `enable_debug_mode()` | Enable debug logging |
| `disable_debug_mode()` | Disable debug logging |
| `is_debug_mode()` | Check debug mode status |
| `get_import_stats()` | Get import statistics |
| `reset_import_stats()` | Reset statistics |

### Import Hooks

| Function | Description |
|----------|-------------|
| `add_pre_import_hook(callback)` | Add pre-import callback |
| `add_post_import_hook(callback)` | Add post-import callback |
| `remove_pre_import_hook(callback)` | Remove pre-import callback |
| `remove_post_import_hook(callback)` | Remove post-import callback |
| `clear_import_hooks()` | Remove all hooks |

### Async Import

| Function | Description |
|----------|-------------|
| `import_async(module_name)` | Import a module asynchronously |
| `import_multiple_async(names)` | Import multiple modules async |

### Retry Configuration

| Function | Description |
|----------|-------------|
| `enable_retry(max_retries, retry_delay)` | Enable retry mechanism |
| `disable_retry()` | Disable retry mechanism |
| `is_retry_enabled()` | Check retry status |

### File Cache

| Function | Description |
|----------|-------------|
| `enable_file_cache()` | Enable file-level caching |
| `disable_file_cache()` | Disable file-level caching |
| `is_file_cache_enabled()` | Check cache status |
| `clear_file_cache()` | Clear all cached data |
| `get_file_cache_info()` | Get cache information |
| `force_save_cache()` | Force save cache to disk |
| `set_cache_dir(path)` | Set custom cache directory |
| `get_cache_dir()` | Get current cache directory |
| `reset_cache_dir()` | Reset to default cache directory |

## Configuration

Custom aliases can be defined in:

1. `~/.laziest_import/aliases.json` (user global)
2. `./.laziest_import.json` (project level)

Example config file:
```json
{
    "mylib": "my_awesome_library",
    "api": "my_api_client"
}
```

## How It Works

1. **LazyModule Proxy**: Each alias maps to a `LazyModule` proxy object
2. **On-Demand Import**: The actual module is imported when first accessed via `__getattr__`
3. **Caching**: Imported modules are cached in the proxy for subsequent access
4. **Submodule Proxy**: `LazySubmodule` handles recursive lazy loading for submodules
5. **Auto-Discovery**: Uses `importlib.util.find_spec()` and searches `sys.path` for unregistered names
6. **Fuzzy Matching**: Levenshtein distance algorithm for typo-tolerant module search

## Error Handling

If a module cannot be imported, an `ImportError` is raised with a clear message:

```python
>>> import laziest_import as lz
>>> lz.nonexistent_module
AttributeError: module 'laziest_import' has no attribute 'nonexistent_module'. 
Available modules: ['np', 'numpy', 'pd', 'pandas', ...] (use list_available() to see all)
```

## Type Stubs

Type stubs (`.pyi`) are included for IDE autocomplete and type checking support.

## Requirements

- Python 3.8+

## License

MIT License
