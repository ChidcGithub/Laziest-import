"""
Factory functions for creating lazy module proxies.
"""

import threading

from .. import _config
from .._alias import _lookup_alias_fast
from ._module import LazyModule

# Thread lock for LazyModule creation
_MODULE_PROXY_LOCK = threading.Lock()


def _get_lazy_module(alias: str) -> LazyModule:
    """Get or create a LazyModule proxy"""
    c = _config

    # First check without lock for performance
    if alias in c._LAZY_MODULES:
        return c._LAZY_MODULES[alias]

    with _MODULE_PROXY_LOCK:
        # Double-check after acquiring lock
        if alias not in c._LAZY_MODULES:
            module_name = c._ALIAS_MAP.get(alias) or _lookup_alias_fast(alias) or alias
            c._LAZY_MODULES[alias] = LazyModule(alias, module_name)
        return c._LAZY_MODULES[alias]
