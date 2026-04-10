"""
LazySubmodule class for lazy loading submodules.
"""

from typing import Any, Union, TYPE_CHECKING
import time
import logging
import importlib
from types import ModuleType

from .._config import (
    _DEBUG_MODE,
    _IMPORT_STATS,
    _CACHE_STATS,
)
from .._cache import _record_module_load

# Forward reference for type hints (LazyModule is in _module.py)
if TYPE_CHECKING:
    from ._module import LazyModule


class LazySubmodule:
    """
    Lazy loading submodule proxy class.
    
    Supports recursive lazy loading for nested module access like np.linalg.svd.
    """
    
    __slots__ = ('_full_name', '_parent', '_attr_name', '_cached_module', '_submodule_cache')
    
    def __init__(self, full_name: str, parent: Union['LazyModule', 'LazySubmodule'], attr_name: str):
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
            # Use full_name as cache key to avoid conflicts
            full_name = f"{object.__getattribute__(self, '_full_name')}.{name}"
            if full_name not in submodule_cache:
                submodule_cache[full_name] = LazySubmodule(full_name, self, name)
            return submodule_cache[full_name]
        
        return attr
    
    def __dir__(self) -> list:
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
