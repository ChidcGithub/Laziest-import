# Backward-compatible redirect to laziest_import._symbol
from . import (
    _compare_signatures,
    _handle_symbol_not_found,
    _interactive_confirm,
    _is_interactive_terminal,
    _score_symbol_match,
    _search_symbol_direct,
    _search_symbol_enhanced,
    _warn_symbol_conflict,
    search_symbol,
)

__all__ = [
    "_compare_signatures",
    "_handle_symbol_not_found",
    "_interactive_confirm",
    "_is_interactive_terminal",
    "_score_symbol_match",
    "_search_symbol_direct",
    "_search_symbol_enhanced",
    "_warn_symbol_conflict",
    "search_symbol",
]
