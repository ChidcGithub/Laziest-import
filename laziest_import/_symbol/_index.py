# Backward-compatible redirect to laziest_import._symbol
from . import (
    _build_symbol_index as _build_symbol_index,
    _SYMBOL_INDEX_LOCK as _SYMBOL_INDEX_LOCK,
)

__all__ = ["_build_symbol_index", "_SYMBOL_INDEX_LOCK"]