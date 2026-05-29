# Backward-compatible redirect to laziest_import._symbol
from . import (
    _SYMBOL_INDEX_LOCK as _SYMBOL_INDEX_LOCK,
)
from . import (
    _build_symbol_index as _build_symbol_index,
)

__all__ = ["_SYMBOL_INDEX_LOCK", "_build_symbol_index"]
