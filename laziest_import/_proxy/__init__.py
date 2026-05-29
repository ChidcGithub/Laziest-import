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

from ._factory import _MODULE_PROXY_LOCK, _get_lazy_module
from ._module import LazyModule
from ._proxy import LazyProxy
from ._submodule import LazySubmodule
from ._symbol import LazySymbol

# Create singleton instance
lazy = LazyProxy()

__all__ = [
    "_MODULE_PROXY_LOCK",
    "LazyModule",
    "LazyProxy",
    "LazySubmodule",
    "LazySymbol",
    "_get_lazy_module",
    "lazy",
]
