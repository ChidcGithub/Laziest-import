"""
Symbol index building for laziest-import.

This module contains functions for building and managing the symbol index.
"""

from typing import Dict, List, Optional, Set, Tuple
import time
import logging
import threading

from .._config import (
    _DEBUG_MODE,
    is_initialized,
    _SYMBOL_SEARCH_CONFIG,
    _SYMBOL_CACHE,
    _STDLIB_SYMBOL_CACHE,
    _THIRD_PARTY_SYMBOL_CACHE,
    _CACHE_STATS,
    _TRACKED_PACKAGES,
    _CACHE_CONFIG,
    _set_symbol_index_built,
    _set_stdlib_cache_built,
    _set_third_party_cache_built,
)
from .._cache import (
    _load_symbol_index,
    _save_symbol_index,
    _load_tracked_packages,
    _save_tracked_packages,
    _track_package,
)
from .._alias import _build_known_modules_cache
from ._scan import _is_stdlib_module, _scan_module_symbols


# Thread lock for symbol index building
_SYMBOL_INDEX_LOCK = threading.Lock()


def _build_symbol_index(
    force: bool = False, max_modules: int = 100, timeout: float = 30.0
) -> None:
    """Build the symbol index by scanning installed packages."""
    # Skip full build during initialization but allow cache loading
    # Only skip if we're not loading from cache
    if not is_initialized() and not force:
        # Still try to load from cache even during initialization
        pass

    # Quick check without lock
    import laziest_import._config as config
    if config._SYMBOL_INDEX_BUILT and not force:
        return

    if not _SYMBOL_SEARCH_CONFIG["cache_enabled"]:
        return

    # Use lock to prevent multiple threads from building simultaneously
    with _SYMBOL_INDEX_LOCK:
        # Double-check after acquiring lock
        if config._SYMBOL_INDEX_BUILT and not force:
            return

        start_time = time.perf_counter()

        # Always load tracked packages for incremental update detection
        existing_tracked = _load_tracked_packages()

        # Try to load from cache first (for both force and non-force)
        stdlib_cache = _load_symbol_index("stdlib")
        third_party_cache = _load_symbol_index("third_party")

        if not force and (stdlib_cache or third_party_cache):
            # Load from cache
            _TRACKED_PACKAGES.clear()
            _TRACKED_PACKAGES.update(existing_tracked)

            if stdlib_cache:
                _STDLIB_SYMBOL_CACHE.clear()
                _STDLIB_SYMBOL_CACHE.update({
                    k: [tuple(loc) for loc in v]
                    for k, v in stdlib_cache.symbols.items()
                })
                _set_stdlib_cache_built(True)
                if _DEBUG_MODE:
                    logging.info(
                        f"[laziest-import] Loaded stdlib symbol index: "
                        f"{len(_STDLIB_SYMBOL_CACHE)} symbols"
                    )

            if third_party_cache:
                _THIRD_PARTY_SYMBOL_CACHE.clear()
                _THIRD_PARTY_SYMBOL_CACHE.update({
                    k: [tuple(loc) for loc in v]
                    for k, v in third_party_cache.symbols.items()
                })
                _set_third_party_cache_built(True)
                if _DEBUG_MODE:
                    logging.info(
                        f"[laziest-import] Loaded third-party symbol index: "
                        f"{len(_THIRD_PARTY_SYMBOL_CACHE)} symbols"
                    )

            if config._STDLIB_CACHE_BUILT or config._THIRD_PARTY_CACHE_BUILT:
                _SYMBOL_CACHE.clear()
                _SYMBOL_CACHE.update(_STDLIB_SYMBOL_CACHE)
                _SYMBOL_CACHE.update(_THIRD_PARTY_SYMBOL_CACHE)

                # Update config module variables
                _set_symbol_index_built(True)

                _CACHE_STATS["symbol_hits"] += 1
                elapsed = time.perf_counter() - start_time
                _CACHE_STATS["last_build_time"] = elapsed

                if _DEBUG_MODE:
                    logging.info(
                        f"[laziest-import] Symbol index loaded from cache: "
                        f"{len(_SYMBOL_CACHE)} symbols in {elapsed:.3f}s"
                    )
                return

    _CACHE_STATS["symbol_misses"] += 1

    _SYMBOL_CACHE.clear()
    _STDLIB_SYMBOL_CACHE.clear()
    _THIRD_PARTY_SYMBOL_CACHE.clear()
    depth = _SYMBOL_SEARCH_CONFIG["search_depth"]

    known_modules = _build_known_modules_cache()

    if _DEBUG_MODE:
        logging.info(
            f"[laziest-import] Building symbol index for {len(known_modules)} modules..."
        )

    priority_packages = {
        "pandas",
        "numpy",
        "matplotlib",
        "seaborn",
        "scipy",
        "sklearn",
        "torch",
        "tensorflow",
        "keras",
        "xgboost",
        "lightgbm",
        "requests",
        "flask",
        "django",
        "fastapi",
        "PIL",
        "cv2",
        "plotly",
        "bokeh",
        "json",
        "os",
        "sys",
        "re",
        "datetime",
        "collections",
        "itertools",
        "pathlib",
        "typing",
        "functools",
        "contextlib",
        "dataclasses",
        # Standard library modules with commonly used symbols
        "math",
        "cmath",
        "statistics",
        "random",
        "decimal",
        "fractions",
    }

    sorted_modules = sorted(
        known_modules,
        key=lambda m: (0 if m.split(".")[0] in priority_packages else 1, m),
    )

    scanned_stdlib = 0
    scanned_third_party = 0
    timed_out = False
    build_success = False
    
    try:
        for module_name in sorted_modules:
            if time.perf_counter() - start_time > timeout:
                timed_out = True
                if _DEBUG_MODE:
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
                    _STDLIB_SYMBOL_CACHE if is_stdlib else _THIRD_PARTY_SYMBOL_CACHE
                )

                for sym_name, locations in symbols.items():
                    if sym_name not in _SYMBOL_CACHE:
                        _SYMBOL_CACHE[sym_name] = []
                    _SYMBOL_CACHE[sym_name].extend(locations)

                    if sym_name not in target_cache:
                        target_cache[sym_name] = []
                    target_cache[sym_name].extend(locations)

                if is_stdlib:
                    scanned_stdlib += 1
                else:
                    scanned_third_party += 1
                    top_level = module_name.split(".")[0]
                    if top_level not in _TRACKED_PACKAGES:
                        _track_package(top_level)

            except Exception:
                continue
        
        build_success = True
        
    except Exception as e:
        if _DEBUG_MODE:
            logging.warning(f"[laziest-import] Symbol index build failed: {e}")
        build_success = False

    # Only update state if we have some data
    if build_success and (scanned_stdlib > 0 or scanned_third_party > 0):
        # Update config module variables
        _set_symbol_index_built(True)
        if scanned_stdlib > 0:
            _set_stdlib_cache_built(True)
        if scanned_third_party > 0:
            _set_third_party_cache_built(True)

        _save_symbol_index(_STDLIB_SYMBOL_CACHE, "stdlib", scanned_stdlib)
        _save_symbol_index(_THIRD_PARTY_SYMBOL_CACHE, "third_party", scanned_third_party)
        _save_tracked_packages()

        elapsed = time.perf_counter() - start_time
        _CACHE_STATS["last_build_time"] = elapsed
        _CACHE_STATS["build_count"] += 1

        if _DEBUG_MODE:
            timeout_msg = " (timed out)" if timed_out else ""
            logging.info(
                f"[laziest-import] Symbol index built: {len(_SYMBOL_CACHE)} symbols "
                f"(stdlib: {scanned_stdlib}, third-party: {scanned_third_party}) "
                f"in {elapsed:.2f}s{timeout_msg}"
            )
    elif timed_out and _DEBUG_MODE:
        logging.info(
            f"[laziest-import] Symbol index build timed out with no data collected"
        )
