"""
Proxy classes for lazy loading modules and symbols.

This module re-exports all components from the _proxy subpackage for backward compatibility.
"""

# Re-export all public API from the _proxy subpackage
from ._proxy import (
    LazySymbol,
    LazyModule,
    LazySubmodule,
    LazyProxy,
    lazy,
    _get_lazy_module,
    _MODULE_PROXY_LOCK,
)

__all__ = [
    'LazySymbol',
    'LazyModule',
    'LazySubmodule',
    'LazyProxy',
    'lazy',
    '_get_lazy_module',
    '_MODULE_PROXY_LOCK',
]