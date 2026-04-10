"""
Symbol index sharding for laziest-import.

This module contains functions for sharded symbol search (faster for large modules).
"""

from typing import Dict, List, Optional, Tuple
import logging

from .._config import _DEBUG_MODE, _SYMBOL_CACHE, SearchResult


_SHARD_CONFIG = {
    "enabled": True,
    "shard_threshold": 100,  # Symbols before creating shard
    "loaded_shards": {},  # module_name -> shard_data
    "shard_index": {},  # symbol_prefix -> shard_file
}


def _get_shard_key(symbol_name: str) -> str:
    """Get shard key for a symbol (first char or first two chars)."""
    if len(symbol_name) >= 2:
        return symbol_name[:2].lower()
    return symbol_name.lower()


def _get_module_shard_name(module_name: str, prefix: str) -> str:
    """Get shard file name for module and prefix."""
    return f"{module_name}.{prefix}.json"


def _load_shard(
    module_name: str, prefix: str
) -> Dict[str, List[Tuple[str, str, Optional[str]]]]:
    """Load a specific shard for a module."""
    if module_name in _SHARD_CONFIG["loaded_shards"]:
        return _SHARD_CONFIG["loaded_shards"][module_name].get(prefix, {})

    # Try to load from disk
    try:
        from .._cache import _get_cache_dir

        cache_dir = _get_cache_dir()
        shard_file = cache_dir / "shards" / _get_module_shard_name(module_name, prefix)

        if shard_file.exists():
            import json

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
    """Save a shard to disk."""
    try:
        from .._cache import _get_cache_dir

        cache_dir = _get_cache_dir()
        shard_dir = cache_dir / "shards"
        shard_dir.mkdir(parents=True, exist_ok=True)

        shard_file = shard_dir / _get_module_shard_name(module_name, prefix)

        import json

        with open(shard_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        # Update index
        if prefix not in _SHARD_CONFIG["shard_index"]:
            _SHARD_CONFIG["shard_index"][prefix] = []
        if module_name not in _SHARD_CONFIG["shard_index"][prefix]:
            _SHARD_CONFIG["shard_index"][prefix].append(module_name)

    except Exception as e:
        if _DEBUG_MODE:
            logging.warning(f"[laziest-import] Failed to save shard: {e}")


def search_with_sharding(symbol_name: str, max_results: int = 5) -> List[SearchResult]:
    """
    Search for symbol using sharded index (faster for large modules).

    Args:
        symbol_name: Symbol to search for
        max_results: Maximum number of results

    Returns:
        List of SearchResult objects
    """
    results = []

    # First check in-memory cache
    if symbol_name in _SYMBOL_CACHE:
        for loc in _SYMBOL_CACHE[symbol_name][:max_results]:
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

    # If not in memory, try sharding
    if _SHARD_CONFIG["enabled"]:
        shard_key = _get_shard_key(symbol_name)

        # Check shard index
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
                    break  # Found in one shard

    return results


def enable_sharding(enabled: bool = True) -> None:
    """Enable or disable symbol sharding."""
    _SHARD_CONFIG["enabled"] = enabled


def disable_sharding() -> None:
    """Disable symbol sharding."""
    _SHARD_CONFIG["enabled"] = False


def get_sharding_config() -> Dict[str, any]:
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
