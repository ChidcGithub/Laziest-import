# Backward-compatible redirect to laziest_import._symbol
from . import (
    _build_incremental_symbol_index,
    _remove_package_symbols,
    build_symbol_index_incremental,
)

__all__ = [
    "_build_incremental_symbol_index",
    "_remove_package_symbols",
    "build_symbol_index_incremental",
]
