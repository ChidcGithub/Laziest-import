"""
LazyProxy class for intelligent module recognition.
"""

from typing import List

from .._config import _ALIAS_MAP, _AUTO_SEARCH_ENABLED
from .._fuzzy import _search_module
from ._module import LazyModule
from ._factory import _get_lazy_module


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
