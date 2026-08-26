"""
Type-stub (.pyi) based symbol indexing for laziest-import.

Parses ``.pyi`` stub files instead of importing modules:

* zero import side effects (no code execution — safe against hostile modules),
* an order of magnitude faster than import-and-inspect scanning,
* precise type signatures for free.

Modules without stubs transparently fall back to the classic import-based scan.
"""

import ast
import importlib.util
import logging
from pathlib import Path
from typing import Any, Optional

from . import _config

# Locations that can hold a stub for one dotted path segment
_STUB_SUFFIXES = ("__init__.pyi", ".pyi")


def _find_stub_path(module_name: str) -> Optional[Path]:
    """Locate the ``.pyi`` file for a (possibly dotted) module name.

    Uses ``importlib.util.find_spec`` on the TOP-LEVEL package only, then walks
    the remaining segments through ``submodule_search_locations`` on the
    filesystem — neither the module itself nor its parent packages are
    executed.
    """
    parts = module_name.split(".")
    try:
        spec = importlib.util.find_spec(parts[0])
    except (ImportError, ValueError, ModuleNotFoundError):
        return None
    if spec is None:
        return None

    if len(parts) == 1:
        origin = spec.origin
        if not origin:
            return None
        stub = Path(origin).with_suffix(".pyi")
        return stub if stub.is_file() else None

    search_dirs = list(spec.submodule_search_locations or ())
    if not search_dirs and spec.origin:
        search_dirs = [str(Path(spec.origin).parent)]

    stub_path: Optional[Path] = None
    for part in parts[1:]:
        found: Optional[tuple[Path, list[str]]] = None
        for directory in search_dirs:
            base = Path(directory) / part
            pkg_init = base / "__init__.pyi"
            mod_file = base.with_name(part + ".pyi")
            if pkg_init.is_file():
                found = (pkg_init, [str(base)])
                break
            if mod_file.is_file():
                found = (mod_file, [])
                break
        if found is None:
            return None
        stub_path, search_dirs = found
    return stub_path


def _unparse(node: Optional[ast.expr]) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return ""


_MAX_SIG_LENGTH = 160


def _format_function_signature(node: Any) -> Optional[str]:
    """Build a compact ``(x: int, y: str = ...) -> bool`` style signature."""
    try:
        args = node.args
        pieces: list[str] = []

        positional = list(getattr(args, "posonlyargs", []) or []) + list(args.args or [])
        defaults = list(args.defaults or [])
        default_offset = len(positional) - len(defaults)

        def fmt(arg: ast.arg, default: Optional[ast.expr] = None) -> str:
            text = arg.arg
            annotation = _unparse(arg.annotation)
            if annotation:
                text += f": {annotation}"
            if default is not None:
                rendered = _unparse(default) or "..."
                text += f" = {rendered}"
            return text

        for index, arg in enumerate(positional):
            default = defaults[index - default_offset] if index >= default_offset else None
            pieces.append(fmt(arg, default))

        def fmt_starred(name: str, prefix: str, annotation: Optional[ast.expr]) -> str:
            text = prefix + name
            rendered = _unparse(annotation)
            if rendered:
                text += f": {rendered}"
            return text

        if args.vararg is not None:
            pieces.append(fmt_starred(args.vararg.arg, "*", args.vararg.annotation))
        elif args.kwonlyargs:
            pieces.append("*")

        kw_defaults = list(args.kw_defaults or [])
        for index, arg in enumerate(args.kwonlyargs or []):
            default = kw_defaults[index] if index < len(kw_defaults) else None
            pieces.append(fmt(arg, default))

        if args.kwarg is not None:
            pieces.append(fmt_starred(args.kwarg.arg, "**", args.kwarg.annotation))

        signature = "(" + ", ".join(pieces) + ")"
        return_type = _unparse(node.returns)
        if return_type:
            signature += f" -> {return_type}"
        return signature[:_MAX_SIG_LENGTH]
    except Exception:
        return None


def _collect_stub_symbols_from_source(
    source: str,
    module_name: str,
    include_private: bool = False,
    max_symbols: int = 1000,
) -> dict[str, list[tuple[str, str, Optional[str]]]]:
    """Parse stub source text and extract top-level symbols.

    Descends through ``if``/``try`` conditional guards (version/platform
    switches are everywhere in real stubs) but not into class/function bodies.
    Overloaded definitions keep their first occurrence.
    """
    symbols: dict[str, list[tuple[str, str, Optional[str]]]] = {}

    def add(name: str, symbol_type: str, signature: Optional[str]) -> bool:
        if not include_private and name.startswith("_"):
            return False
        if name in symbols or len(symbols) >= max_symbols:
            return False
        symbols[name] = [(module_name, symbol_type, signature)]
        return True

    def visit_body(body: list[ast.stmt]) -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                add(node.name, "function", _format_function_signature(node))
            elif isinstance(node, ast.ClassDef):
                bases_sig = ", ".join(_unparse(b) for b in node.bases[:3] if _unparse(b))
                add(node.name, "class", f"({bases_sig})" if bases_sig else None)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                annotation = _unparse(node.annotation)
                add(node.target.id, "variable", annotation or None)
            elif isinstance(node, ast.If):
                visit_body(node.body)
                visit_body(node.orelse)
            elif isinstance(node, ast.Try):
                visit_body(node.body)
                visit_body(node.orelse)
                for handler in node.handlers:
                    visit_body(handler.body)

    tree = ast.parse(source)
    visit_body(list(tree.body))
    return symbols


def _scan_stub_symbols(
    module_name: str,
    include_private: bool = False,
    max_symbols: Optional[int] = None,
) -> dict[str, list[tuple[str, str, Optional[str]]]]:
    """Scan one module's symbols from its ``.pyi`` stub.

    Returns {} when the module has no usable stub (caller should fall back
    to import-based scanning).
    """
    if not _config._STUB_INDEX_CONFIG.get("enabled", True):
        return {}

    stub_path = _find_stub_path(module_name)
    if stub_path is None:
        return {}

    max_bytes = int(_config._STUB_INDEX_CONFIG.get("max_file_size_mb", 4)) * 1024 * 1024
    try:
        if stub_path.stat().st_size > max_bytes:
            if _config._DEBUG_MODE:
                logging.debug(f"[laziest-import] Stub too large, skipping: {stub_path}")
            return {}
        source = stub_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}

    limit = max_symbols or int(_config._STUB_INDEX_CONFIG.get("max_symbols_per_module", 1000))

    try:
        symbols = _collect_stub_symbols_from_source(
            source,
            module_name,
            include_private=include_private,
            max_symbols=limit,
        )
    except SyntaxError as e:
        if _config._DEBUG_MODE:
            logging.debug(f"[laziest-import] Unparsable stub {stub_path}: {e}")
        return {}

    if symbols and _config._DEBUG_MODE:
        logging.debug(
            f"[laziest-import] Stub-scanned '{module_name}': {len(symbols)} symbols from {stub_path.name}"
        )
    return symbols


__all__ = [
    "_collect_stub_symbols_from_source",
    "_find_stub_path",
    "_format_function_signature",
    "_scan_stub_symbols",
]
