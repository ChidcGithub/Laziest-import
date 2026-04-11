"""
LazyModule class for lazy loading modules.
"""

from typing import Any, List
import sys
import time
import logging
import importlib
import asyncio
from types import ModuleType

from .._config import (
    _DEBUG_MODE,
    _AUTO_SEARCH_ENABLED,
    _AUTO_INSTALL_CONFIG,
    _IMPORT_STATS,
    _CACHE_STATS,
    _RETRY_CONFIG,
    _PRE_IMPORT_HOOKS,
    _POST_IMPORT_HOOKS,
    _ALIAS_MAP,
    get_importing_modules,
)
from .._cache import _record_module_load
from .._fuzzy import _search_module
from ._submodule import LazySubmodule


class LazyModule:
    """
    Lazy loading module proxy class.
    
    Imports the actual module only when attributes are accessed.
    Supports auto-search for unregistered modules and submodule lazy loading.
    """
    
    __slots__ = ('_alias', '_module_name', '_cached_module', '_auto_searched', '_submodule_cache')
    
    def __init__(self, alias: str, module_name: str, auto_searched: bool = False):
        object.__setattr__(self, '_alias', alias)
        object.__setattr__(self, '_module_name', module_name)
        object.__setattr__(self, '_cached_module', None)
        object.__setattr__(self, '_auto_searched', auto_searched)
        object.__setattr__(self, '_submodule_cache', {})
    
    def _get_module(self) -> Any:
        """Get the actual module (lazy load)"""
        cached = object.__getattribute__(self, '_cached_module')
        if cached is not None:
            alias = object.__getattribute__(self, '_alias')
            _IMPORT_STATS.module_access_counts[alias] = _IMPORT_STATS.module_access_counts.get(alias, 0) + 1
            _CACHE_STATS["module_hits"] += 1
            return cached
        
        _CACHE_STATS["module_misses"] += 1
        
        module_name = object.__getattribute__(self, '_module_name')
        alias = object.__getattribute__(self, '_alias')
        
        importing_modules = get_importing_modules()
        if module_name in importing_modules:
            return importlib.import_module(module_name)
        
        importing_modules.add(module_name)
        
        try:
            for hook in _PRE_IMPORT_HOOKS:
                try:
                    hook(module_name)
                except Exception as e:
                    if _DEBUG_MODE:
                        logging.warning(f"Pre-import hook failed for {module_name}: {e}")
            
            start_time = time.perf_counter()
            
            def _do_import(name: str) -> Any:
                """Internal import function with retry support."""
                if not _RETRY_CONFIG["enabled"]:
                    return importlib.import_module(name)
                
                max_retries = _RETRY_CONFIG["max_retries"]
                retry_delay = _RETRY_CONFIG["retry_delay"]
                retry_modules = _RETRY_CONFIG["retry_modules"]
                
                if retry_modules and name.split('.')[0] not in retry_modules:
                    return importlib.import_module(name)
                
                # Check if we're in an async context to avoid blocking
                in_async_context = False
                try:
                    loop = asyncio.get_running_loop()
                    in_async_context = loop is not None
                except RuntimeError:
                    pass
                
                # In async context, disable retry with sleep to avoid blocking event loop
                if in_async_context:
                    if _DEBUG_MODE:
                        logging.debug(
                            f"[laziest-import] In async context, disabling retry for '{name}' "
                            f"(sleep would block event loop)"
                        )
                    return importlib.import_module(name)
                
                last_error = None
                for attempt in range(max_retries + 1):
                    try:
                        return importlib.import_module(name)
                    except ImportError as e:
                        last_error = e
                        if attempt < max_retries:
                            if _DEBUG_MODE:
                                logging.info(f"Retry {attempt + 1}/{max_retries} for {name}")
                            time.sleep(retry_delay)
                raise last_error
            
            try:
                # Measure memory before import
                # Only use tracemalloc if it's already running to avoid
                # interfering with user's own tracemalloc configuration
                try:
                    import tracemalloc
                    if tracemalloc.is_tracing():
                        mem_before = tracemalloc.get_traced_memory()[0]
                    else:
                        mem_before = 0
                except Exception:
                    mem_before = 0

                module = _do_import(module_name)

                elapsed = time.perf_counter() - start_time

                # Measure memory after import
                try:
                    import tracemalloc
                    if tracemalloc.is_tracing():
                        mem_after = tracemalloc.get_traced_memory()[0]
                        mem_delta = max(0, mem_after - mem_before)
                    else:
                        mem_delta = 0
                except Exception:
                    mem_delta = 0
                
                _IMPORT_STATS.total_imports += 1
                _IMPORT_STATS.total_time += elapsed
                _IMPORT_STATS.module_times[module_name] = elapsed
                _IMPORT_STATS.module_access_counts[alias] = 1
                
                _record_module_load(module_name)
                
                # Record for profiler
                from .._analysis import _profiler
                if _profiler.is_active():
                    _profiler.record_load(module_name, elapsed, mem_delta)
                
                object.__setattr__(self, '_cached_module', module)
                
                for hook in _POST_IMPORT_HOOKS:
                    try:
                        hook(module_name, module)
                    except Exception as e:
                        if _DEBUG_MODE:
                            logging.warning(f"Post-import hook failed for {module_name}: {e}")
                
                if _DEBUG_MODE:
                    logging.info(f"[laziest-import] Loaded module '{module_name}' in {elapsed*1000:.2f}ms")
                
                return module
            except ImportError as e:
                auto_searched = object.__getattribute__(self, '_auto_searched')
                if _AUTO_SEARCH_ENABLED and not auto_searched:
                    found_name = _search_module(alias)
                    if found_name and found_name != module_name:
                        try:
                            module = _do_import(found_name)
                            object.__setattr__(self, '_module_name', found_name)
                            object.__setattr__(self, '_cached_module', module)
                            object.__setattr__(self, '_auto_searched', True)
                            _ALIAS_MAP[alias] = found_name
                            
                            elapsed = time.perf_counter() - start_time
                            _IMPORT_STATS.total_imports += 1
                            _IMPORT_STATS.total_time += elapsed
                            _IMPORT_STATS.module_times[found_name] = elapsed
                            
                            return module
                        except ImportError:
                            pass
                
                if _AUTO_INSTALL_CONFIG["enabled"]:
                    from .._install import _get_pip_package_name, _install_package_sync, _interactive_install_confirm, rebuild_module_cache
                    
                    pip_package = _get_pip_package_name(module_name)
                    
                    should_install = True
                    if _AUTO_INSTALL_CONFIG["interactive"]:
                        should_install = _interactive_install_confirm(module_name, pip_package)
                    
                    if should_install:
                        success, message = _install_package_sync(
                            pip_package,
                            index=_AUTO_INSTALL_CONFIG["index"],
                            extra_args=_AUTO_INSTALL_CONFIG["extra_args"],
                            prefer_uv=_AUTO_INSTALL_CONFIG["prefer_uv"],
                            silent=_AUTO_INSTALL_CONFIG["silent"]
                        )
                        
                        if success:
                            if _DEBUG_MODE:
                                logging.info(f"[laziest-import] {message}")
                            
                            rebuild_module_cache()
                            
                            try:
                                module = _do_import(module_name)
                                
                                elapsed = time.perf_counter() - start_time
                                _IMPORT_STATS.total_imports += 1
                                _IMPORT_STATS.total_time += elapsed
                                _IMPORT_STATS.module_times[module_name] = elapsed
                                _IMPORT_STATS.module_access_counts[alias] = 1
                                
                                _record_module_load(module_name)
                                
                                object.__setattr__(self, '_cached_module', module)
                                
                                return module
                            except ImportError as import_error:
                                raise ImportError(
                                    f"Module '{module_name}' was installed but still cannot be imported. "
                                    f"Error: {import_error}"
                                ) from import_error
                
                raise ImportError(
                    f"Cannot import module '{module_name}' (alias '{alias}'). "
                    f"Please ensure the module is installed: pip install {module_name.split('.')[0]}"
                ) from e
        finally:
            importing_modules.discard(module_name)
    
    def __getattr__(self, name: str) -> Any:
        if name.startswith('_'):
            allowed_dunder = {'__name__', '__file__', '__path__', '__package__',
                             '__loader__', '__spec__', '__doc__', '__version__'}
            if name not in allowed_dunder:
                raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        
        module = self._get_module()
        attr = getattr(module, name)
        
        if isinstance(attr, ModuleType):
            submodule_cache = object.__getattribute__(self, '_submodule_cache')
            # Use full_name as cache key to avoid conflicts between different parent modules
            full_name = f"{object.__getattribute__(self, '_module_name')}.{name}"
            if full_name not in submodule_cache:
                submodule_cache[full_name] = LazySubmodule(full_name, self, name)
            return submodule_cache[full_name]
        
        return attr
    
    def __dir__(self) -> List[str]:
        module = self._get_module()
        return dir(module)
    
    def __repr__(self) -> str:
        module_name = object.__getattribute__(self, '_module_name')
        cached = object.__getattribute__(self, '_cached_module')
        if cached is not None:
            return f"<LazyModule '{module_name}' (loaded)>"
        return f"<LazyModule '{module_name}' (not loaded)>"
    
    def __call__(self, *args, **kwargs) -> Any:
        module = self._get_module()
        if callable(module):
            return module(*args, **kwargs)
        module_name = object.__getattribute__(self, '_module_name')
        raise TypeError(f"Module '{module_name}' ({type(module).__name__}) is not callable")
