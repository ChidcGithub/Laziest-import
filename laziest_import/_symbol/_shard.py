# Backward-compatible redirect to laziest_import._symbol
from . import (
    search_with_sharding as search_with_sharding,
    enable_sharding as enable_sharding,
    disable_sharding as disable_sharding,
    get_sharding_config as get_sharding_config,
    clear_shard_cache as clear_shard_cache,
    _SHARD_CONFIG as _SHARD_CONFIG,
    _get_shard_key as _get_shard_key,
    _load_shard as _load_shard,
    _save_shard as _save_shard,
)

__all__ = [
    "search_with_sharding",
    "enable_sharding",
    "disable_sharding",
    "get_sharding_config",
    "clear_shard_cache",
    "_SHARD_CONFIG",
    "_get_shard_key",
    "_load_shard",
    "_save_shard",
]