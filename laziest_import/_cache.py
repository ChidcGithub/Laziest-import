"""
Cache system for laziest-import.
"""

from typing import Dict, List, Optional, Set, Any, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import sys
import json
import hashlib
import time
import logging
import threading
import traceback
import atexit
import importlib.util

from ._config import (
    _DEBUG_MODE,
    _FILE_CACHE_ENABLED,
    _CACHE_CONFIG,
    _CACHE_STATS,
    _TRACKED_PACKAGES,
    _SYMBOL_CACHE,
    _STDLIB_SYMBOL_CACHE,
    _THIRD_PARTY_SYMBOL_CACHE,
    _SYMBOL_INDEX_BUILT,
    _STDLIB_CACHE_BUILT,
    _THIRD_PARTY_CACHE_BUILT,
    _CONFIRMED_MAPPINGS,
)

# Cache version for compatibility checking
_CACHE_VERSION: str = "0.0.2.3"

# Current caller file info
_CALLER_FILE_PATH: Optional[str] = None
_CALLER_FILE_SHA: Optional[str] = None
_CALLER_LOADED_MODULES: Set[str] = set()

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


# ============== Symbol Index Persistence ==============

def _get_symbol_index_path(cache_type: str = "all") -> Path:
    """Get symbol index cache file path."""
    cache_dir = _get_cache_dir()
    if cache_type == "stdlib":
        return cache_dir / "symbol_index_stdlib.json"
    elif cache_type == "third_party":
        return cache_dir / "symbol_index_third_party.json"
    else:
        return cache_dir / "symbol_index.json"


def _get_tracked_packages_path() -> Path:
    """Get tracked packages file path."""
    return _get_cache_dir() / "tracked_packages.json"


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
        return {
            "version": self.version,
            "cache_type": self.cache_type,
            "timestamp": self.timestamp,
            "symbol_count": self.symbol_count,
            "module_count": self.module_count,
            "python_version": self.python_version,
            "symbols": self.symbols,
        }
    
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


def _save_symbol_index(
    symbols: Dict[str, List[Tuple[str, str, Optional[str]]]],
    cache_type: str = "all",
    module_count: int = 0
) -> bool:
    """Save symbol index to cache file."""
    try:
        _cleanup_cache_if_needed()
        
        serializable_symbols = {}
        for name, locations in symbols.items():
            serializable_symbols[name] = [list(loc) for loc in locations]
        
        cache = SymbolIndexCache(
            version=_CACHE_VERSION,
            cache_type=cache_type,
            timestamp=time.time(),
            symbol_count=len(symbols),
            module_count=module_count,
            symbols=serializable_symbols,
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )
        
        cache_path = _get_symbol_index_path(cache_type)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache.to_dict(), f, indent=2)
        
        if _DEBUG_MODE:
            logging.info(
                f"[laziest-import] Saved {cache_type} symbol index: "
                f"{len(symbols)} symbols from {module_count} modules"
            )
        return True
    except Exception as e:
        if _DEBUG_MODE:
            logging.warning(f"[laziest-import] Failed to save symbol index: {e}")
        return False


def _load_symbol_index(cache_type: str = "all") -> Optional[SymbolIndexCache]:
    """Load symbol index from cache file."""
    try:
        cache_path = _get_symbol_index_path(cache_type)
        if not cache_path.exists():
            return None
        
        with open(cache_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cache = SymbolIndexCache.from_dict(data)
        
        if cache.version != _CACHE_VERSION:
            if _DEBUG_MODE:
                logging.info(
                    f"[laziest-import] Symbol index version mismatch: "
                    f"{cache.version} != {_CACHE_VERSION}, will rebuild"
                )
            return None
        
        current_py = f"{sys.version_info.major}.{sys.version_info.minor}"
        if cache.python_version and not cache.python_version.startswith(current_py):
            if _DEBUG_MODE:
                logging.info(
                    f"[laziest-import] Python version changed: "
                    f"{cache.python_version} -> {current_py}, will rebuild"
                )
            return None
        
        ttl = _CACHE_CONFIG.get("symbol_index_ttl", 86400)
        if cache_type == "stdlib":
            ttl = _CACHE_CONFIG.get("stdlib_cache_ttl", 604800)
        elif cache_type == "third_party":
            ttl = _CACHE_CONFIG.get("third_party_cache_ttl", 86400)
        
        if time.time() - cache.timestamp > ttl:
            if _DEBUG_MODE:
                logging.info(
                    f"[laziest-import] {cache_type} symbol index expired (TTL: {ttl}s)"
                )
            return None
        
        return cache
    except Exception as e:
        if _DEBUG_MODE:
            logging.warning(f"[laziest-import] Failed to load symbol index: {e}")
        return None


def _save_tracked_packages() -> bool:
    """Save tracked packages information."""
    try:
        path = _get_tracked_packages_path()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(_TRACKED_PACKAGES, f, indent=2)
        return True
    except Exception as e:
        if _DEBUG_MODE:
            logging.warning(f"[laziest-import] Failed to save tracked packages: {e}")
        return False


def _load_tracked_packages() -> Dict[str, Dict[str, Any]]:
    """Load tracked packages information."""
    try:
        path = _get_tracked_packages_path()
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _get_package_version(package_name: str) -> Optional[str]:
    """Get installed version of a package."""
    try:
        from importlib.metadata import version as get_version
        return get_version(package_name)
    except Exception:
        return None


def _track_package(package_name: str, module_count: int = 0) -> None:
    """Track a package for incremental updates."""
    global _TRACKED_PACKAGES
    version = _get_package_version(package_name)
    _TRACKED_PACKAGES[package_name] = {
        "version": version,
        "mtime": time.time(),
        "module_count": module_count,
    }


def _check_package_changed(package_name: str) -> bool:
    """Check if a package has changed since last scan."""
    if package_name not in _TRACKED_PACKAGES:
        return True
    
    tracked = _TRACKED_PACKAGES[package_name]
    current_version = _get_package_version(package_name)
    
    if current_version and tracked.get("version") != current_version:
        return True
    
    return False


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
    
    if not _FILE_CACHE_ENABLED:
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
    from ._config import _INITIALIZED
    
    if not _INITIALIZED:
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
        if not _INITIALIZED:
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
    _CALLER_LOADED_MODULES.add(module_name)


def _save_current_cache() -> None:
    """Save cache for the current caller file (called at exit)."""
    if not _FILE_CACHE_ENABLED:
        return
    
    if _CALLER_FILE_PATH and _CALLER_FILE_SHA and _CALLER_LOADED_MODULES:
        _save_file_cache(
            _CALLER_FILE_PATH,
            _CALLER_FILE_SHA,
            _CALLER_LOADED_MODULES,
        )


# Register exit handler
atexit.register(_save_current_cache)


# ============== Cache Configuration API ==============

def set_cache_config(
    symbol_index_ttl: Optional[int] = None,
    stdlib_cache_ttl: Optional[int] = None,
    third_party_cache_ttl: Optional[int] = None,
    enable_compression: Optional[bool] = None,
    max_cache_size_mb: Optional[int] = None,
) -> None:
    """Configure cache settings."""
    if symbol_index_ttl is not None:
        _CACHE_CONFIG["symbol_index_ttl"] = symbol_index_ttl
    if stdlib_cache_ttl is not None:
        _CACHE_CONFIG["stdlib_cache_ttl"] = stdlib_cache_ttl
    if third_party_cache_ttl is not None:
        _CACHE_CONFIG["third_party_cache_ttl"] = third_party_cache_ttl
    if enable_compression is not None:
        _CACHE_CONFIG["enable_compression"] = enable_compression
    if max_cache_size_mb is not None:
        _CACHE_CONFIG["max_cache_size_mb"] = max_cache_size_mb


def get_cache_config() -> Dict[str, Any]:
    """Get current cache configuration."""
    return dict(_CACHE_CONFIG)


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    total_hits = _CACHE_STATS["symbol_hits"] + _CACHE_STATS["module_hits"]
    total_misses = _CACHE_STATS["symbol_misses"] + _CACHE_STATS["module_misses"]
    total_requests = total_hits + total_misses
    hit_rate = total_hits / total_requests if total_requests > 0 else 0.0
    
    return {
        **_CACHE_STATS,
        "hit_rate": hit_rate,
        "total_requests": total_requests,
    }


def reset_cache_stats() -> None:
    """Reset cache statistics."""
    global _CACHE_STATS
    _CACHE_STATS = {
        "symbol_hits": 0,
        "symbol_misses": 0,
        "module_hits": 0,
        "module_misses": 0,
        "last_build_time": 0.0,
        "build_count": 0,
    }


def invalidate_package_cache(package_name: str) -> bool:
    """Invalidate cache for a specific package."""
    global _TRACKED_PACKAGES, _THIRD_PARTY_CACHE_BUILT
    
    # Return False if package not tracked
    if package_name not in _TRACKED_PACKAGES:
        return False
    
    del _TRACKED_PACKAGES[package_name]
    
    # Remove symbols from cache
    to_remove = []
    for symbol, locations in _SYMBOL_CACHE.items():
        locations = [loc for loc in locations if not loc[0].startswith(package_name)]
        if locations:
            _SYMBOL_CACHE[symbol] = locations
        else:
            to_remove.append(symbol)
    
    for symbol in to_remove:
        del _SYMBOL_CACHE[symbol]
    
    # Also check third-party cache
    to_remove = []
    for symbol, locations in _THIRD_PARTY_SYMBOL_CACHE.items():
        locations = [loc for loc in locations if not loc[0].startswith(package_name)]
        if locations:
            _THIRD_PARTY_SYMBOL_CACHE[symbol] = locations
        else:
            to_remove.append(symbol)
    
    for symbol in to_remove:
        del _THIRD_PARTY_SYMBOL_CACHE[symbol]
    
    _save_tracked_packages()
    return True


def get_cache_version() -> str:
    """Get current cache version."""
    return _CACHE_VERSION


def clear_symbol_cache() -> None:
    """Clear the symbol cache (memory only)."""
    global _SYMBOL_INDEX_BUILT, _STDLIB_CACHE_BUILT, _THIRD_PARTY_CACHE_BUILT
    _SYMBOL_CACHE.clear()
    _STDLIB_SYMBOL_CACHE.clear()
    _THIRD_PARTY_SYMBOL_CACHE.clear()
    _CONFIRMED_MAPPINGS.clear()
    _SYMBOL_INDEX_BUILT = False
    _STDLIB_CACHE_BUILT = False
    _THIRD_PARTY_CACHE_BUILT = False


# ============== File Cache API ==============

def enable_file_cache() -> None:
    """Enable file cache."""
    global _FILE_CACHE_ENABLED
    _FILE_CACHE_ENABLED = True


def disable_file_cache() -> None:
    """Disable file cache."""
    global _FILE_CACHE_ENABLED
    _FILE_CACHE_ENABLED = False


def is_file_cache_enabled() -> bool:
    """Check if file cache is enabled."""
    return _FILE_CACHE_ENABLED


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
        "enabled": _FILE_CACHE_ENABLED,
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
