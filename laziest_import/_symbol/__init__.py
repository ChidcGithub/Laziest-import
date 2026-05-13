"""
Symbol search system for laziest-import.

This module provides symbol search, resolution, indexing, scanning,
sharding, and incremental update functionality.

Public API:
    - enable_symbol_search / disable_symbol_search
    - search_symbol
    - rebuild_symbol_index
    - set_symbol_preference / get_symbol_preference / clear_symbol_preference
    - list_symbol_conflicts
    - set_module_priority / get_module_priority
    - enable_auto_symbol_resolution / disable_auto_symbol_resolution
    - get_symbol_resolution_config
    - get_loaded_modules_context
    - get_module_skip_config / set_module_skip_config
    - build_symbol_index_incremental
    - search_with_sharding / enable_sharding / disable_sharding
    - get_sharding_config / clear_shard_cache

Internal exports (backward compatibility):
    - _is_stdlib_module, _scan_module_symbols, _build_symbol_index
    - _search_symbol_direct, _search_symbol_enhanced, _handle_symbol_not_found
    - _build_incremental_symbol_index, _remove_package_symbols
    - _SYMBOL_INDEX_LOCK
    - _config._SYMBOL_CACHE, _config._STDLIB_SYMBOL_CACHE, _config._THIRD_PARTY_SYMBOL_CACHE
"""

from typing import Dict, List, Optional, Set, Any, Tuple
import sys
import time
import logging
import threading
import json
import warnings
import importlib
import inspect
import pkgutil
import importlib.util
from dataclasses import dataclass, asdict
from pathlib import Path

from .. import _config
from .._config import SearchResult, SymbolMatch
from .._fuzzy import (
    _levenshtein_distance,
    _get_common_symbol_misspellings,
)
from .._cache import (
    _load_symbol_index,
    _save_symbol_index,
    _load_tracked_packages,
    _save_tracked_packages,
    _track_package,
    _get_cache_dir,
    _get_cache_size,
    _cleanup_cache_if_needed,
    _check_cache_size_before_save,
    _should_use_compression,
    _get_compressed_path,
    _save_compressed_json,
    _load_compressed_json,
)
from .._alias import _build_known_modules_cache


# ── Symbol index lock ──────────────────────────────────────
_SYMBOL_INDEX_LOCK = threading.Lock()

# Backward-compatible re-exports of config state (previously direct imports)
_SYMBOL_CACHE = _config._SYMBOL_CACHE
_STDLIB_SYMBOL_CACHE = _config._STDLIB_SYMBOL_CACHE
_THIRD_PARTY_SYMBOL_CACHE = _config._THIRD_PARTY_SYMBOL_CACHE


# ── Standard library detection ─────────────────────────────

def _is_stdlib_module(module_name: str) -> bool:
    """Check if a module is part of the standard library."""
    if hasattr(sys, "stdlib_module_names"):
        return module_name.split(".")[0] in sys.stdlib_module_names

    stdlib_prefixes = {
        "abc", "argparse", "array", "ast", "asyncio", "atexit", "base64",
        "bisect", "builtins", "bz2", "calendar", "cgi", "cmath", "cmd",
        "code", "codecs", "collections", "configparser", "contextlib",
        "copy", "csv", "ctypes", "dataclasses", "datetime", "dbm", "decimal",
        "difflib", "dis", "email", "enum", "errno", "fcntl", "filecmp",
        "fileinput", "fnmatch", "fractions", "ftplib", "functools", "gc",
        "getopt", "getpass", "gettext", "glob", "gzip", "hashlib", "heapq",
        "hmac", "html", "http", "imaplib", "importlib", "inspect", "io",
        "itertools", "json", "keyword", "linecache", "locale", "logging",
        "lzma", "mailbox", "marshal", "math", "mimetypes", "mmap",
        "multiprocessing", "netrc", "numbers", "operator", "optparse", "os",
        "pathlib", "pickle", "platform", "plistlib", "poplib", "pprint",
        "profile", "queue", "random", "re", "reprlib", "sched", "secrets",
        "select", "shelve", "shlex", "shutil", "signal", "site", "smtplib",
        "socket", "socketserver", "sqlite3", "ssl", "stat", "statistics",
        "string", "struct", "subprocess", "sys", "sysconfig", "tarfile",
        "tempfile", "termios", "textwrap", "threading", "time", "timeit",
        "tkinter", "token", "tokenize", "trace", "traceback", "types",
        "typing", "unicodedata", "unittest", "urllib", "uuid", "warnings",
        "wave", "weakref", "webbrowser", "wsgiref", "xml", "xmlrpc",
        "zipfile", "zipimport", "zlib", "zoneinfo",
    }
    return module_name.split(".")[0] in stdlib_prefixes


# ── Signature helper ───────────────────────────────────────

def _get_signature_hint(obj: Any) -> Optional[str]:
    """Get a signature hint string for a callable object."""
    try:
        if callable(obj):
            sig = inspect.signature(obj)
            return str(sig)
    except (ValueError, TypeError):
        pass
    return None


# ── Symbol scanning ─────────────────────────────────────────

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

    if _config._SYMBOL_SEARCH_CONFIG["skip_stdlib"] and _is_stdlib_module(module_name):
        return symbols

    skip_modules = {
        "test", "tests", "testing", "conftest", "setup",
        "examples", "docs", "doc", "scripts", "tools",
        "vendor", "vendored", "__pycache__", ".git", ".hg",
        ".svn", "pytest", "py.test", "sphinx", "mkdocs",
        "laziest_import", "laziest-import",
    }

    if _config._MODULE_SKIP_CONFIG.get("skip_test_modules", True):
        skip_modules.update(["_test", "test_", "tests_", "_tests"])

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
            ImportError, ModuleNotFoundError, SyntaxError,
            AttributeError, TypeError, ValueError,
            OSError, RecursionError, SystemExit,
        ):
            return symbols

        skip_private = _config._SYMBOL_SEARCH_CONFIG["skip_private"]

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

        large_threshold = _config._MODULE_SKIP_CONFIG.get("large_module_threshold", 100)
        if (
            _config._MODULE_SKIP_CONFIG.get("skip_large_modules", True)
            and len(public_names) > large_threshold
        ):
            if not hasattr(module, "__all__"):
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


# ── Symbol index building ───────────────────────────────────

def _build_symbol_index(
    force: bool = False, max_modules: int = 100, timeout: float = 30.0
) -> None:
    """Build the symbol index by scanning installed packages."""
    if not _config.is_initialized() and not force:
        pass

    import laziest_import._config as config
    if config._SYMBOL_INDEX_BUILT and not force:
        return

    if not _config._SYMBOL_SEARCH_CONFIG["cache_enabled"]:
        return

    with _SYMBOL_INDEX_LOCK:
        if config._SYMBOL_INDEX_BUILT and not force:
            return

        start_time = time.perf_counter()
        existing_tracked = _load_tracked_packages()

        stdlib_cache = _load_symbol_index("stdlib")
        third_party_cache = _load_symbol_index("third_party")

        if not force and (stdlib_cache or third_party_cache):
            _config._TRACKED_PACKAGES.clear()
            _config._TRACKED_PACKAGES.update(existing_tracked)

            if stdlib_cache:
                _config._STDLIB_SYMBOL_CACHE.clear()
                _config._STDLIB_SYMBOL_CACHE.update({
                    k: [tuple(loc) for loc in v]
                    for k, v in stdlib_cache.symbols.items()
                })
                _config._set_stdlib_cache_built(True)
                if _config._DEBUG_MODE:
                    logging.info(
                        f"[laziest-import] Loaded stdlib symbol index: "
                        f"{len(_config._STDLIB_SYMBOL_CACHE)} symbols"
                    )

            if third_party_cache:
                _config._THIRD_PARTY_SYMBOL_CACHE.clear()
                _config._THIRD_PARTY_SYMBOL_CACHE.update({
                    k: [tuple(loc) for loc in v]
                    for k, v in third_party_cache.symbols.items()
                })
                _config._set_third_party_cache_built(True)
                if _config._DEBUG_MODE:
                    logging.info(
                        f"[laziest-import] Loaded third-party symbol index: "
                        f"{len(_config._THIRD_PARTY_SYMBOL_CACHE)} symbols"
                    )

            if config._STDLIB_CACHE_BUILT or config._THIRD_PARTY_CACHE_BUILT:
                _config._SYMBOL_CACHE.clear()
                _config._SYMBOL_CACHE.update(_config._STDLIB_SYMBOL_CACHE)
                _config._SYMBOL_CACHE.update(_config._THIRD_PARTY_SYMBOL_CACHE)
                _config._set_symbol_index_built(True)
                _config._CACHE_STATS["symbol_hits"] += 1
                elapsed = time.perf_counter() - start_time
                _config._CACHE_STATS["last_build_time"] = elapsed
                if _config._DEBUG_MODE:
                    logging.info(
                        f"[laziest-import] Symbol index loaded from cache: "
                        f"{len(_config._SYMBOL_CACHE)} symbols in {elapsed:.3f}s"
                    )
                return

    _config._CACHE_STATS["symbol_misses"] += 1
    _config._SYMBOL_CACHE.clear()
    _config._STDLIB_SYMBOL_CACHE.clear()
    _config._THIRD_PARTY_SYMBOL_CACHE.clear()
    depth = _config._SYMBOL_SEARCH_CONFIG["search_depth"]
    known_modules = _build_known_modules_cache()

    if _config._DEBUG_MODE:
        logging.info(
            f"[laziest-import] Building symbol index for {len(known_modules)} modules..."
        )

    priority_packages = {
        "pandas", "numpy", "matplotlib", "seaborn", "scipy", "sklearn",
        "torch", "tensorflow", "keras", "xgboost", "lightgbm",
        "requests", "flask", "django", "fastapi", "PIL", "cv2",
        "plotly", "bokeh", "json", "os", "sys", "re", "datetime",
        "collections", "itertools", "pathlib", "typing", "functools",
        "contextlib", "dataclasses", "math", "cmath", "statistics",
        "random", "decimal", "fractions",
    }

    scanned_stdlib = 0
    scanned_third_party = 0
    timed_out = False
    build_success = False

    try:
        sorted_modules = sorted(
            known_modules,
            key=lambda m: (0 if m.split(".")[0] in priority_packages else 1, m),
        )

        for module_name in sorted_modules:
            if time.perf_counter() - start_time > timeout:
                timed_out = True
                if _config._DEBUG_MODE:
                    logging.info(
                        f"[laziest-import] Symbol index build timed out after {timeout}s"
                    )
                break

            if scanned_stdlib + scanned_third_party >= max_modules:
                break

            if any(
                x in module_name.lower()
                for x in ["test", "tests", "_test", "__pycache__", "conftest", "setup"]
            ):
                continue

            try:
                symbols = _scan_module_symbols(module_name, depth)
                is_stdlib = _is_stdlib_module(module_name)
                target_cache = (
                    _config._STDLIB_SYMBOL_CACHE if is_stdlib else _config._THIRD_PARTY_SYMBOL_CACHE
                )

                for sym_name, locations in symbols.items():
                    if sym_name not in _config._SYMBOL_CACHE:
                        _config._SYMBOL_CACHE[sym_name] = []
                    _config._SYMBOL_CACHE[sym_name].extend(locations)

                    if sym_name not in target_cache:
                        target_cache[sym_name] = []
                    target_cache[sym_name].extend(locations)

                if is_stdlib:
                    scanned_stdlib += 1
                else:
                    scanned_third_party += 1
                    top_level = module_name.split(".")[0]
                    if top_level not in _config._TRACKED_PACKAGES:
                        _track_package(top_level)

            except Exception:
                continue

        build_success = True

    except Exception as e:
        if _config._DEBUG_MODE:
            logging.warning(f"[laziest-import] Symbol index build failed: {e}")
        build_success = False

    if build_success and (scanned_stdlib > 0 or scanned_third_party > 0):
        _config._set_symbol_index_built(True)
        if scanned_stdlib > 0:
            _config._set_stdlib_cache_built(True)
        if scanned_third_party > 0:
            _config._set_third_party_cache_built(True)

        _save_symbol_index(_config._STDLIB_SYMBOL_CACHE, "stdlib", scanned_stdlib)
        _save_symbol_index(_config._THIRD_PARTY_SYMBOL_CACHE, "third_party", scanned_third_party)
        _save_tracked_packages()

        elapsed = time.perf_counter() - start_time
        _config._CACHE_STATS["last_build_time"] = elapsed
        _config._CACHE_STATS["build_count"] += 1

        if _config._DEBUG_MODE:
            timeout_msg = " (timed out)" if timed_out else ""
            logging.info(
                f"[laziest-import] Symbol index built: {len(_config._SYMBOL_CACHE)} symbols "
                f"(stdlib: {scanned_stdlib}, third-party: {scanned_third_party}) "
                f"in {elapsed:.2f}s{timeout_msg}"
            )
    elif timed_out and _config._DEBUG_MODE:
        logging.info(
            f"[laziest-import] Symbol index build timed out with no data collected"
        )


# ── Signature comparison ────────────────────────────────────

def _compare_signatures(sig1: Optional[str], sig2: Optional[str]) -> float:
    """Compare two signature strings and return a similarity score."""
    if sig1 is None or sig2 is None:
        return 0.5

    def extract_params(sig: str) -> Set[str]:
        try:
            inner = sig.strip("()")
            if not inner:
                return set()
            params = set()
            for part in inner.split(","):
                part = part.strip()
                if part:
                    param_name = part.split("=")[0].split(":")[0].strip()
                    if param_name and not param_name.startswith("*"):
                        params.add(param_name)
            return params
        except Exception:
            return set()

    params1 = extract_params(sig1)
    params2 = extract_params(sig2)

    if not params1 or not params2:
        return 0.5

    intersection = len(params1 & params2)
    union = len(params1 | params2)
    return intersection / union if union > 0 else 0.0


# ── Symbol search ───────────────────────────────────────────

def search_symbol(
    name: str,
    symbol_type: Optional[str] = None,
    signature: Optional[str] = None,
    max_results: Optional[int] = None,
) -> List[SearchResult]:
    """Search for a symbol (class/function) by name across installed packages."""
    if not _config._SYMBOL_SEARCH_CONFIG["enabled"]:
        return []

    import laziest_import._config as config
    if not config._SYMBOL_INDEX_BUILT:
        _build_symbol_index()

    if name not in _config._SYMBOL_CACHE:
        name_lower = name.lower()
        matches = []
        for cached_name in _config._SYMBOL_CACHE.keys():
            if cached_name.lower() == name_lower:
                matches.append(cached_name)
            elif name_lower in cached_name.lower():
                matches.append(cached_name)
            elif _levenshtein_distance(name_lower, cached_name.lower()) <= 2:
                matches.append(cached_name)

        if not matches:
            return []

        all_results = []
        for match_name in matches[:3]:
            all_results.extend(
                _search_symbol_direct(match_name, symbol_type, signature)
            )

        seen = set()
        results = []
        for r in all_results:
            key = (r.module_name, r.symbol_name)
            if key not in seen:
                seen.add(key)
                results.append(r)

        max_res = max_results or _config._SYMBOL_SEARCH_CONFIG["max_results"]
        return sorted(results, key=lambda x: -x.score)[:max_res]

    return _search_symbol_direct(name, symbol_type, signature, max_results)


def _search_symbol_direct(
    name: str,
    symbol_type: Optional[str] = None,
    signature: Optional[str] = None,
    max_results: Optional[int] = None,
) -> List[SearchResult]:
    """Direct search for an exact symbol name in cache."""
    results = []

    if name not in _config._SYMBOL_CACHE:
        return results

    for module_name, sym_type, cached_sig in _config._SYMBOL_CACHE[name]:
        if symbol_type and sym_type != symbol_type:
            continue

        score = 1.0

        if _config._SYMBOL_SEARCH_CONFIG["skip_stdlib"] and _is_stdlib_module(module_name):
            score *= 0.5

        if signature and cached_sig:
            sig_score = _compare_signatures(signature, cached_sig)
            if _config._SYMBOL_SEARCH_CONFIG["exact_params"] and sig_score < 0.9:
                continue
            score *= 0.5 + 0.5 * sig_score

        results.append(
            SearchResult(
                module_name=module_name,
                symbol_name=name,
                symbol_type=sym_type,
                signature=cached_sig,
                score=score,
            )
        )

    results.sort(key=lambda x: -x.score)
    max_res = max_results or _config._SYMBOL_SEARCH_CONFIG["max_results"]
    return results[:max_res]


def _score_symbol_match(
    result: SearchResult, context: Set[str], original_name: str
) -> SymbolMatch:
    """Score a symbol search result with context awareness and priority."""
    confidence = result.score
    module = result.module_name.split(".")[0]
    source = "exact"

    if result.symbol_name in _config._SYMBOL_PREFERENCES:
        pref = _config._SYMBOL_PREFERENCES[result.symbol_name]
        pref_base = pref.split(".")[0]
        if module == pref_base:
            return SymbolMatch(
                module_name=result.module_name,
                symbol_name=result.symbol_name,
                symbol_type=result.symbol_type,
                signature=result.signature,
                confidence=1.0,
                source="user_pref",
                obj=result.obj,
            )
        else:
            confidence *= 0.2
            source = "not_preferred"

    if _config._SYMBOL_RESOLUTION_CONFIG["context_aware"] and module in context:
        confidence *= 1.5
        source = "context"

    priority = _config._MODULE_PRIORITY.get(module, 50)
    confidence *= priority / 100

    if result.symbol_name != original_name:
        distance = _levenshtein_distance(
            original_name.lower(), result.symbol_name.lower()
        )
        max_dist = max(len(original_name), len(result.symbol_name)) // 3
        fuzzy_penalty = distance / max(max_dist, 1)
        confidence *= 1 - fuzzy_penalty * 0.3
        source = "fuzzy"

    if _config._SYMBOL_SEARCH_CONFIG.get("skip_stdlib") and _is_stdlib_module(
        result.module_name
    ):
        confidence *= 0.5

    confidence = min(confidence, 1.0)

    return SymbolMatch(
        module_name=result.module_name,
        symbol_name=result.symbol_name,
        symbol_type=result.symbol_type,
        signature=result.signature,
        confidence=confidence,
        source=source,
        obj=result.obj,
    )


def _search_symbol_enhanced(
    name: str, auto: bool = True, symbol_type: Optional[str] = None
) -> Optional[SymbolMatch]:
    """Enhanced symbol search with conflict resolution and spell correction."""
    if not _config._SYMBOL_RESOLUTION_CONFIG["auto_symbol"]:
        return None

    import laziest_import._config as config
    if not config._SYMBOL_INDEX_BUILT:
        _build_symbol_index()

    original_name = name

    corrected_name = None
    if _config._SYMBOL_RESOLUTION_CONFIG["symbol_misspelling"]:
        misspellings = _get_common_symbol_misspellings()
        name_lower = name.lower()
        if name_lower in misspellings:
            corrected_name = misspellings[name_lower]
            if _config._DEBUG_MODE:
                logging.debug(
                    f"[laziest-import] Symbol misspelling corrected: '{name}' -> '{corrected_name}'"
                )

    search_name = corrected_name or name
    results = search_symbol(search_name, symbol_type=symbol_type)

    if not results and not corrected_name:
        name_lower = search_name.lower()
        fuzzy_matches: List[Tuple[int, str]] = []

        for cached_name in _config._SYMBOL_CACHE.keys():
            dist = _levenshtein_distance(name_lower, cached_name.lower())
            max_dist = min(3, max(len(name_lower), len(cached_name)) // 3)
            if dist <= max_dist:
                fuzzy_matches.append((dist, cached_name))

        fuzzy_matches.sort(key=lambda x: x[0])
        for dist, match_name in fuzzy_matches[:3]:
            match_results = search_symbol(match_name, symbol_type=symbol_type)
            results.extend(match_results)

        if results and _config._DEBUG_MODE:
            logging.debug(
                f"[laziest-import] Fuzzy symbol search found {len(results)} results for '{name}'"
            )

    if not results:
        return None

    context = _infer_context()
    scored_results = [_score_symbol_match(r, context, original_name) for r in results]
    scored_results.sort(key=lambda x: -x.confidence)

    best = scored_results[0]
    second = scored_results[1] if len(scored_results) > 1 else None

    if not auto:
        return best

    threshold = _config._SYMBOL_RESOLUTION_CONFIG["auto_threshold"]
    conflict_threshold = _config._SYMBOL_RESOLUTION_CONFIG["conflict_threshold"]

    if best.confidence >= threshold:
        if second and (best.confidence - second.confidence) < conflict_threshold:
            if _config._SYMBOL_RESOLUTION_CONFIG["warn_on_conflict"]:
                _warn_symbol_conflict(original_name, scored_results[:3])
            if best.source in ("user_pref", "context"):
                return best
            return None
        return best

    if _config._SYMBOL_RESOLUTION_CONFIG["warn_on_conflict"]:
        _warn_symbol_conflict(original_name, scored_results[:3])

    return None


def _warn_symbol_conflict(name: str, matches: List[SymbolMatch]) -> None:
    """Warn about symbol conflict and suggest disambiguation."""
    if not matches:
        return

    suggestions = ", ".join(
        f"{m.module_name}.{m.symbol_name}({m.confidence:.0%})" for m in matches[:3]
    )

    examples = []
    for m in matches[:2]:
        module_alias = m.module_name.split(".")[0]
        examples.append(f"{module_alias}.{m.symbol_name}")

    example_str = " or ".join(examples) if examples else ""

    warnings.warn(
        f"[laziest-import] Symbol '{name}' found in multiple modules: {suggestions}. "
        f"Use module prefix to disambiguate, e.g., {example_str}. "
        f"Or set a preference: set_symbol_preference('{name}', '{matches[0].module_name}')",
        UserWarning,
        stacklevel=4,
    )


# ── Interactive confirm ─────────────────────────────────────

def _is_interactive_terminal() -> bool:
    """Check if we're running in an interactive terminal."""
    if not sys.stdin.isatty():
        return False
    if not sys.stdout.isatty():
        return False
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            return sys.stdin.isatty()
    except ImportError:
        pass
    return True


def _interactive_confirm(
    results: List[SearchResult], symbol_name: str
) -> Optional[str]:
    """Interactively ask user to confirm which module to use."""
    if not results:
        return None

    if not _config._SYMBOL_SEARCH_CONFIG["interactive"]:
        return results[0].module_name

    if not _is_interactive_terminal():
        if _config._DEBUG_MODE:
            logging.debug(
                f"[laziest-import] Non-interactive environment, auto-selecting "
                f"'{results[0].module_name}' for symbol '{symbol_name}'"
            )
        return results[0].module_name

    print(f"\n[laziest-import] Found {len(results)} match(es) for '{symbol_name}':")
    print("-" * 60)

    for i, r in enumerate(results, 1):
        sig_str = f" {r.signature}" if r.signature else ""
        type_str = f"[{r.symbol_type}]"
        print(f"  {i}. {r.module_name}.{r.symbol_name} {type_str}{sig_str}")

    print(f"  0. Skip (do not register)")
    print("-" * 60)

    try:
        choice = input(f"Select [1-{len(results)}, 0 to skip] (default=1): ").strip()
        if not choice:
            choice = "1"
        if choice == "0":
            return None
        idx = int(choice) - 1
        if 0 <= idx < len(results):
            return results[idx].module_name
        print(f"Invalid choice: {choice}")
        return None
    except (ValueError, EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return None
    except OSError:
        if _config._DEBUG_MODE:
            logging.debug(
                f"[laziest-import] OSError during interactive confirm, "
                f"auto-selecting '{results[0].module_name}'"
            )
        return results[0].module_name


def _handle_symbol_not_found(name: str) -> Optional[str]:
    """Handle a symbol not found error by searching and prompting user."""
    from .._alias import register_alias

    if not _config.is_initialized():
        return None

    if name in _config._CONFIRMED_MAPPINGS:
        return _config._CONFIRMED_MAPPINGS[name]

    results = search_symbol(name)
    if not results:
        return None

    selected_module = _interactive_confirm(results, name)
    if selected_module:
        _config._CONFIRMED_MAPPINGS[name] = selected_module
        register_alias(name, selected_module)
        print(f"[laziest-import] Registered alias: {name} -> {selected_module}")
        return selected_module

    return None


# ── Infer context ───────────────────────────────────────────

def _infer_context() -> Set[str]:
    """Infer the current context by examining loaded modules."""
    loaded = set()

    for alias, lazy_mod in _config._LAZY_MODULES.items():
        cached = object.__getattribute__(lazy_mod, "_cached_module")
        if cached is not None:
            module_name = object.__getattribute__(lazy_mod, "_module_name")
            base_module = module_name.split(".")[0]
            loaded.add(base_module)

    for mod_name in sys.modules.keys():
        if mod_name and not mod_name.startswith("_"):
            base_module = mod_name.split(".")[0]
            if base_module in _config._MODULE_PRIORITY or base_module in _config._ALIAS_MAP.values():
                loaded.add(base_module)

    return loaded


# ── Sharding ────────────────────────────────────────────────

_SHARD_CONFIG = {
    "enabled": True,
    "shard_threshold": 100,
    "loaded_shards": {},
    "shard_index": {},
}


def _get_shard_key(symbol_name: str) -> str:
    if len(symbol_name) >= 2:
        return symbol_name[:2].lower()
    return symbol_name.lower()


def _get_module_shard_name(module_name: str, prefix: str) -> str:
    return f"{module_name}.{prefix}.json"


def _load_shard(
    module_name: str, prefix: str
) -> Dict[str, List[Tuple[str, str, Optional[str]]]]:
    if module_name in _SHARD_CONFIG["loaded_shards"]:
        return _SHARD_CONFIG["loaded_shards"][module_name].get(prefix, {})

    try:
        cache_dir = _get_cache_dir()
        shard_file = cache_dir / "shards" / _get_module_shard_name(module_name, prefix)

        if shard_file.exists():
            with open(shard_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if module_name not in _SHARD_CONFIG["loaded_shards"]:
                _SHARD_CONFIG["loaded_shards"][module_name] = {}

            _SHARD_CONFIG["loaded_shards"][module_name][prefix] = data
            return data
    except Exception:
        pass

    return {}


def _save_shard(
    module_name: str, prefix: str, data: Dict[str, List[Tuple[str, str, Optional[str]]]]
) -> None:
    try:
        cache_dir = _get_cache_dir()
        shard_dir = cache_dir / "shards"
        shard_dir.mkdir(parents=True, exist_ok=True)

        shard_file = shard_dir / _get_module_shard_name(module_name, prefix)

        with open(shard_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        if prefix not in _SHARD_CONFIG["shard_index"]:
            _SHARD_CONFIG["shard_index"][prefix] = []
        if module_name not in _SHARD_CONFIG["shard_index"][prefix]:
            _SHARD_CONFIG["shard_index"][prefix].append(module_name)

    except Exception as e:
        if _config._DEBUG_MODE:
            logging.warning(f"[laziest-import] Failed to save shard: {e}")


def search_with_sharding(symbol_name: str, max_results: int = 5) -> List[SearchResult]:
    """Search for symbol using sharded index (faster for large modules)."""
    results = []

    if symbol_name in _config._SYMBOL_CACHE:
        for loc in _config._SYMBOL_CACHE[symbol_name][:max_results]:
            module_name, sym_type, signature = loc
            results.append(
                SearchResult(
                    module_name=module_name,
                    symbol_name=symbol_name,
                    symbol_type=sym_type,
                    signature=signature,
                    score=1.0,
                    obj=None,
                )
            )
        return results

    if _SHARD_CONFIG["enabled"]:
        shard_key = _get_shard_key(symbol_name)

        if shard_key in _SHARD_CONFIG["shard_index"]:
            for module_name in _SHARD_CONFIG["shard_index"][shard_key]:
                shard = _load_shard(module_name, shard_key)
                if symbol_name in shard:
                    for loc in shard[symbol_name][:max_results]:
                        module_name, sym_type, signature = loc
                        results.append(
                            SearchResult(
                                module_name=module_name,
                                symbol_name=symbol_name,
                                symbol_type=sym_type,
                                signature=signature,
                                score=1.0,
                                obj=None,
                            )
                        )
                    break

    return results


def enable_sharding(enabled: bool = True) -> None:
    """Enable or disable symbol sharding."""
    _SHARD_CONFIG["enabled"] = enabled


def disable_sharding() -> None:
    """Disable symbol sharding."""
    _SHARD_CONFIG["enabled"] = False


def get_sharding_config() -> Dict[str, Any]:
    """Get current sharding configuration."""
    return {
        "enabled": _SHARD_CONFIG["enabled"],
        "shard_threshold": _SHARD_CONFIG["shard_threshold"],
        "loaded_shards_count": len(_SHARD_CONFIG["loaded_shards"]),
        "shard_index_size": len(_SHARD_CONFIG["shard_index"]),
    }


def clear_shard_cache() -> None:
    """Clear loaded shards from memory."""
    _SHARD_CONFIG["loaded_shards"].clear()
    _SHARD_CONFIG["shard_index"].clear()


# ── Incremental build ───────────────────────────────────────

def _build_incremental_symbol_index(timeout: float = 30.0) -> bool:
    """Build symbol index incrementally, only scanning changed packages."""
    if not _config._INCREMENTAL_INDEX_CONFIG.get("enabled", True):
        return False

    existing_tracked = _load_tracked_packages()
    if existing_tracked:
        _config._TRACKED_PACKAGES.clear()
        _config._TRACKED_PACKAGES.update(existing_tracked)

    if not _config._TRACKED_PACKAGES:
        if _config._DEBUG_MODE:
            logging.info("[laziest-import] No existing cache, need full rebuild")
        return False

    from .._cache._incremental import _detect_changed_packages

    new_packages, updated_packages, removed_packages = _detect_changed_packages()

    if not new_packages and not updated_packages and not removed_packages:
        if _config._DEBUG_MODE:
            logging.info(
                "[laziest-import] No package changes detected, skip incremental build"
            )
        return True

    if _config._DEBUG_MODE:
        logging.info(
            f"[laziest-import] Incremental update: "
            f"{len(new_packages)} new, {len(updated_packages)} updated, {len(removed_packages)} removed"
        )

    total_changes = len(new_packages) + len(updated_packages) + len(removed_packages)
    if total_changes > len(_config._TRACKED_PACKAGES) * 0.5:
        if _config._DEBUG_MODE:
            logging.info("[laziest-import] Too many changes, full rebuild recommended")
        return False

    start_time = time.perf_counter()
    depth = _config._SYMBOL_SEARCH_CONFIG["search_depth"]
    scanned_count = 0

    packages_to_remove = removed_packages | updated_packages
    for pkg in packages_to_remove:
        _remove_package_symbols(pkg)

    packages_to_scan = new_packages | updated_packages
    known_modules = _build_known_modules_cache()

    for module_name in known_modules:
        if time.perf_counter() - start_time > timeout:
            if _config._DEBUG_MODE:
                logging.info(
                    f"[laziest-import] Incremental build timed out after {timeout}s"
                )
            break

        top_level = module_name.split(".")[0]
        if top_level not in packages_to_scan:
            continue

        try:
            symbols = _scan_module_symbols(module_name, depth)

            is_stdlib = _is_stdlib_module(module_name)
            target_cache = (
                _config._STDLIB_SYMBOL_CACHE if is_stdlib else _config._THIRD_PARTY_SYMBOL_CACHE
            )

            for sym_name, locations in symbols.items():
                if sym_name not in _config._SYMBOL_CACHE:
                    _config._SYMBOL_CACHE[sym_name] = []
                _config._SYMBOL_CACHE[sym_name].extend(locations)

                if sym_name not in target_cache:
                    target_cache[sym_name] = []
                target_cache[sym_name].extend(locations)

            scanned_count += 1

        except Exception:
            continue

    for pkg in packages_to_scan:
        _track_package(pkg)
    _save_tracked_packages()
    _save_symbol_index(_config._STDLIB_SYMBOL_CACHE, "stdlib")
    _save_symbol_index(_config._THIRD_PARTY_SYMBOL_CACHE, "third_party")

    elapsed = time.perf_counter() - start_time
    _config._CACHE_STATS["last_build_time"] = elapsed
    _config._CACHE_STATS["build_count"] += 1

    if _config._DEBUG_MODE:
        logging.info(
            f"[laziest-import] Incremental index built: scanned {scanned_count} modules in {elapsed:.2f}s"
        )

    _config._set_symbol_index_built(True)
    return True


def _remove_package_symbols(package_name: str) -> None:
    """Remove all symbols from a specific package from the cache."""
    for cache in (_config._SYMBOL_CACHE, _config._STDLIB_SYMBOL_CACHE, _config._THIRD_PARTY_SYMBOL_CACHE):
        to_remove = []
        for symbol, locations in cache.items():
            filtered = [
                loc for loc in locations
                if not loc[0].startswith(package_name + ".") and loc[0] != package_name
            ]
            if filtered:
                cache[symbol] = filtered
            else:
                to_remove.append(symbol)
        for symbol in to_remove:
            del cache[symbol]


def build_symbol_index_incremental() -> bool:
    """Public API for incremental symbol index build."""
    return _build_incremental_symbol_index()


# ── Public API ──────────────────────────────────────────────

def enable_symbol_search(
    interactive: bool = True,
    exact_params: bool = False,
    max_results: int = 5,
    search_depth: int = 1,
    skip_stdlib: bool = False,
) -> None:
    """Enable symbol search functionality."""
    _config._SYMBOL_SEARCH_CONFIG["enabled"] = True
    _config._SYMBOL_SEARCH_CONFIG["interactive"] = interactive
    _config._SYMBOL_SEARCH_CONFIG["exact_params"] = exact_params
    _config._SYMBOL_SEARCH_CONFIG["max_results"] = max_results
    _config._SYMBOL_SEARCH_CONFIG["search_depth"] = search_depth
    _config._SYMBOL_SEARCH_CONFIG["skip_stdlib"] = skip_stdlib


def disable_symbol_search() -> None:
    """Disable symbol search functionality."""
    _config._SYMBOL_SEARCH_CONFIG["enabled"] = False


def is_symbol_search_enabled() -> bool:
    """Check if symbol search is enabled."""
    return _config._SYMBOL_SEARCH_CONFIG["enabled"]


def rebuild_symbol_index() -> None:
    """Rebuild the symbol index."""
    import laziest_import._config as config

    _config._SYMBOL_CACHE.clear()
    _config._STDLIB_SYMBOL_CACHE.clear()
    _config._THIRD_PARTY_SYMBOL_CACHE.clear()
    _config._set_symbol_index_built(False)
    _config._set_stdlib_cache_built(False)
    _config._set_third_party_cache_built(False)

    for cache_type in ["stdlib", "third_party", "all"]:
        cache_path = _get_symbol_index_path(cache_type)
        if cache_path.exists():
            cache_path.unlink()

    _build_symbol_index(force=True)


def get_symbol_search_config() -> Dict[str, Any]:
    """Get current symbol search configuration."""
    return dict(_config._SYMBOL_SEARCH_CONFIG)


def get_symbol_cache_info() -> Dict[str, Any]:
    """Get information about the symbol cache."""
    import laziest_import._config as config

    return {
        "built": config._SYMBOL_INDEX_BUILT,
        "symbol_count": len(_config._SYMBOL_CACHE),
        "stdlib_symbols": len(_config._STDLIB_SYMBOL_CACHE),
        "third_party_symbols": len(_config._THIRD_PARTY_SYMBOL_CACHE),
        "stdlib_built": config._STDLIB_CACHE_BUILT,
        "third_party_built": config._THIRD_PARTY_CACHE_BUILT,
        "confirmed_mappings": len(_config._CONFIRMED_MAPPINGS),
        "tracked_packages": len(_config._TRACKED_PACKAGES),
        "cache_stats": dict(_config._CACHE_STATS),
        "cache_config": dict(_config._CACHE_CONFIG),
    }


def set_symbol_preference(symbol: str, module: str) -> None:
    """Set a preference for symbol resolution."""
    _config._SYMBOL_PREFERENCES[symbol] = module
    if _config._DEBUG_MODE:
        import logging
        logging.debug(f"[laziest-import] Set symbol preference: {symbol} -> {module}")


def get_symbol_preference(symbol: str) -> Optional[str]:
    """Get the preferred module for a symbol."""
    return _config._SYMBOL_PREFERENCES.get(symbol)


def clear_symbol_preference(symbol: str) -> bool:
    """Clear a symbol preference."""
    if symbol in _config._SYMBOL_PREFERENCES:
        del _config._SYMBOL_PREFERENCES[symbol]
        return True
    return False


def list_symbol_conflicts(symbol: str) -> List[Dict[str, Any]]:
    """List all modules that export a symbol."""
    import laziest_import._config as config

    if not config._SYMBOL_INDEX_BUILT:
        _build_symbol_index()

    if symbol not in _config._SYMBOL_CACHE:
        return []

    return [
        {
            "module": loc[0],
            "type": loc[1],
            "signature": loc[2],
            "priority": _config._MODULE_PRIORITY.get(loc[0].split(".")[0], 50),
        }
        for loc in _config._SYMBOL_CACHE[symbol]
    ]


def set_module_priority(module: str, priority: int) -> None:
    """Set priority for a module (higher = more preferred)."""
    _config._MODULE_PRIORITY[module] = priority


def get_module_priority(module: str) -> int:
    """Get the priority for a module."""
    return _config._MODULE_PRIORITY.get(module, 50)


def enable_auto_symbol_resolution(
    auto_threshold: float = 0.7,
    conflict_threshold: float = 0.3,
    warn_on_conflict: bool = True,
) -> None:
    """Enable automatic symbol resolution."""
    _config._SYMBOL_RESOLUTION_CONFIG["auto_symbol"] = True
    _config._SYMBOL_RESOLUTION_CONFIG["auto_threshold"] = auto_threshold
    _config._SYMBOL_RESOLUTION_CONFIG["conflict_threshold"] = conflict_threshold
    _config._SYMBOL_RESOLUTION_CONFIG["warn_on_conflict"] = warn_on_conflict


def disable_auto_symbol_resolution() -> None:
    """Disable automatic symbol resolution."""
    _config._SYMBOL_RESOLUTION_CONFIG["auto_symbol"] = False


def get_symbol_resolution_config() -> Dict[str, Any]:
    """Get symbol resolution configuration."""
    return dict(_config._SYMBOL_RESOLUTION_CONFIG)


def get_loaded_modules_context() -> Set[str]:
    """Get the set of currently loaded module names."""
    return _infer_context()


def get_module_skip_config() -> Dict[str, Any]:
    """Get current module skip configuration."""
    return dict(_config._MODULE_SKIP_CONFIG)


def set_module_skip_config(
    skip_test_modules: Optional[bool] = None,
    skip_internal_modules: Optional[bool] = None,
    skip_large_modules: Optional[bool] = None,
    large_module_threshold: Optional[int] = None,
) -> None:
    """Configure module skip settings."""
    if skip_test_modules is not None:
        _config._MODULE_SKIP_CONFIG["skip_test_modules"] = skip_test_modules
    if skip_internal_modules is not None:
        _config._MODULE_SKIP_CONFIG["skip_internal_modules"] = skip_internal_modules
    if skip_large_modules is not None:
        _config._MODULE_SKIP_CONFIG["skip_large_modules"] = skip_large_modules
    if large_module_threshold is not None:
        _config._MODULE_SKIP_CONFIG["large_module_threshold"] = large_module_threshold


# ── Cache path helpers (localized from _cache subpackage) ────

def _get_symbol_index_path(cache_type: str = "all") -> Path:
    """Get symbol index cache file path."""
    cache_dir = _get_cache_dir()
    if cache_type == "stdlib":
        return cache_dir / "symbol_index_stdlib.json"
    elif cache_type == "third_party":
        return cache_dir / "symbol_index_third_party.json"
    else:
        return cache_dir / "symbol_index.json"


# ── Dataclass re-exports ────────────────────────────────────

@dataclass
class SymbolIndexCache:
    """Symbol index cache with metadata."""
    version: str
    cache_type: str
    timestamp: float
    symbol_count: int
    module_count: int
    symbols: Dict[str, List[Tuple[str, str, Optional[str]]]]
    python_version: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SymbolIndexCache":
        return cls(
            version=data.get("version", "0.0"),
            cache_type=data.get("cache_type", "all"),
            timestamp=data.get("timestamp", 0.0),
            symbol_count=data.get("symbol_count", 0),
            module_count=data.get("module_count", 0),
            symbols=data.get("symbols", {}),
            python_version=data.get("python_version", ""),
        )


# ============== Backward-compatible submodule stubs ==============

# These stubs exist so that `from laziest_import._symbol._scan import X`
# still works.  They simply re-export from this module.

# _scan
class _scan:
    _is_stdlib_module = staticmethod(_is_stdlib_module)
    _scan_module_symbols = staticmethod(_scan_module_symbols)
    _get_signature_hint = staticmethod(_get_signature_hint)


# _index
class _index:
    _build_symbol_index = staticmethod(_build_symbol_index)
    _SYMBOL_INDEX_LOCK = _SYMBOL_INDEX_LOCK


# _search
class _search:
    search_symbol = staticmethod(search_symbol)
    _search_symbol_direct = staticmethod(_search_symbol_direct)
    _search_symbol_enhanced = staticmethod(_search_symbol_enhanced)
    _handle_symbol_not_found = staticmethod(_handle_symbol_not_found)
    _compare_signatures = staticmethod(_compare_signatures)
    _score_symbol_match = staticmethod(_score_symbol_match)
    _warn_symbol_conflict = staticmethod(_warn_symbol_conflict)
    _is_interactive_terminal = staticmethod(_is_interactive_terminal)
    _interactive_confirm = staticmethod(_interactive_confirm)


# _shard
class _shard:
    search_with_sharding = staticmethod(search_with_sharding)
    enable_sharding = staticmethod(enable_sharding)
    disable_sharding = staticmethod(disable_sharding)
    get_sharding_config = staticmethod(get_sharding_config)
    clear_shard_cache = staticmethod(clear_shard_cache)
    _SHARD_CONFIG = _SHARD_CONFIG
    _get_shard_key = staticmethod(_get_shard_key)
    _load_shard = staticmethod(_load_shard)
    _save_shard = staticmethod(_save_shard)


# _api
class _api:
    enable_symbol_search = staticmethod(enable_symbol_search)
    disable_symbol_search = staticmethod(disable_symbol_search)
    is_symbol_search_enabled = staticmethod(is_symbol_search_enabled)
    rebuild_symbol_index = staticmethod(rebuild_symbol_index)
    get_symbol_search_config = staticmethod(get_symbol_search_config)
    get_symbol_cache_info = staticmethod(get_symbol_cache_info)
    set_symbol_preference = staticmethod(set_symbol_preference)
    get_symbol_preference = staticmethod(get_symbol_preference)
    clear_symbol_preference = staticmethod(clear_symbol_preference)
    list_symbol_conflicts = staticmethod(list_symbol_conflicts)
    set_module_priority = staticmethod(set_module_priority)
    get_module_priority = staticmethod(get_module_priority)
    enable_auto_symbol_resolution = staticmethod(enable_auto_symbol_resolution)
    disable_auto_symbol_resolution = staticmethod(disable_auto_symbol_resolution)
    get_symbol_resolution_config = staticmethod(get_symbol_resolution_config)
    get_loaded_modules_context = staticmethod(get_loaded_modules_context)
    get_module_skip_config = staticmethod(get_module_skip_config)
    set_module_skip_config = staticmethod(set_module_skip_config)


# _incremental
class _incremental:
    _build_incremental_symbol_index = staticmethod(_build_incremental_symbol_index)
    _remove_package_symbols = staticmethod(_remove_package_symbols)
    build_symbol_index_incremental = staticmethod(build_symbol_index_incremental)