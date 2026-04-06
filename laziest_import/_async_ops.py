"""
Async operations for laziest-import.
"""

from typing import Any, Dict, List, Optional, Set
import asyncio
import importlib
import logging

from ._config import (
    _DEBUG_MODE,
    _ALIAS_MAP,
    _LAZY_MODULES,
    _RETRY_CONFIG,
)
from ._fuzzy import _search_module


async def import_async(alias: str) -> Any:
    """
    Asynchronously import a module.
    
    Useful for importing large modules without blocking the event loop.
    
    Args:
        alias: Module alias to import
        
    Returns:
        The imported module object
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    def _sync_import():
        if alias in _LAZY_MODULES:
            return _LAZY_MODULES[alias]._get_module()
        
        module_name = _ALIAS_MAP.get(alias, alias)
        try:
            return importlib.import_module(module_name)
        except ImportError:
            found = _search_module(alias)
            if found:
                return importlib.import_module(found)
            raise
    
    return await loop.run_in_executor(None, _sync_import)


async def import_multiple_async(aliases: List[str]) -> Dict[str, Any]:
    """
    Asynchronously import multiple modules in parallel.
    
    Args:
        aliases: List of module aliases to import
        
    Returns:
        Dictionary mapping alias to module object
    """
    tasks = [import_async(alias) for alias in aliases]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    modules = {}
    for alias, result in zip(aliases, results):
        if isinstance(result, Exception):
            if _DEBUG_MODE:
                logging.warning(f"Failed to import {alias}: {result}")
        else:
            modules[alias] = result
    
    return modules


def enable_retry(
    max_retries: int = 3,
    retry_delay: float = 0.5,
    modules: Optional[Set[str]] = None
) -> None:
    """
    Enable automatic retry for module imports.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        modules: Set of module names to retry. If None, retry all modules.
    """
    _RETRY_CONFIG["enabled"] = True
    _RETRY_CONFIG["max_retries"] = max_retries
    _RETRY_CONFIG["retry_delay"] = retry_delay
    _RETRY_CONFIG["retry_modules"] = modules if modules else set()


def disable_retry() -> None:
    """Disable automatic retry for module imports."""
    _RETRY_CONFIG["enabled"] = False


def is_retry_enabled() -> bool:
    """Check if retry is enabled."""
    return _RETRY_CONFIG["enabled"]
