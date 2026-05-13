# Backward-compatible redirect to laziest_import._symbol
from . import (
    search_symbol as search_symbol,
    _search_symbol_direct as _search_symbol_direct,
    _search_symbol_enhanced as _search_symbol_enhanced,
    _handle_symbol_not_found as _handle_symbol_not_found,
    _compare_signatures as _compare_signatures,
    _score_symbol_match as _score_symbol_match,
    _warn_symbol_conflict as _warn_symbol_conflict,
    _is_interactive_terminal as _is_interactive_terminal,
    _interactive_confirm as _interactive_confirm,
)

__all__ = [
    "search_symbol",
    "_search_symbol_direct",
    "_search_symbol_enhanced",
    "_handle_symbol_not_found",
    "_compare_signatures",
    "_score_symbol_match",
    "_warn_symbol_conflict",
    "_is_interactive_terminal",
    "_interactive_confirm",
]