"""
Proxy classes for lazy loading modules and symbols.

This module re-exports all components from the _proxy subpackage for backward compatibility.
"""

# Re-export all public API from the _proxy subpackage
from ._proxy import (
    _MODULE_PROXY_LOCK,
    LazyModule,
    LazyProxy,
    LazySubmodule,
    LazySymbol,
    _get_lazy_module,
    lazy,
)

__all__ = [
    "_MODULE_PROXY_LOCK",
    "LazyModule",
    "LazyProxy",
    "LazySubmodule",
    "LazySymbol",
    "_get_lazy_module",
    "lazy",
]
