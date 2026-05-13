# Backward-compatible redirect to laziest_import._symbol
from . import (
    _is_stdlib_module as _is_stdlib_module,
    _scan_module_symbols as _scan_module_symbols,
    _get_signature_hint as _get_signature_hint,
)

__all__ = ["_is_stdlib_module", "_scan_module_symbols", "_get_signature_hint"]