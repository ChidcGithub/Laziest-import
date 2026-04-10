"""
Cache directory management for laziest-import.
"""

from typing import Optional, Union
from pathlib import Path
import logging

from .._config import (
    _DEBUG_MODE,
    _CACHE_CONFIG,
)

# Cache directory (can be customized)
_CACHE_DIR: Optional[Path] = None


# ============== Cache Directory Management ==============

def _get_default_cache_dir() -> Path:
    """Get default cache directory path."""
    return Path.home() / ".laziest_import" / "cache"


def _get_cache_dir() -> Path:
    """Get or create cache directory."""
    cache_dir = _CACHE_DIR if _CACHE_DIR is not None else _get_default_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _get_cache_size() -> int:
    """Get total cache size in bytes."""
    cache_dir = _get_cache_dir()
    total_size = 0
    try:
        for cache_file in cache_dir.glob("*.json"):
            total_size += cache_file.stat().st_size
    except (OSError, IOError):
        pass
    return total_size


def _cleanup_cache_if_needed() -> None:
    """Clean up old cache files if cache size exceeds limit."""
    max_size_bytes = _CACHE_CONFIG.get("max_cache_size_mb", 100) * 1024 * 1024
    current_size = _get_cache_size()
    
    if current_size <= max_size_bytes:
        return
    
    cache_dir = _get_cache_dir()
    cache_files = []
    try:
        for cache_file in cache_dir.glob("*.json"):
            cache_files.append((cache_file, cache_file.stat().st_mtime))
    except (OSError, IOError):
        return
    
    cache_files.sort(key=lambda x: x[1])
    
    for cache_file, _ in cache_files:
        if current_size <= max_size_bytes:
            break
        try:
            file_size = cache_file.stat().st_size
            cache_file.unlink()
            current_size -= file_size
            if _DEBUG_MODE:
                logging.debug(f"[laziest-import] Removed old cache file: {cache_file.name}")
        except (OSError, IOError):
            continue


def _check_cache_size_before_save() -> bool:
    """Check if we should save cache based on size limit."""
    max_size_bytes = _CACHE_CONFIG.get("max_cache_size_mb", 100) * 1024 * 1024
    current_size = _get_cache_size()
    return current_size < max_size_bytes * 0.9


def set_cache_dir(path: Union[str, Path]) -> None:
    """Set custom cache directory."""
    global _CACHE_DIR
    _CACHE_DIR = Path(path).resolve()


def get_cache_dir() -> Path:
    """Get current cache directory path."""
    return _get_cache_dir()


def reset_cache_dir() -> None:
    """Reset cache directory to default location."""
    global _CACHE_DIR
    _CACHE_DIR = None


# Export internal functions for use within _cache subpackage
__all__ = [
    "_get_default_cache_dir",
    "_get_cache_dir",
    "_get_cache_size",
    "_cleanup_cache_if_needed",
    "_check_cache_size_before_save",
    "set_cache_dir",
    "get_cache_dir",
    "reset_cache_dir",
]
