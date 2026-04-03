# laziest-import

A Python library for automatic lazy importing. Import the library once, then use any installed module without explicit import statements.

## Installation

```bash
pip install laziest-import
```

Or install from source:

```bash
git clone https://github.com/yourusername/laziest-import.git
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
```

### Method 2: Namespace Prefix

```python
import laziest_import as lz

arr = lz.np.array([1, 2, 3])
df = lz.pd.DataFrame({'a': [1, 2]})
```

## Features

### Lazy Loading

Modules are only imported when first accessed, not at import time. This reduces startup overhead and memory usage.

### Module Caching

Each module is imported exactly once. Subsequent accesses return the cached module object.

### Auto-Discovery

When accessing an unregistered name, the library automatically searches for matching installed modules:

```python
import laziest_import as lz

# flask is not pre-registered, but auto-discovered
app = lz.flask.Flask(__name__)
```

Auto-discovery matching rules:
- Exact match (case-insensitive)
- Underscore/hyphen variants (`my_lib` matches `mylib`)
- Prefix match for names with 4+ characters

### Custom Aliases

Register your own module aliases:

```python
from laziest_import import *

register_alias("mylib", "my_awesome_library")

# Now you can use it directly
result = mylib.some_function()
```

## API Reference

### Functions

| Function | Description |
|----------|-------------|
| `register_alias(alias, module_name)` | Register a custom alias |
| `unregister_alias(alias)` | Remove a registered alias |
| `list_loaded()` | Return list of loaded module aliases |
| `list_available()` | Return list of all registered aliases |
| `get_module(alias)` | Get a loaded module object |
| `clear_cache()` | Clear module cache |
| `enable_auto_search()` | Enable auto-discovery |
| `disable_auto_search()` | Disable auto-discovery |
| `is_auto_search_enabled()` | Check auto-discovery status |
| `search_module(name)` | Search for a module by name |
| `rebuild_module_cache()` | Rebuild the module cache |

## Predefined Aliases

### Data Science

| Alias | Module |
|-------|--------|
| `np` | numpy |
| `pd` | pandas |
| `plt` | matplotlib.pyplot |
| `mpl` | matplotlib |
| `sns` | seaborn |

### Machine Learning

| Alias | Module |
|-------|--------|
| `sklearn` | sklearn |
| `torch` | torch |
| `tf` | tensorflow |
| `keras` | keras |

### Standard Library

| Alias | Module |
|-------|--------|
| `os`, `sys`, `re`, `json`, `csv` | os, sys, re, json, csv |
| `datetime`, `pathlib`, `math` | datetime, pathlib, math |
| `random`, `time`, `asyncio` | random, time, asyncio |
| `collections`, `itertools`, `functools` | collections, itertools, functools |

### Web & Network

| Alias | Module |
|-------|--------|
| `requests` | requests |
| `httpx` | httpx |
| `bs4` | bs4 (BeautifulSoup) |

### Image Processing

| Alias | Module |
|-------|--------|
| `Image` | PIL.Image |
| `cv2` | cv2 (OpenCV) |

## How It Works

1. **LazyModule Proxy**: Each alias maps to a `LazyModule` proxy object
2. **On-Demand Import**: The actual module is imported when first accessed via `__getattr__`
3. **Caching**: Imported modules are cached in the proxy for subsequent access
4. **Auto-Discovery**: Uses `importlib.util.find_spec()` and searches `sys.path` for unregistered names

## Error Handling

If a module cannot be imported, an `ImportError` is raised with a clear message:

```python
>>> import laziest_import as lz
>>> lz.nonexistent_module
ImportError: Cannot import module 'nonexistent_module'. 
Please ensure it is installed: pip install nonexistent_module
```

## Requirements

- Python 3.8+

## License

MIT License