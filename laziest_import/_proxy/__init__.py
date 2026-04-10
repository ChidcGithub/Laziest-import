"""
Proxy classes for lazy loading modules and symbols.

This package provides:
- LazySymbol: Lazy loading symbol (class/function) proxy
- LazyModule: Lazy loading module proxy
- LazySubmodule: Lazy loading submodule proxy
- LazyProxy: Intelligent module recognition proxy
- lazy: Singleton LazyProxy instance
- _get_lazy_module: Factory function for creating LazyModule proxies
"""

from ._symbol import LazySymbol
from ._module import LazyModule
from ._submodule import LazySubmodule
from ._proxy import LazyProxy
from ._factory import _get_lazy_module, _MODULE_PROXY_LOCK

# Create singleton instance
lazy = LazyProxy()

__all__ = [
    'LazySymbol',
    'LazyModule',
    'LazySubmodule',
    'LazyProxy',
    'lazy',
    '_get_lazy_module',
    '_MODULE_PROXY_LOCK',
]
