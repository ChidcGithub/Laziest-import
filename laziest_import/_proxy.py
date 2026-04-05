"""
Proxy classes for lazy loading modules and symbols.
"""

from typing import Any, Dict, List, Optional, Union
import sys
import time
import logging
import importlib
import asyncio
from types import ModuleType

from ._config import (
    _DEBUG_MODE,
    _AUTO_SEARCH_ENABLED,
    _AUTO_INSTALL_CONFIG,
    _IMPORT_STATS,
    _CACHE_STATS,
    _RETRY_CONFIG,
    _PRE_IMPORT_HOOKS,
    _POST_IMPORT_HOOKS,
    _ALIAS_MAP,
    _LAZY_MODULES,
    _SYMBOL_CACHE,
    get_importing_modules,
)
from ._cache import _record_module_load
from ._fuzzy import _search_module
from ._alias import _lookup_alias_fast, _build_known_modules_cache


class LazySymbol:
    """
    Lazy loading symbol proxy class.
    
    Imports the actual symbol (class/function) from a module when accessed.
    Supports transparent usage as the underlying class/function.
    """
    
    __slots__ = ('_symbol_name', '_module_name', '_symbol_type', '_cached_obj', '_loaded')
    
    def __init__(self, symbol_name: str, module_name: str, symbol_type: str = 'class'):
        object.__setattr__(self, '_symbol_name', symbol_name)
        object.__setattr__(self, '_module_name', module_name)
        object.__setattr__(self, '_symbol_type', symbol_type)
        object.__setattr__(self, '_cached_obj', None)
        object.__setattr__(self, '_loaded', False)
    
    def _get_object(self) -> Any:
        """Get the actual symbol object (lazy load)."""
        cached = object.__getattribute__(self, '_cached_obj')
        if cached is not None:
            return cached
        
        symbol_name = object.__getattribute__(self, '_symbol_name')
        module_name = object.__getattribute__(self, '_module_name')
        
        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            raise ImportError(
                f"Cannot import module '{module_name}' for symbol '{symbol_name}': {e}"
            ) from e
        
        obj = getattr(module, symbol_name, None)
        if obj is None:
            raise AttributeError(
                f"Module '{module_name}' has no attribute '{symbol_name}'"
            )
        
        object.__setattr__(self, '_cached_obj', obj)
        object.__setattr__(self, '_loaded', True)
        
        if symbol_name not in _SYMBOL_CACHE:
            _SYMBOL_CACHE[symbol_name] = []
        
        _IMPORT_STATS.total_imports += 1
        _IMPORT_STATS.module_access_counts[module_name] = _IMPORT_STATS.module_access_counts.get(module_name, 0) + 1
        
        if _DEBUG_MODE:
            logging.info(
                f"[laziest-import] Loaded symbol '{symbol_name}' from '{module_name}'"
            )
        
        return obj
    
    def __getattr__(self, name: str) -> Any:
        obj = self._get_object()
        return getattr(obj, name)
    
    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.__slots__:
            object.__setattr__(self, name, value)
        else:
            obj = self._get_object()
            setattr(obj, name, value)
    
    def __call__(self, *args, **kwargs) -> Any:
        obj = self._get_object()
        if not callable(obj):
            raise TypeError(f"'{self._symbol_name}' object is not callable")
        return obj(*args, **kwargs)
    
    def __repr__(self) -> str:
        loaded = object.__getattribute__(self, '_loaded')
        symbol_name = object.__getattribute__(self, '_symbol_name')
        module_name = object.__getattribute__(self, '_module_name')
        symbol_type = object.__getattribute__(self, '_symbol_type')
        
        if loaded:
            obj = object.__getattribute__(self, '_cached_obj')
            return f"<LazySymbol {symbol_type} '{symbol_name}' from '{module_name}' (loaded: {obj})>"
        return f"<LazySymbol {symbol_type} '{symbol_name}' from '{module_name}' (not loaded)>"
    
    def __str__(self) -> str:
        obj = self._get_object()
        return str(obj)
    
    def __class__(self) -> type:
        obj = self._get_object()
        return obj.__class__
    
    def __instancecheck__(self, instance: Any) -> bool:
        obj = self._get_object()
        return isinstance(instance, obj)
    
    def __subclasscheck__(self, subclass: type) -> bool:
        obj = self._get_object()
        return issubclass(subclass, obj)
    
    def __origin__(self) -> Any:
        obj = self._get_object()
        return getattr(obj, '__origin__', obj)
    
    def __args__(self) -> tuple:
        obj = self._get_object()
        return getattr(obj, '__args__', ())
    
    def __enter__(self):
        obj = self._get_object()
        return obj.__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        obj = self._get_object()
        return obj.__exit__(exc_type, exc_val, exc_tb)
    
    async def __aenter__(self):
        obj = self._get_object()
        return await obj.__aenter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        obj = self._get_object()
        return await obj.__aexit__(exc_type, exc_val, exc_tb)
    
    def __iter__(self):
        obj = self._get_object()
        return iter(obj)
    
    def __next__(self):
        obj = self._get_object()
        return next(obj)
    
    def __aiter__(self):
        obj = self._get_object()
        return obj.__aiter__()
    
    async def __anext__(self):
        obj = self._get_object()
        return await obj.__anext__()
    
    def __get__(self, obj, objtype=None):
        underlying = self._get_object()
        if hasattr(underlying, '__get__'):
            return underlying.__get__(obj, objtype)
        return underlying
    
    # Arithmetic operators
    def __add__(self, other): return self._get_object() + other
    def __sub__(self, other): return self._get_object() - other
    def __mul__(self, other): return self._get_object() * other
    def __truediv__(self, other): return self._get_object() / other
    def __floordiv__(self, other): return self._get_object() // other
    def __mod__(self, other): return self._get_object() % other
    def __pow__(self, other): return self._get_object() ** other
    def __matmul__(self, other): return self._get_object() @ other
    
    # Comparison operators
    def __eq__(self, other): return self._get_object() == other
    def __ne__(self, other): return self._get_object() != other
    def __lt__(self, other): return self._get_object() < other
    def __le__(self, other): return self._get_object() <= other
    def __gt__(self, other): return self._get_object() > other
    def __ge__(self, other): return self._get_object() >= other
    
    # Indexing
    def __getitem__(self, key): return self._get_object()[key]
    def __setitem__(self, key, value): self._get_object()[key] = value
    def __delitem__(self, key): del self._get_object()[key]
    
    # Length
    def __len__(self): return len(self._get_object())
    
    # Boolean
    def __bool__(self): return bool(self._get_object())
    
    # Hash
    def __hash__(self): return hash(self._get_object())


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
                """Internal import function with retry support"""
                if not _RETRY_CONFIG["enabled"]:
                    return importlib.import_module(name)
                
                max_retries = _RETRY_CONFIG["max_retries"]
                retry_delay = _RETRY_CONFIG["retry_delay"]
                retry_modules = _RETRY_CONFIG["retry_modules"]
                
                if retry_modules and name.split('.')[0] not in retry_modules:
                    return importlib.import_module(name)
                
                in_async_context = False
                try:
                    loop = asyncio.get_running_loop()
                    in_async_context = loop is not None
                except RuntimeError:
                    pass
                
                last_error = None
                for attempt in range(max_retries + 1):
                    try:
                        return importlib.import_module(name)
                    except ImportError as e:
                        last_error = e
                        if attempt < max_retries:
                            if _DEBUG_MODE:
                                logging.info(f"Retry {attempt + 1}/{max_retries} for {name}")
                            if not in_async_context:
                                time.sleep(retry_delay)
                raise last_error
            
            try:
                module = _do_import(module_name)
                
                elapsed = time.perf_counter() - start_time
                _IMPORT_STATS.total_imports += 1
                _IMPORT_STATS.total_time += elapsed
                _IMPORT_STATS.module_times[module_name] = elapsed
                _IMPORT_STATS.module_access_counts[alias] = 1
                
                _record_module_load(module_name)
                
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
                    from ._install import _get_pip_package_name, _install_package_sync, _interactive_install_confirm, rebuild_module_cache
                    
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
            if name not in submodule_cache:
                full_name = f"{object.__getattribute__(self, '_module_name')}.{name}"
                submodule_cache[name] = LazySubmodule(full_name, self, name)
            return submodule_cache[name]
        
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


class LazySubmodule:
    """
    Lazy loading submodule proxy class.
    
    Supports recursive lazy loading for nested module access like np.linalg.svd.
    """
    
    __slots__ = ('_full_name', '_parent', '_attr_name', '_cached_module', '_submodule_cache')
    
    def __init__(self, full_name: str, parent: Union[LazyModule, 'LazySubmodule'], attr_name: str):
        object.__setattr__(self, '_full_name', full_name)
        object.__setattr__(self, '_parent', parent)
        object.__setattr__(self, '_attr_name', attr_name)
        object.__setattr__(self, '_cached_module', None)
        object.__setattr__(self, '_submodule_cache', {})
    
    def _get_module(self) -> Any:
        """Get the actual submodule (lazy load)"""
        cached = object.__getattribute__(self, '_cached_module')
        if cached is not None:
            _CACHE_STATS["module_hits"] += 1
            return cached
        
        _CACHE_STATS["module_misses"] += 1
        
        full_name = object.__getattribute__(self, '_full_name')
        
        start_time = time.perf_counter()
        
        try:
            module = importlib.import_module(full_name)
            
            elapsed = time.perf_counter() - start_time
            _IMPORT_STATS.total_imports += 1
            _IMPORT_STATS.total_time += elapsed
            _IMPORT_STATS.module_times[full_name] = elapsed
            
            _record_module_load(full_name)
            
            object.__setattr__(self, '_cached_module', module)
            
            if _DEBUG_MODE:
                logging.info(f"[laziest-import] Loaded submodule '{full_name}' in {elapsed*1000:.2f}ms")
            
            return module
        except ImportError:
            parent = object.__getattribute__(self, '_parent')
            attr_name = object.__getattribute__(self, '_attr_name')
            parent_module = parent._get_module()
            attr = getattr(parent_module, attr_name)
            
            if isinstance(attr, ModuleType):
                object.__setattr__(self, '_cached_module', attr)
                return attr
            
            return attr
    
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
            if name not in submodule_cache:
                full_name = f"{object.__getattribute__(self, '_full_name')}.{name}"
                submodule_cache[name] = LazySubmodule(full_name, self, name)
            return submodule_cache[name]
        
        return attr
    
    def __dir__(self) -> List[str]:
        module = self._get_module()
        return dir(module)
    
    def __repr__(self) -> str:
        full_name = object.__getattribute__(self, '_full_name')
        cached = object.__getattribute__(self, '_cached_module')
        if cached is not None:
            return f"<LazySubmodule '{full_name}' (loaded)>"
        return f"<LazySubmodule '{full_name}' (not loaded)>"
    
    def __call__(self, *args, **kwargs) -> Any:
        module = self._get_module()
        if callable(module):
            return module(*args, **kwargs)
        raise TypeError(f"'{type(module).__name__}' object is not callable")


class LazyProxy:
    """
    A proxy object that intercepts all attribute access and applies
    intelligent module recognition including:
    - Abbreviation expansion
    - Submodule mapping
    - Misspelling correction
    - Fuzzy matching
    
    Usage:
        from laziest_import import lazy
        
        # These all work with auto-correction:
        arr = lazy.nump.array([1, 2, 3])  # nump -> numpy
        df = lazy.pnda.DataFrame()         # pnda -> pandas
        net = lazy.nn.Linear(10, 5)        # nn -> torch.nn
    """
    __slots__ = ()
    
    def __getattr__(self, name: str) -> LazyModule:
        """Intercept attribute access and return a LazyModule with auto-correction."""
        if name in _ALIAS_MAP:
            return _get_lazy_module(name)
        
        if _AUTO_SEARCH_ENABLED:
            found = _search_module(name)
            if found:
                _ALIAS_MAP[name] = found
                return _get_lazy_module(name)
        
        available = list(_ALIAS_MAP.keys())[:10]
        msg = f"No module found for '{name}'."
        if available:
            msg += f" Similar modules: {available}..."
        raise AttributeError(msg)
    
    def __dir__(self) -> List[str]:
        return list(_ALIAS_MAP.keys())
    
    def __repr__(self) -> str:
        return f"<LazyProxy (auto-correction enabled)>"


# Create singleton instance
lazy = LazyProxy()


def _get_lazy_module(alias: str) -> LazyModule:
    """Get or create a LazyModule proxy"""
    if alias not in _LAZY_MODULES:
        if _ALIAS_MAP:
            module_name = _ALIAS_MAP.get(alias, alias)
        else:
            module_name = _lookup_alias_fast(alias) or alias
        _LAZY_MODULES[alias] = LazyModule(alias, module_name)
    return _LAZY_MODULES[alias]
