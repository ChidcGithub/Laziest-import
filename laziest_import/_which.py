"""
Symbol location finder (like Unix `which` command).
"""

from typing import Optional, List, Dict, Any, Tuple
import importlib
import inspect
import sys

from ._config import _SYMBOL_CACHE, _SYMBOL_INDEX_BUILT, _DEBUG_MODE
from ._symbol import _is_stdlib_module


class SymbolLocation:
    """Represents a symbol's definition location."""

    def __init__(
        self,
        module_name: str,
        symbol_name: str,
        symbol_type: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        doc: Optional[str] = None,
        signature: Optional[str] = None,
    ) -> None:
        self.module_name = module_name
        self.symbol_name = symbol_name
        self.symbol_type = symbol_type
        self.file_path = file_path
        self.line_number = line_number
        self.doc = doc
        self.signature = signature

    def __repr__(self) -> str:
        parts = [f"{self.module_name}.{self.symbol_name}"]
        if self.file_path:
            parts.append(f"at {self.file_path}")
            if self.line_number:
                parts.append(f":{self.line_number}")
        return f"<SymbolLocation: {' '.join(parts)}>"

    def __str__(self) -> str:
        if self.file_path:
            location = f"{self.file_path}"
            if self.line_number:
                location += f":{self.line_number}"
            return f"{self.module_name}.{self.symbol_name} ({location})"
        return f"{self.module_name}.{self.symbol_name}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "symbol": self.symbol_name,
            "type": self.symbol_type,
            "file": self.file_path,
            "line": self.line_number,
            "doc": self.doc,
            "signature": self.signature,
        }


def which(
    symbol_name: str, module_hint: Optional[str] = None
) -> Optional[SymbolLocation]:
    """
    Find where a symbol is defined, similar to Unix `which` command.

    Args:
        symbol_name: Name of the symbol to find
        module_hint: Optional module name to search first

    Returns:
        SymbolLocation object or None if not found

    Example:
        >>> which("array")           # Find numpy array
        >>> which("DataFrame", "pandas")  # Find specifically in pandas
    """
    # First check if symbol is in cache
    if symbol_name in _SYMBOL_CACHE:
        locations = _SYMBOL_CACHE[symbol_name]

        # If module_hint provided, try to find in that module first
        if module_hint:
            for loc in locations:
                if loc[0].startswith(module_hint):
                    return _create_location_from_tuple(symbol_name, loc)

            # Also try submodule match
            for loc in locations:
                if module_hint.split(".")[0] in loc[0].split(".")[0]:
                    return _create_location_from_tuple(symbol_name, loc)

            # Module hint didn't match in cache, try live search
            live_result = _find_symbol_live(symbol_name, module_hint)
            if live_result:
                return live_result

        # Return first match (no hint or hint didn't match)
        if locations:
            return _create_location_from_tuple(symbol_name, locations[0])

    # If not in cache and index is built, try direct import
    if not _SYMBOL_INDEX_BUILT:
        return _find_symbol_live(symbol_name, module_hint)

    return None


def which_all(symbol_name: str) -> List[SymbolLocation]:
    """
    Find all locations where a symbol is defined.

    Args:
        symbol_name: Name of the symbol to find

    Returns:
        List of SymbolLocation objects
    """
    locations: List[SymbolLocation] = []

    if symbol_name in _SYMBOL_CACHE:
        for loc in _SYMBOL_CACHE[symbol_name]:
            location = _create_location_from_tuple(symbol_name, loc)
            if location:
                locations.append(location)

    # Also try live search for new modules
    if not _SYMBOL_INDEX_BUILT:
        location = _find_symbol_live(symbol_name, None)
        if location:
            # Avoid duplicates
            if not any(l.module_name == location.module_name for l in locations):
                locations.append(location)

    return locations


def _create_location_from_tuple(
    symbol_name: str, loc_tuple: Tuple[str, str, Optional[str]]
) -> Optional[SymbolLocation]:
    """Create SymbolLocation from cached tuple."""
    module_name, sym_type, _ = loc_tuple

    try:
        # Try to get more details by importing
        mod = importlib.import_module(module_name)
        obj = getattr(mod, symbol_name, None)

        if obj is None:
            return SymbolLocation(module_name, symbol_name, sym_type)

        file_path, line_number = None, None
        try:
            file_path = inspect.getfile(obj)
            line_number = inspect.getsourcelines(obj)[1]
        except (TypeError, OSError):
            pass

        doc = inspect.getdoc(obj)

        signature = None
        if callable(obj) and not isinstance(obj, type):
            try:
                signature = str(inspect.signature(obj))
            except (ValueError, TypeError):
                pass

        return SymbolLocation(
            module_name=module_name,
            symbol_name=symbol_name,
            symbol_type=sym_type,
            file_path=file_path,
            line_number=line_number,
            doc=doc,
            signature=signature,
        )

    except ImportError:
        return SymbolLocation(module_name, symbol_name, sym_type)


def _find_symbol_live(
    symbol_name: str, module_hint: Optional[str]
) -> Optional[SymbolLocation]:
    """Find symbol by trying to import modules live."""
    # Priority modules to search
    priority_modules = []

    if module_hint:
        priority_modules.append(module_hint)

    # Add common data science modules
    priority_modules.extend(
        [
            "numpy",
            "pandas",
            "torch",
            "tensorflow",
            "scipy",
            "collections",
            "typing",
            "os",
            "sys",
            "re",
        ]
    )

    # Remove duplicates while preserving order
    seen = set()
    priority_modules = [x for x in priority_modules if not (x in seen or seen.add(x))]

    for mod_name in priority_modules:
        try:
            mod = importlib.import_module(mod_name)

            # Check direct attributes
            if hasattr(mod, symbol_name):
                obj = getattr(mod, symbol_name)
                return _get_location_from_object(mod_name, symbol_name, obj)

            # Check submodules for nested symbols
            if "." not in symbol_name:
                for attr_name in dir(mod):
                    if attr_name.startswith("_"):
                        continue
                    try:
                        submod = getattr(mod, attr_name)
                        if hasattr(submod, symbol_name):
                            obj = getattr(submod, symbol_name)
                            return _get_location_from_object(
                                f"{mod_name}.{attr_name}", symbol_name, obj
                            )
                    except (ImportError, AttributeError):
                        continue

        except ImportError:
            continue

    return None


def _get_location_from_object(
    module_name: str, symbol_name: str, obj: Any
) -> SymbolLocation:
    """Get detailed location info from an object."""
    sym_type = _get_symbol_type(obj)

    file_path, line_number = None, None
    try:
        file_path = inspect.getfile(obj)
        line_number = inspect.getsourcelines(obj)[1]
    except (TypeError, OSError, RuntimeError):
        pass

    doc = None
    try:
        doc = inspect.getdoc(obj)
    except (TypeError, RuntimeError):
        pass

    signature = None
    if callable(obj) and not isinstance(obj, type):
        try:
            signature = str(inspect.signature(obj))
        except (ValueError, TypeError, RuntimeError):
            pass

    return SymbolLocation(
        module_name=module_name,
        symbol_name=symbol_name,
        symbol_type=sym_type,
        file_path=file_path,
        line_number=line_number,
        doc=doc,
        signature=signature,
    )


def _get_symbol_type(obj: Any) -> str:
    """Get the type of a symbol."""
    if inspect.isclass(obj):
        return "class"
    elif inspect.isfunction(obj):
        return "function"
    elif inspect.ismethod(obj):
        return "method"
    elif inspect.ismodule(obj):
        return "module"
    elif callable(obj):
        return "callable"
    elif isinstance(obj, type):
        return "type"
    else:
        return "object"
