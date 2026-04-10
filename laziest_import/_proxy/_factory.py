"""
Factory functions for creating lazy module proxies.
"""

import threading

from .._config import _ALIAS_MAP, _LAZY_MODULES
from .._alias import _lookup_alias_fast
from ._module import LazyModule


# Thread lock for LazyModule creation
_MODULE_PROXY_LOCK = threading.Lock()


def _get_lazy_module(alias: str) -> LazyModule:
    """Get or create a LazyModule proxy"""
    # First check without lock for performance
    if alias in _LAZY_MODULES:
        return _LAZY_MODULES[alias]
    
    with _MODULE_PROXY_LOCK:
        # Double-check after acquiring lock
        if alias not in _LAZY_MODULES:
            if _ALIAS_MAP:
                module_name = _ALIAS_MAP.get(alias, alias)
            else:
                module_name = _lookup_alias_fast(alias) or alias
            _LAZY_MODULES[alias] = LazyModule(alias, module_name)
        return _LAZY_MODULES[alias]
