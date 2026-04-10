"""
Symbol index persistence for laziest-import.
"""

from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import sys
import json
import time
import logging
import gzip

from .._config import (
    _DEBUG_MODE,
    _CACHE_CONFIG,
    _TRACKED_PACKAGES,
    _SYMBOL_CACHE,
    _STDLIB_SYMBOL_CACHE,
    _THIRD_PARTY_SYMBOL_CACHE,
    get_cache_version as _get_cache_version_from_config,
)

from ._dir import _get_cache_dir, _cleanup_cache_if_needed

# Cache version for compatibility checking (loaded from version.json)
_CACHE_VERSION: str = _get_cache_version_from_config()


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


__all__ = [
    "SymbolIndexCache",
    "_get_symbol_index_path",
    "_get_tracked_packages_path",
    "_save_compressed_json",
    "_load_compressed_json",
    "_should_use_compression",
    "_get_compressed_path",
    "_save_symbol_index",
    "_load_symbol_index",
    "_save_tracked_packages",
    "_load_tracked_packages",
    "_get_package_version",
    "_track_package",
    "_check_package_changed",
]
