"""
Cache system for laziest-import.
"""

from typing import Dict, List, Optional, Set, Any, Tuple, Union, Callable
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
import gzip
import io

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
    _INCREMENTAL_INDEX_CONFIG,
    _PREHEAT_CONFIG,
    _BACKGROUND_INDEX_BUILDING,
    _BACKGROUND_INDEX_THREAD,
    get_cache_version as _get_cache_version_from_config,
    # Setter functions for state modification
    _set_symbol_index_built,
    _set_stdlib_cache_built,
    _set_third_party_cache_built,
)

# Cache version for compatibility checking (loaded from version.json)
_CACHE_VERSION: str = _get_cache_version_from_config()

# Thread lock for cache operations
_CACHE_LOCK = threading.Lock()

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


def _save_compressed_json(data: Dict[str, Any], file_path: Path) -> bool:
    """Save data as compressed JSON using gzip."""
    try:
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        with gzip.open(file_path, 'wt', encoding='utf-8') as f:
            f.write(json_str)
        return True
    except Exception as e:
        if _DEBUG_MODE:
            logging.warning(f"[laziest-import] Failed to save compressed cache: {e}")
        return False


def _load_compressed_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load compressed JSON data using gzip."""
    try:
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def _should_use_compression(cache_type: str) -> bool:
    """Check if compression should be used for this cache type."""
    return _CACHE_CONFIG.get("enable_compression", False)


def _get_compressed_path(file_path: Path) -> Path:
    """Get the compressed version of a cache file path."""
    return file_path.with_suffix(file_path.suffix + ".gz")


def _save_symbol_index(
    symbols: Dict[str, List[Tuple[str, str, Optional[str]]]],
    cache_type: str = "all",
    module_count: int = 0
) -> bool:
    """Save symbol index to cache file with optional compression."""
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
        use_compression = _should_use_compression(cache_type)
        
        if use_compression:
            compressed_path = _get_compressed_path(cache_path)
            if _save_compressed_json(cache.to_dict(), compressed_path):
                # Remove uncompressed version if exists
                if cache_path.exists():
                    cache_path.unlink()
                if _DEBUG_MODE:
                    logging.info(
                        f"[laziest-import] Saved {cache_type} symbol index (compressed): "
                        f"{len(symbols)} symbols from {module_count} modules"
                    )
                return True
            # Fall back to uncompressed if compression fails
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache.to_dict(), f, indent=2)
        
        # Remove compressed version if exists (switching from compressed to uncompressed)
        compressed_path = _get_compressed_path(cache_path)
        if compressed_path.exists():
            compressed_path.unlink()
        
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
    """Load symbol index from cache file (supports both compressed and uncompressed)."""
    try:
        cache_path = _get_symbol_index_path(cache_type)
        compressed_path = _get_compressed_path(cache_path)
        
        data = None
        
        # Try compressed version first
        if compressed_path.exists():
            data = _load_compressed_json(compressed_path)
            if data is None:
                # Corrupted compressed file, try to remove and fall back
                try:
                    compressed_path.unlink()
                except Exception:
                    pass
        
        # Fall back to uncompressed
        if data is None and cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        if data is None:
            return None
        
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
    
    with _CACHE_LOCK:
        if _CALLER_FILE_PATH and _CALLER_FILE_SHA and _CALLER_LOADED_MODULES:
            _save_file_cache(
                _CALLER_FILE_PATH,
                _CALLER_FILE_SHA,
                _CALLER_LOADED_MODULES.copy(),  # Use copy to avoid modification during save
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
    from ._config import (
        _SYMBOL_INDEX_BUILT as config_symbol_built,
        _STDLIB_CACHE_BUILT as config_stdlib_built,
        _THIRD_PARTY_CACHE_BUILT as config_third_party_built,
    )
    
    _SYMBOL_CACHE.clear()
    _STDLIB_SYMBOL_CACHE.clear()
    _THIRD_PARTY_SYMBOL_CACHE.clear()
    _CONFIRMED_MAPPINGS.clear()
    
    # Modify the config module variables using setters
    _set_symbol_index_built(False)
    _set_stdlib_cache_built(False)
    _set_third_party_cache_built(False)


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


# ============== Background Index Building ==============

def _start_background_index_build(callback: Optional[Callable[[], None]] = None) -> bool:
    """Start background symbol index build.
    
    Args:
        callback: Optional callback to run after build completes
        
    Returns:
        True if background build started, False if already running or disabled
    """
    from ._config import _BACKGROUND_INDEX_BUILDING, _BACKGROUND_INDEX_THREAD
    
    if not _PREHEAT_CONFIG.get("enabled", True):
        return False
    
    if not _PREHEAT_CONFIG.get("async_index_build", True):
        return False
    
    if _BACKGROUND_INDEX_BUILDING:
        return False
    
    if _SYMBOL_INDEX_BUILT:
        return False
    
    def _background_build_worker():
        global _BACKGROUND_INDEX_BUILDING
        from ._config import _BACKGROUND_INDEX_BUILDING as _bg_flag
        from ._symbol import _build_symbol_index
        
        try:
            # Import the flag dynamically to get the reference
            import laziest_import._config as config_module
            config_module._BACKGROUND_INDEX_BUILDING = True
            
            timeout = _INCREMENTAL_INDEX_CONFIG.get("background_timeout", 60.0)
            _build_symbol_index(force=False, timeout=timeout)
            
            if callback:
                callback()
                
        except Exception as e:
            if _DEBUG_MODE:
                logging.warning(f"[laziest-import] Background index build failed: {e}")
        finally:
            import laziest_import._config as config_module
            config_module._BACKGROUND_INDEX_BUILDING = False
    
    thread = threading.Thread(target=_background_build_worker, daemon=True)
    thread.start()
    return True


def _is_background_index_building() -> bool:
    """Check if background index build is in progress."""
    from ._config import _BACKGROUND_INDEX_BUILDING
    return _BACKGROUND_INDEX_BUILDING


def _wait_for_background_index(timeout: float = 30.0) -> bool:
    """Wait for background index build to complete.
    
    Args:
        timeout: Maximum time to wait in seconds
        
    Returns:
        True if build completed, False if timeout
    """
    from ._config import _BACKGROUND_INDEX_THREAD
    
    if not _is_background_index_building():
        return True
    
    start = time.time()
    while time.time() - start < timeout:
        if not _is_background_index_building():
            return True
        time.sleep(0.1)
    
    return False


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
    from ._alias import _build_known_modules_cache
    all_modules = _build_known_modules_cache()
    
    for pkg in new_packages | updated_packages:
        for mod in all_modules:
            if mod.split('.')[0] == pkg:
                modules_to_update.add(mod)
    
    return modules_to_update, False


def enable_incremental_index(enabled: bool = True) -> None:
    """Enable or disable incremental index updates."""
    from ._config import _INCREMENTAL_INDEX_CONFIG
    _INCREMENTAL_INDEX_CONFIG["enabled"] = enabled


def enable_background_build(enabled: bool = True) -> None:
    """Enable or disable background index building."""
    from ._config import _PREHEAT_CONFIG
    _PREHEAT_CONFIG["enabled"] = enabled
    _PREHEAT_CONFIG["async_index_build"] = enabled


def enable_cache_compression(enabled: bool = True) -> None:
    """Enable or disable cache compression."""
    _CACHE_CONFIG["enable_compression"] = enabled


def get_incremental_config() -> Dict[str, Any]:
    """Get incremental index update configuration."""
    from ._config import _INCREMENTAL_INDEX_CONFIG
    return dict(_INCREMENTAL_INDEX_CONFIG)


def get_preheat_config() -> Dict[str, Any]:
    """Get background preheat configuration."""
    from ._config import _PREHEAT_CONFIG
    return dict(_PREHEAT_CONFIG)


def get_package_version(package_name: str) -> Optional[str]:
    """Get the version of an installed package.
    
    Args:
        package_name: The name of the package (e.g., 'numpy', 'pandas')
        
    Returns:
        Version string if found, None otherwise
        
    Examples:
        >>> get_package_version('numpy')
        '1.24.0'
        >>> get_package_version('nonexistent')
        None
    """
    try:
        from importlib.metadata import version, PackageNotFoundError
        # Normalize package name (handle both my-package and my_package)
        normalized = package_name.lower().replace('_', '-')
        return version(normalized)
    except PackageNotFoundError:
        return None
    except Exception:
        return None


def get_all_package_versions() -> Dict[str, str]:
    """Get versions of all installed packages.
    
    Returns:
        Dictionary mapping package names to their versions
    """
    try:
        from importlib.metadata import distributions
        versions = {}
        for dist in distributions():
            name = dist.metadata.get("Name", "")
            ver = dist.metadata.get("Version", "")
            if name and ver:
                # Use normalized name
                import_name = name.lower().replace("-", "_")
                versions[import_name] = ver
        return versions
    except Exception:
        return {}


def get_laziest_import_version() -> str:
    """Get the version of laziest-import library itself.
    
    Priority:
    1. Read from version.json (most reliable for development)
    2. Fallback to importlib.metadata (for installed package)
    
    Returns:
        Version string
    """
    # First try to read from version.json (same source as __version__)
    try:
        import os
        version_file = os.path.join(os.path.dirname(__file__), 'version.json')
        if os.path.exists(version_file):
            with open(version_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                version = data.get('_current_version')
                if version:
                    return version
    except Exception:
        pass
    
    # Fallback to importlib.metadata for installed package
    try:
        from importlib.metadata import version
        return version('laziest-import')
    except Exception:
        pass
    
    return 'unknown'
