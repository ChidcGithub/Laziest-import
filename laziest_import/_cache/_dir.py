"""
Cache directory management for laziest-import.
"""

import logging
import re
from pathlib import Path
from typing import Optional, Union

from .. import _config

# Cache directory (can be customized)
_CACHE_DIR: Optional[Path] = None

# Files owned by this library inside the cache dir:
# - symbol_index_stdlib.json / symbol_index_third_party.json (+ .gz)
# - tracked_packages.json
# - <sha256>.json per-caller file caches
_OWNED_PATTERNS = ("symbol_index_*.json*", "tracked_packages.json*")
_SHA256_NAME_RE = re.compile(r"^[0-9a-f]{64}\.json$")


def _is_owned_cache_file(path: Path) -> bool:
    """Check whether a file inside the cache dir was created by this library."""
    name = path.name
    if any(path.match(pat) for pat in _OWNED_PATTERNS):
        return True
    return _SHA256_NAME_RE.match(name) is not None


def _iter_cache_files(cache_dir: Path):
    """Yield cache files owned by this library."""
    try:
        for entry in cache_dir.iterdir():
            if entry.is_file() and _is_owned_cache_file(entry):
                yield entry
    except OSError:
        return


def _get_default_cache_dir() -> Path:
    """Get default cache directory path."""
    return Path.home() / ".laziest_import" / "cache"


def _get_cache_dir() -> Path:
    """Get or create cache directory."""
    cache_dir = _CACHE_DIR if _CACHE_DIR is not None else _get_default_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _get_cache_size() -> int:
    """Get total size of cache files owned by this library, in bytes."""
    cache_dir = _get_cache_dir()
    total_size = 0
    try:
        for cache_file in _iter_cache_files(cache_dir):
            total_size += cache_file.stat().st_size
    except OSError:
        pass
    return total_size


def _cleanup_cache_if_needed() -> None:
    """Clean up old cache files if cache size exceeds limit."""
    c = _config
    max_size_mb = c._CACHE_CONFIG.get("max_cache_size_mb", 100)
    if max_size_mb <= 0:
        return
    max_size_bytes = max_size_mb * 1024 * 1024
    current_size = _get_cache_size()

    if current_size <= max_size_bytes:
        return

    cache_dir = _get_cache_dir()
    cache_files = []
    try:
        for cache_file in _iter_cache_files(cache_dir):
            cache_files.append((cache_file, cache_file.stat().st_mtime))
    except OSError:
        return

    cache_files.sort(key=lambda x: x[1])

    for cache_file, _ in cache_files:
        if current_size <= max_size_bytes:
            break
        try:
            file_size = cache_file.stat().st_size
            cache_file.unlink()
            current_size -= file_size
            if c._DEBUG_MODE:
                logging.debug(f"[laziest-import] Removed old cache file: {cache_file.name}")
        except OSError:
            continue


def _check_cache_size_before_save() -> bool:
    """Check if we should save cache based on size limit."""
    c = _config
    max_size_mb = c._CACHE_CONFIG.get("max_cache_size_mb", 100)
    if max_size_mb <= 0:
        return True
    max_size_bytes = max_size_mb * 1024 * 1024
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
    "_check_cache_size_before_save",
    "_cleanup_cache_if_needed",
    "_get_cache_dir",
    "_get_cache_size",
    "_get_default_cache_dir",
    "get_cache_dir",
    "reset_cache_dir",
    "set_cache_dir",
]
