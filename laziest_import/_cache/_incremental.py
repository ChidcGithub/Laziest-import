"""
Incremental index update detection for laziest-import.
"""

from typing import Dict, Optional, Set, Tuple, Any
import logging

from .._config import (
    _DEBUG_MODE,
    _TRACKED_PACKAGES,
    _INCREMENTAL_INDEX_CONFIG,
)

from ._symbol_index import (
    _save_tracked_packages,
    _check_package_changed,
)


# ============== Incremental Index Update ==============

def _get_installed_packages() -> Set[str]:
    """Get set of installed top-level packages."""
    try:
        from importlib.metadata import distributions
        packages = set()
        for dist in distributions():
            # Get top-level package names
            name = dist.metadata.get("Name", "")
            if name:
                # Convert package name to import name (e.g., my-package -> my_package)
                import_name = name.lower().replace("-", "_")
                packages.add(import_name)
        return packages
    except Exception:
        return set()


def _detect_changed_packages() -> Tuple[Set[str], Set[str], Set[str]]:
    """Detect package changes since last scan.
    
    Returns:
        Tuple of (new_packages, updated_packages, removed_packages)
    """
    if not _INCREMENTAL_INDEX_CONFIG.get("enabled", True):
        return set(), set(), set()
    
    current_packages = _get_installed_packages()
    tracked_packages = set(_TRACKED_PACKAGES.keys())
    
    new_packages = current_packages - tracked_packages
    removed_packages = tracked_packages - current_packages
    
    # Check for version updates
    updated_packages = set()
    if _INCREMENTAL_INDEX_CONFIG.get("check_version", True):
        for pkg in tracked_packages & current_packages:
            if _check_package_changed(pkg):
                updated_packages.add(pkg)
    
    return new_packages, updated_packages, removed_packages


def _get_incremental_update_modules() -> Tuple[Set[str], bool]:
    """Get modules that need incremental update.
    
    Returns:
        Tuple of (modules_to_update, needs_full_rebuild)
    """
    new_packages, updated_packages, removed_packages = _detect_changed_packages()
    
    # If no existing cache, need full rebuild
    if not _TRACKED_PACKAGES:
        return set(), True
    
    # If too many changes, full rebuild might be faster
    total_changes = len(new_packages) + len(updated_packages) + len(removed_packages)
    if total_changes > len(_TRACKED_PACKAGES) * 0.3:  # More than 30% changed
        return set(), True
    
    # Collect modules to update
    modules_to_update = set()
    
    # Add new package modules
    from .._alias import _build_known_modules_cache
    all_modules = _build_known_modules_cache()
    
    for pkg in new_packages | updated_packages:
        for mod in all_modules:
            if mod.split('.')[0] == pkg:
                modules_to_update.add(mod)
    
    return modules_to_update, False


def enable_incremental_index(enabled: bool = True) -> None:
    """Enable or disable incremental index updates."""
    from .._config import _INCREMENTAL_INDEX_CONFIG
    _INCREMENTAL_INDEX_CONFIG["enabled"] = enabled


def get_incremental_config() -> Dict[str, Any]:
    """Get incremental index update configuration."""
    from .._config import _INCREMENTAL_INDEX_CONFIG
    return dict(_INCREMENTAL_INDEX_CONFIG)


__all__ = [
    "_get_installed_packages",
    "_detect_changed_packages",
    "_get_incremental_update_modules",
    "enable_incremental_index",
    "get_incremental_config",
]
