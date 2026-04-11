"""
File cache system for laziest-import.
"""

from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import sys
import json
import hashlib
import logging
import threading
import traceback
import atexit
import importlib.util

from .._config import (
    _DEBUG_MODE,
    _CACHE_STATS,
)
# Import config module directly to modify its global variables
from .. import _config

from ._dir import _get_cache_dir, _cleanup_cache_if_needed, _get_cache_size

# Thread lock for cache operations
_CACHE_LOCK = threading.Lock()

# Current caller file info
_CALLER_FILE_PATH: Optional[str] = None
_CALLER_FILE_SHA: Optional[str] = None
_CALLER_LOADED_MODULES: Set[str] = set()


# ============== File Cache System ==============

def _calculate_file_sha(file_path: str) -> Optional[str]:
    """Calculate SHA256 hash of a file."""
    try:
        path = Path(file_path)
        if not path.exists():
            return None
        
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except (OSError, IOError):
        return None


def _get_caller_file_path() -> Optional[str]:
    """Get the path of the file that imported laziest_import."""
    try:
        for frame_info in traceback.extract_stack():
            if 'laziest_import' not in frame_info.filename:
                if not frame_info.filename.startswith('<'):
                    return str(Path(frame_info.filename).resolve())
    except Exception:
        pass
    return None


def _get_cache_file_path(file_path: str) -> Path:
    """Get cache file path for a given source file."""
    path_hash = hashlib.sha256(file_path.encode()).hexdigest()
    return _get_cache_dir() / f"{path_hash}.json"


@dataclass
class FileCache:
    """Cache data for a single file."""
    file_path: str
    file_sha: str
    loaded_modules: List[str]
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileCache":
        return cls(**data)


def _load_file_cache(file_path: str) -> Optional[FileCache]:
    """Load cache for a file."""
    cache_file = _get_cache_file_path(file_path)
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return FileCache.from_dict(data)
    except (json.JSONDecodeError, KeyError, OSError):
        return None


def _save_file_cache(file_path: str, file_sha: str, modules: Set[str]) -> bool:
    """Save cache for a file."""
    try:
        _cleanup_cache_if_needed()
        
        cache = FileCache(
            file_path=file_path,
            file_sha=file_sha,
            loaded_modules=list(modules),
            timestamp=time.time()
        )
        
        cache_file = _get_cache_file_path(file_path)
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache.to_dict(), f, indent=2)
        
        if _DEBUG_MODE:
            logging.info(f"[laziest-import] Saved cache for {file_path}: {len(modules)} modules")
        
        return True
    except (OSError, IOError) as e:
        if _DEBUG_MODE:
            logging.warning(f"Failed to save cache: {e}")
        return False


def _init_file_cache() -> None:
    """Initialize file cache for the current caller file."""
    global _CALLER_FILE_PATH, _CALLER_FILE_SHA, _CALLER_LOADED_MODULES
    
    if not _config._FILE_CACHE_ENABLED:
        return
    
    caller_path = _get_caller_file_path()
    if not caller_path:
        return
    
    _CALLER_FILE_PATH = caller_path
    caller_sha = _calculate_file_sha(caller_path)
    _CALLER_FILE_SHA = caller_sha
    
    if not caller_sha:
        return
    
    cache = _load_file_cache(caller_path)
    
    if cache and cache.file_sha == caller_sha:
        if _DEBUG_MODE:
            logging.info(
                f"[laziest-import] Found valid cache for {caller_path}: "
                f"{len(cache.loaded_modules)} modules"
            )
        _CALLER_LOADED_MODULES = set(cache.loaded_modules)
        _start_background_preload(cache.loaded_modules)
    else:
        if _DEBUG_MODE:
            if cache:
                logging.info(
                    f"[laziest-import] Cache outdated for {caller_path}, will rebuild"
                )
            else:
                logging.info(
                    f"[laziest-import] No cache found for {caller_path}"
                )


def _start_background_preload(modules: List[str]) -> None:
    """Start background thread to preload modules in parallel."""
    from .._config import is_initialized
    
    if not is_initialized():
        return
    
    if not modules:
        return
    
    modules_to_load = [m for m in modules if m not in sys.modules]
    if not modules_to_load:
        return
    
    def _preload_single(module_name: str) -> bool:
        """Preload a single module."""
        try:
            spec = importlib.util.find_spec(module_name)
            if spec:
                import importlib
                importlib.import_module(module_name)
                if _DEBUG_MODE:
                    logging.debug(f"[laziest-import] Preloaded {module_name}")
                return True
        except Exception as e:
            if _DEBUG_MODE:
                logging.debug(f"[laziest-import] Failed to preload {module_name}: {e}")
        return False
    
    def _preload_parallel():
        """Parallel preload worker."""
        if not is_initialized():
            return
        
        max_workers = min(4, len(modules_to_load))
        
        try:
            from concurrent.futures import ThreadPoolExecutor
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                list(executor.map(_preload_single, modules_to_load))
        except ImportError:
            for module_name in modules_to_load:
                _preload_single(module_name)
    
    thread = threading.Thread(target=_preload_parallel, daemon=True)
    thread.start()


def _record_module_load(module_name: str) -> None:
    """Record a module load for the current caller file."""
    global _CALLER_LOADED_MODULES
    # Use lock to prevent race condition with _save_current_cache
    with _CACHE_LOCK:
        _CALLER_LOADED_MODULES.add(module_name)


def _save_current_cache() -> None:
    """Save cache for the current caller file (called at exit)."""
    if not _config._FILE_CACHE_ENABLED:
        return
    
    modules_copy = None
    
    with _CACHE_LOCK:
        if _CALLER_FILE_PATH and _CALLER_FILE_SHA and _CALLER_LOADED_MODULES:
            # Create a copy while holding the lock to prevent iteration errors
            modules_copy = set(_CALLER_LOADED_MODULES)
    
    # Save outside the lock to avoid holding it during I/O
    if _config._FILE_CACHE_ENABLED and _CALLER_FILE_PATH and _CALLER_FILE_SHA and modules_copy:
        _save_file_cache(
            _CALLER_FILE_PATH,
            _CALLER_FILE_SHA,
            modules_copy,
        )


# Register exit handler
atexit.register(_save_current_cache)


# Need to import time for _save_file_cache
import time


# ============== File Cache API ==============

def enable_file_cache() -> None:
    """Enable file cache."""
    _config._FILE_CACHE_ENABLED = True


def disable_file_cache() -> None:
    """Disable file cache."""
    _config._FILE_CACHE_ENABLED = False


def is_file_cache_enabled() -> bool:
    """Check if file cache is enabled."""
    return _config._FILE_CACHE_ENABLED


def clear_file_cache(file_path: Optional[str] = None) -> int:
    """Clear file cache."""
    global _CALLER_LOADED_MODULES
    if file_path:
        cache_file = _get_cache_file_path(file_path)
        if cache_file.exists():
            cache_file.unlink()
            return 1
        return 0
    else:
        # Clear all file caches
        cache_dir = _get_cache_dir()
        count = 0
        for cache_file in cache_dir.glob("*.json"):
            # Skip symbol index files
            if "symbol_index" not in cache_file.name and "tracked_packages" not in cache_file.name:
                cache_file.unlink()
                count += 1
        _CALLER_LOADED_MODULES.clear()
        return count


def get_file_cache_info() -> Dict[str, Any]:
    """Get file cache information."""
    return {
        "enabled": _config._FILE_CACHE_ENABLED,
        "caller_file": _CALLER_FILE_PATH,
        "caller_sha": _CALLER_FILE_SHA,
        "loaded_modules_count": len(_CALLER_LOADED_MODULES),
        "cache_size": _get_cache_size(),
        "cache_dir": str(_get_cache_dir()),
    }


def force_save_cache() -> bool:
    """Force save current cache."""
    _save_current_cache()
    return True


__all__ = [
    "FileCache",
    "_CACHE_LOCK",
    "_CALLER_FILE_PATH",
    "_CALLER_FILE_SHA",
    "_CALLER_LOADED_MODULES",
    "_calculate_file_sha",
    "_get_caller_file_path",
    "_get_cache_file_path",
    "_load_file_cache",
    "_save_file_cache",
    "_init_file_cache",
    "_start_background_preload",
    "_record_module_load",
    "_save_current_cache",
    "enable_file_cache",
    "disable_file_cache",
    "is_file_cache_enabled",
    "clear_file_cache",
    "get_file_cache_info",
    "force_save_cache",
]
