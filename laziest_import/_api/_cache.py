from pathlib import Path
from typing import Any, Dict, Optional, Union

from .. import _config
from .._cache import (
    clear_symbol_cache,
    get_cache_stats,
    reset_cache_stats,
    set_cache_config,
    get_cache_config,
    clear_file_cache,
    get_file_cache_info,
    force_save_cache,
    enable_file_cache,
    disable_file_cache,
    is_file_cache_enabled,
    set_cache_dir,
    get_cache_dir,
    reset_cache_dir,
    enable_cache_compression,
)
from .._symbol import rebuild_symbol_index


class CacheSymbolsNamespace:
    def clear(self) -> None:
        clear_symbol_cache()

    def reset(self) -> None:
        clear_symbol_cache()
        rebuild_symbol_index()

    @property
    def count(self) -> int:
        return len(_config._SYMBOL_CACHE)

    @property
    def stdlib_count(self) -> int:
        return len(_config._STDLIB_SYMBOL_CACHE)

    @property
    def third_party_count(self) -> int:
        return len(_config._THIRD_PARTY_SYMBOL_CACHE)

    def __repr__(self) -> str:
        return (
            f"<SymbolCache: {self.count} total, "
            f"{self.stdlib_count} stdlib, "
            f"{self.third_party_count} third-party>"
        )


class CacheFilesNamespace:
    def clear(self, file_path: Optional[str] = None) -> int:
        return clear_file_cache(file_path)

    def info(self) -> Dict[str, Any]:
        return get_file_cache_info()

    def force_save(self) -> bool:
        return force_save_cache()

    @property
    def enabled(self) -> bool:
        return is_file_cache_enabled()

    @enabled.setter
    def enabled(self, value: bool) -> None:
        if value:
            enable_file_cache()
        else:
            disable_file_cache()

    def __repr__(self) -> str:
        info = get_file_cache_info()
        return f"<FileCache: enabled={info['enabled']}, files={info['loaded_modules_count']}>"


class CacheStatsNamespace:
    def _get_stats(self) -> Dict[str, Any]:
        return get_cache_stats()

    @property
    def hit_rate(self) -> float:
        return self._get_stats().get("hit_rate", 0.0)

    @property
    def symbol_hits(self) -> int:
        return self._get_stats().get("symbol_hits", 0)

    @property
    def symbol_misses(self) -> int:
        return self._get_stats().get("symbol_misses", 0)

    @property
    def module_hits(self) -> int:
        return self._get_stats().get("module_hits", 0)

    @property
    def module_misses(self) -> int:
        return self._get_stats().get("module_misses", 0)

    @property
    def total_requests(self) -> int:
        return self._get_stats().get("total_requests", 0)

    @property
    def last_build_time(self) -> float:
        return self._get_stats().get("last_build_time", 0.0)

    @property
    def build_count(self) -> int:
        return self._get_stats().get("build_count", 0)

    def reset(self) -> None:
        reset_cache_stats()

    def __getitem__(self, key: str) -> Any:
        stats = self._get_stats()
        if key not in stats:
            raise KeyError(key)
        return stats[key]

    def __getattr__(self, name: str) -> Any:
        stats = self._get_stats()
        if name in stats:
            return stats[name]
        raise AttributeError(f"CacheStats has no attribute '{name}'")

    def __contains__(self, key: str) -> bool:
        return key in self._get_stats()

    def keys(self) -> list:
        return list(self._get_stats().keys())

    def items(self) -> list:
        return list(self._get_stats().items())

    def __repr__(self) -> str:
        s = self._get_stats()
        return f"<CacheStats: hits={s.get('total_requests', 0)}, rate={s.get('hit_rate', 0):.1%}>"


class CacheConfigNamespace:
    def __getitem__(self, key: str) -> Any:
        cfg = get_cache_config()
        if key not in cfg:
            raise KeyError(key)
        return cfg[key]

    def __setitem__(self, key: str, value: Any) -> None:
        set_cache_config(**{key: value})

    @property
    def max_size_mb(self) -> int:
        return get_cache_config().get("max_cache_size_mb", 100)

    @max_size_mb.setter
    def max_size_mb(self, value: int) -> None:
        set_cache_config(max_cache_size_mb=value)

    @property
    def symbol_index_ttl(self) -> int:
        return get_cache_config().get("symbol_index_ttl", 86400)

    @symbol_index_ttl.setter
    def symbol_index_ttl(self, value: int) -> None:
        set_cache_config(symbol_index_ttl=value)

    @property
    def stdlib_cache_ttl(self) -> int:
        return get_cache_config().get("stdlib_cache_ttl", 604800)

    @stdlib_cache_ttl.setter
    def stdlib_cache_ttl(self, value: int) -> None:
        set_cache_config(stdlib_cache_ttl=value)

    @property
    def third_party_cache_ttl(self) -> int:
        return get_cache_config().get("third_party_cache_ttl", 86400)

    @third_party_cache_ttl.setter
    def third_party_cache_ttl(self, value: int) -> None:
        set_cache_config(third_party_cache_ttl=value)

    @property
    def symbol_index_enabled(self) -> bool:
        return get_cache_config().get("symbol_index_enabled", True)

    @symbol_index_enabled.setter
    def symbol_index_enabled(self, value: bool) -> None:
        set_cache_config(symbol_index_enabled=value)

    @property
    def compression(self) -> bool:
        return get_cache_config().get("enable_compression", False)

    @compression.setter
    def compression(self, value: bool) -> None:
        enable_cache_compression(value)

    def snapshot(self) -> Dict[str, Any]:
        return dict(get_cache_config())

    def export(self, path: Optional[str] = None) -> str:
        import json
        data = dict(get_cache_config())
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        return json.dumps(data, indent=2)

    def __repr__(self) -> str:
        return f"<CacheConfig: max={self.max_size_mb}MB, compression={self.compression}>"


class CacheNamespace:
    @property
    def symbols(self) -> CacheSymbolsNamespace:
        return _CACHE_SYMBOLS_NS

    @property
    def files(self) -> CacheFilesNamespace:
        return _CACHE_FILES_NS

    @property
    def stats(self) -> CacheStatsNamespace:
        return _CACHE_STATS_NS

    @property
    def config(self) -> CacheConfigNamespace:
        return _CACHE_CONFIG_NS

    def clear(self) -> None:
        clear_symbol_cache()
        clear_file_cache()
        for lm in _config._LAZY_MODULES.values():
            object.__setattr__(lm, "_cached_module", None)
            object.__setattr__(lm, "_submodule_cache", {})
        _config._LAZY_MODULES.clear()

    @property
    def dir(self) -> Path:
        return get_cache_dir()

    @dir.setter
    def dir(self, value: Union[str, Path]) -> None:
        set_cache_dir(value)

    def reset_dir(self) -> None:
        reset_cache_dir()

    @property
    def compression(self) -> bool:
        return get_cache_config().get("enable_compression", False)

    @compression.setter
    def compression(self, value: bool) -> None:
        enable_cache_compression(value)

    def __repr__(self) -> str:
        return f"<CacheNamespace: dir={self.dir}>"


_CACHE_SYMBOLS_NS = CacheSymbolsNamespace()
_CACHE_FILES_NS = CacheFilesNamespace()
_CACHE_STATS_NS = CacheStatsNamespace()
_CACHE_CONFIG_NS = CacheConfigNamespace()


def clear_cache() -> None:
    clear_symbol_cache()
    clear_file_cache()
    for lm in _config._LAZY_MODULES.values():
        object.__setattr__(lm, "_cached_module", None)
        object.__setattr__(lm, "_submodule_cache", {})
    _config._LAZY_MODULES.clear()
