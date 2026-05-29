# Backward-compatible redirect to laziest_import._symbol
from . import (
    _get_signature_hint as _get_signature_hint,
)
from . import (
    _is_stdlib_module as _is_stdlib_module,
)
from . import (
    _scan_module_symbols as _scan_module_symbols,
)

__all__ = ["_get_signature_hint", "_is_stdlib_module", "_scan_module_symbols"]
