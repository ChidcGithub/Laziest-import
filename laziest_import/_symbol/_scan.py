# Backward-compatible redirect to laziest_import._symbol
from . import (
    _get_signature_hint,
    _is_stdlib_module,
    _scan_module_symbols,
)

__all__ = ["_get_signature_hint", "_is_stdlib_module", "_scan_module_symbols"]
