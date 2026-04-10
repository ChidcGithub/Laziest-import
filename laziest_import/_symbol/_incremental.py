"""
Incremental symbol index building for laziest-import.

This module contains functions for incremental index updates.
"""

from typing import Dict, List, Optional, Set, Tuple
import time
import logging

from .._config import (
    _DEBUG_MODE,
    _SYMBOL_SEARCH_CONFIG,
    _SYMBOL_CACHE,
    _STDLIB_SYMBOL_CACHE,
    _THIRD_PARTY_SYMBOL_CACHE,
    _CACHE_STATS,
    _TRACKED_PACKAGES,
    _INCREMENTAL_INDEX_CONFIG,
    _set_symbol_index_built,
)
from .._cache import (
    _load_tracked_packages,
    _save_tracked_packages,
    _save_symbol_index,
    _track_package,
    _detect_changed_packages,
)
from .._alias import _build_known_modules_cache
from ._scan import _is_stdlib_module, _scan_module_symbols


def _build_incremental_symbol_index(timeout: float = 30.0) -> bool:
    """Build symbol index incrementally, only scanning changed packages."""
    if not _INCREMENTAL_INDEX_CONFIG.get("enabled", True):
        return False

    # Load existing tracked packages first
    existing_tracked = _load_tracked_packages()
    if existing_tracked:
        _TRACKED_PACKAGES.clear()
        _TRACKED_PACKAGES.update(existing_tracked)

    # Check if we have existing cache
    if not _TRACKED_PACKAGES:
        if _DEBUG_MODE:
            logging.info("[laziest-import] No existing cache, need full rebuild")
        return False

    # Detect changes
    new_packages, updated_packages, removed_packages = _detect_changed_packages()

    if not new_packages and not updated_packages and not removed_packages:
        if _DEBUG_MODE:
            logging.info(
                "[laziest-import] No package changes detected, skip incremental build"
            )
        return True

    if _DEBUG_MODE:
        logging.info(
            f"[laziest-import] Incremental update: "
            f"{len(new_packages)} new, {len(updated_packages)} updated, {len(removed_packages)} removed"
        )

    # Check if too many changes
    total_changes = len(new_packages) + len(updated_packages) + len(removed_packages)
    if total_changes > len(_TRACKED_PACKAGES) * 0.5:  # More than 50% changed
        if _DEBUG_MODE:
            logging.info("[laziest-import] Too many changes, full rebuild recommended")
        return False

    start_time = time.perf_counter()
    depth = _SYMBOL_SEARCH_CONFIG["search_depth"]
    scanned_count = 0

    # Remove symbols from removed/updated packages
    packages_to_remove = removed_packages | updated_packages
    for pkg in packages_to_remove:
        _remove_package_symbols(pkg)

    # Scan new and updated packages
    packages_to_scan = new_packages | updated_packages
    known_modules = _build_known_modules_cache()

    for module_name in known_modules:
        if time.perf_counter() - start_time > timeout:
            if _DEBUG_MODE:
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
                _STDLIB_SYMBOL_CACHE if is_stdlib else _THIRD_PARTY_SYMBOL_CACHE
            )

            for sym_name, locations in symbols.items():
                if sym_name not in _SYMBOL_CACHE:
                    _SYMBOL_CACHE[sym_name] = []
                _SYMBOL_CACHE[sym_name].extend(locations)

                if sym_name not in target_cache:
                    target_cache[sym_name] = []
                target_cache[sym_name].extend(locations)

            scanned_count += 1

        except Exception:
            continue

    # Update tracked packages
    for pkg in packages_to_scan:
        _track_package(pkg)
    _save_tracked_packages()
    _save_symbol_index(_STDLIB_SYMBOL_CACHE, "stdlib")
    _save_symbol_index(_THIRD_PARTY_SYMBOL_CACHE, "third_party")

    elapsed = time.perf_counter() - start_time
    _CACHE_STATS["last_build_time"] = elapsed
    _CACHE_STATS["build_count"] += 1

    if _DEBUG_MODE:
        logging.info(
            f"[laziest-import] Incremental index built: scanned {scanned_count} modules in {elapsed:.2f}s"
        )

    # Update config module variable
    _set_symbol_index_built(True)
    return True


def _remove_package_symbols(package_name: str) -> None:
    """Remove all symbols from a specific package from the cache."""
    # Remove from main cache
    to_remove = []
    for symbol, locations in _SYMBOL_CACHE.items():
        filtered = [
            loc
            for loc in locations
            if not loc[0].startswith(package_name + ".") and loc[0] != package_name
        ]
        if filtered:
            _SYMBOL_CACHE[symbol] = filtered
        else:
            to_remove.append(symbol)

    for symbol in to_remove:
        del _SYMBOL_CACHE[symbol]

    # Remove from stdlib cache
    to_remove = []
    for symbol, locations in _STDLIB_SYMBOL_CACHE.items():
        filtered = [
            loc
            for loc in locations
            if not loc[0].startswith(package_name + ".") and loc[0] != package_name
        ]
        if filtered:
            _STDLIB_SYMBOL_CACHE[symbol] = filtered
        else:
            to_remove.append(symbol)

    for symbol in to_remove:
        del _STDLIB_SYMBOL_CACHE[symbol]

    # Remove from third-party cache
    to_remove = []
    for symbol, locations in _THIRD_PARTY_SYMBOL_CACHE.items():
        filtered = [
            loc
            for loc in locations
            if not loc[0].startswith(package_name + ".") and loc[0] != package_name
        ]
        if filtered:
            _THIRD_PARTY_SYMBOL_CACHE[symbol] = filtered
        else:
            to_remove.append(symbol)

    for symbol in to_remove:
        del _THIRD_PARTY_SYMBOL_CACHE[symbol]


def build_symbol_index_incremental() -> bool:
    """Public API for incremental symbol index build."""
    return _build_incremental_symbol_index()
