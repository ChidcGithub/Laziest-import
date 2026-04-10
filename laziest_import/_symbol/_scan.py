"""
Symbol scanning utilities for laziest-import.

This module contains functions for detecting standard library modules
and scanning modules for exported symbols.
"""

from typing import Dict, List, Optional, Set, Any, Tuple
import sys
import inspect
import importlib
import pkgutil
import warnings

from .._config import (
    _DEBUG_MODE,
    _SYMBOL_SEARCH_CONFIG,
    _MODULE_SKIP_CONFIG,
)


def _get_signature_hint(obj: Any) -> Optional[str]:
    """Get a signature hint string for a callable object."""
    try:
        if callable(obj):
            sig = inspect.signature(obj)
            return str(sig)
    except (ValueError, TypeError):
        pass
    return None


def _is_stdlib_module(module_name: str) -> bool:
    """Check if a module is part of the standard library."""
    if hasattr(sys, "stdlib_module_names"):
        return module_name.split(".")[0] in sys.stdlib_module_names

    stdlib_prefixes = {
        "abc",
        "argparse",
        "array",
        "ast",
        "asyncio",
        "atexit",
        "base64",
        "bisect",
        "builtins",
        "bz2",
        "calendar",
        "cgi",
        "cmath",
        "cmd",
        "code",
        "codecs",
        "collections",
        "configparser",
        "contextlib",
        "copy",
        "csv",
        "ctypes",
        "dataclasses",
        "datetime",
        "dbm",
        "decimal",
        "difflib",
        "dis",
        "email",
        "enum",
        "errno",
        "fcntl",
        "filecmp",
        "fileinput",
        "fnmatch",
        "fractions",
        "ftplib",
        "functools",
        "gc",
        "getopt",
        "getpass",
        "gettext",
        "glob",
        "gzip",
        "hashlib",
        "heapq",
        "hmac",
        "html",
        "http",
        "imaplib",
        "importlib",
        "inspect",
        "io",
        "itertools",
        "json",
        "keyword",
        "linecache",
        "locale",
        "logging",
        "lzma",
        "mailbox",
        "marshal",
        "math",
        "mimetypes",
        "mmap",
        "multiprocessing",
        "netrc",
        "numbers",
        "operator",
        "optparse",
        "os",
        "pathlib",
        "pickle",
        "platform",
        "plistlib",
        "poplib",
        "pprint",
        "profile",
        "queue",
        "random",
        "re",
        "reprlib",
        "sched",
        "secrets",
        "select",
        "shelve",
        "shlex",
        "shutil",
        "signal",
        "site",
        "smtplib",
        "socket",
        "socketserver",
        "sqlite3",
        "ssl",
        "stat",
        "statistics",
        "string",
        "struct",
        "subprocess",
        "sys",
        "sysconfig",
        "tarfile",
        "tempfile",
        "termios",
        "textwrap",
        "threading",
        "time",
        "timeit",
        "tkinter",
        "token",
        "tokenize",
        "trace",
        "traceback",
        "types",
        "typing",
        "unicodedata",
        "unittest",
        "urllib",
        "uuid",
        "warnings",
        "wave",
        "weakref",
        "webbrowser",
        "wsgiref",
        "xml",
        "xmlrpc",
        "zipfile",
        "zipimport",
        "zlib",
        "zoneinfo",
    }
    return module_name.split(".")[0] in stdlib_prefixes


def _scan_module_symbols(
    module_name: str,
    depth: int = 1,
    _scanned: Optional[Set[str]] = None,
    _current_depth: int = 0,
) -> Dict[str, List[Tuple[str, str, Optional[str]]]]:
    """Scan a module for exported symbols (classes, functions, callables)."""
    if _scanned is None:
        _scanned = set()

    MAX_DEPTH = 3
    if _current_depth > MAX_DEPTH:
        return {}

    if module_name in _scanned:
        return {}
    _scanned.add(module_name)

    symbols: Dict[str, List[Tuple[str, str, Optional[str]]]] = {}

    if _SYMBOL_SEARCH_CONFIG["skip_stdlib"] and _is_stdlib_module(module_name):
        return symbols

    # Enhanced skip modules using configuration
    skip_modules = {
        "test",
        "tests",
        "testing",
        "conftest",
        "setup",
        "examples",
        "docs",
        "doc",
        "scripts",
        "tools",
        "vendor",
        "vendored",
        "__pycache__",
        ".git",
        ".hg",
        ".svn",
        "pytest",
        "py.test",
        "sphinx",
        "mkdocs",
        "laziest_import",
        "laziest-import",
    }

    # Additional skip patterns from configuration
    if _MODULE_SKIP_CONFIG.get("skip_test_modules", True):
        skip_modules.update(["_test", "test_", "tests_", "_tests"])

    # Check if module should be skipped
    module_lower = module_name.lower()
    if any(skip in module_lower for skip in skip_modules):
        return symbols

    internal_patterns = ["._", ".core.", ".linalg.linalg", ".internal."]
    if any(pattern in module_name for pattern in internal_patterns):
        return symbols

    if module_name.endswith("__main__"):
        return symbols

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        warnings.simplefilter("ignore", FutureWarning)

        try:
            module = importlib.import_module(module_name)
        except (
            ImportError,
            ModuleNotFoundError,
            SyntaxError,
            AttributeError,
            TypeError,
            ValueError,
            OSError,
            RecursionError,
            SystemExit,
        ):
            return symbols

        skip_private = _SYMBOL_SEARCH_CONFIG["skip_private"]

        try:
            public_names = getattr(module, "__all__", None)
            if public_names is None:
                public_names = [
                    name for name in dir(module) if not name.startswith("_")
                ]
            else:
                public_names = [n for n in public_names if isinstance(n, str)]
        except Exception:
            public_names = []

        # Check for large modules and optionally skip
        large_threshold = _MODULE_SKIP_CONFIG.get("large_module_threshold", 100)
        if (
            _MODULE_SKIP_CONFIG.get("skip_large_modules", True)
            and len(public_names) > large_threshold
        ):
            # For large modules, only scan __all__ if defined, otherwise skip most
            if not hasattr(module, "__all__"):
                # Filter to only include likely important symbols
                public_names = [n for n in public_names if not n.startswith("_")][
                    :large_threshold
                ]

        MAX_SYMBOLS_PER_MODULE = 100
        if len(public_names) > MAX_SYMBOLS_PER_MODULE:
            public_names = public_names[:MAX_SYMBOLS_PER_MODULE]

        for name in public_names:
            if skip_private and name.startswith("_"):
                continue

            try:
                obj = getattr(module, name)
            except (AttributeError, ImportError, TypeError, RecursionError):
                continue

            symbol_type = None
            signature = None

            try:
                if inspect.isclass(obj):
                    symbol_type = "class"
                    try:
                        init = getattr(obj, "__init__", None)
                        if init and callable(init):
                            signature = _get_signature_hint(init)
                    except Exception:
                        pass
                elif inspect.isfunction(obj):
                    symbol_type = "function"
                    signature = _get_signature_hint(obj)
                elif callable(obj):
                    symbol_type = "callable"
                    signature = _get_signature_hint(obj)
            except Exception:
                continue

            if symbol_type:
                if name not in symbols:
                    symbols[name] = []
                symbols[name].append((module_name, symbol_type, signature))

    if depth > 0 and hasattr(module, "__path__"):
        try:
            submodule_count = 0
            MAX_SUBMODULES = 20
            for finder, submod_name, ispkg in pkgutil.iter_modules(module.__path__):
                if submodule_count >= MAX_SUBMODULES:
                    break
                full_submod_name = f"{module_name}.{submod_name}"
                try:
                    submod_symbols = _scan_module_symbols(
                        full_submod_name, depth - 1, _scanned, _current_depth + 1
                    )
                    for sym_name, locations in submod_symbols.items():
                        if sym_name not in symbols:
                            symbols[sym_name] = []
                        symbols[sym_name].extend(locations)
                    submodule_count += 1
                except Exception:
                    continue
        except Exception:
            pass

    return symbols
