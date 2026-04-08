"""
Module introspection utilities.
Provides ways to explore module contents without fully importing them.
"""

from typing import List, Dict, Set, Optional, Any
import importlib
import inspect
import sys
import pkgutil
import os


def list_module_symbols(
    module_name: str,
    include_private: bool = False,
    include_submodules: bool = True,
    filter_types: Optional[Set[str]] = None,
) -> List[str]:
    """
    List symbols available in a module without fully importing it.

    Args:
        module_name: Name of the module (e.g., 'numpy', 'os.path')
        include_private: Include symbols starting with '_'
        include_submodules: Include submodule names
        filter_types: Filter by types ('function', 'class', 'constant', 'module')

    Returns:
        List of symbol names

    Example:
        >>> list_module_symbols('math')
        ['acos', 'acosh', 'asin', ...]
        >>> list_module_symbols('numpy', filter_types={'class'})
        ['ndarray', 'Matrix', ...]
    """
    filter_types = filter_types or set()

    try:
        mod = importlib.import_module(module_name)
    except ImportError:
        return []

    symbols: List[str] = []
    seen: Set[str] = set()

    for attr_name in dir(mod):
        if attr_name in seen:
            continue
        seen.add(attr_name)

        if not include_private and attr_name.startswith("_"):
            continue

        try:
            attr = getattr(mod, attr_name, None)
            if attr is None:
                continue

            obj_type = _get_symbol_type(attr)

            if filter_types and obj_type not in filter_types:
                continue

            symbols.append(attr_name)

        except (ImportError, AttributeError):
            continue

    if include_submodules:
        symbols.extend(_get_submodules(module_name))

    return sorted(symbols)


def get_module_info(module_name: str) -> Dict[str, Any]:
    """
    Get information about a module.

    Args:
        module_name: Name of the module

    Returns:
        Dictionary with module info (name, path, doc, symbols count)

    Example:
        >>> info = get_module_info('json')
        >>> info['name']
        'json'
        >>> info['path']
        '/path/to/python/lib/json/__init__.py'
    """
    result: Dict[str, Any] = {
        "name": module_name,
        "path": None,
        "doc": None,
        "symbols_count": 0,
        "is_package": False,
        "version": None,
    }

    try:
        mod = importlib.import_module(module_name)
        result["doc"] = inspect.getdoc(mod)
        result["symbols_count"] = len(dir(mod))
        result["is_package"] = hasattr(mod, "__path__")

        if hasattr(mod, "__version__"):
            result["version"] = getattr(mod, "__version__")
        elif hasattr(mod, "version"):
            result["version"] = getattr(mod, "version")

        try:
            result["path"] = importlib.util.find_spec(module_name)
            if result["path"]:
                result["path"] = result["path"].origin
        except (ValueError, AttributeError):
            pass

    except ImportError:
        pass

    return result


def _get_submodules(module_name: str) -> List[str]:
    """Get submodule names for a package."""
    submodules: List[str] = []

    try:
        mod = importlib.import_module(module_name)

        if not hasattr(mod, "__path__"):
            return []

        package_path = getattr(mod, "__path__")
        if not package_path:
            return []

        pkg_name = module_name

        for importer, name, ispkg in pkgutil.iter_modules(package_path, f"{pkg_name}."):
            submodules.append(name.split(".")[-1])

    except (ImportError, AttributeError):
        pass

    return submodules


def _get_symbol_type(obj: Any) -> str:
    """Get the type category of an object."""
    import inspect

    if inspect.ismodule(obj):
        return "module"
    elif inspect.isclass(obj):
        return "class"
    elif inspect.isfunction(obj) or inspect.isbuiltin(obj):
        return "function"
    elif inspect.ismethod(obj):
        return "method"
    elif callable(obj):
        return "callable"
    else:
        return "constant"


def search_in_module(module_name: str, pattern: str) -> List[str]:
    """
    Search for symbols matching a pattern in a module.

    Args:
        module_name: Name of the module
        pattern: Search pattern (substring match)

    Returns:
        List of matching symbol names

    Example:
        >>> search_in_module('math', 'sin')
        ['asin', 'sinh', 'sin']
    """
    symbols = list_module_symbols(module_name)
    pattern_lower = pattern.lower()
    return [s for s in symbols if pattern_lower in s.lower()]
