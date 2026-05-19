from typing import Any, Dict, List, Optional

from .. import _config
from .._symbol import (
    search_symbol,
    rebuild_symbol_index,
    get_symbol_search_config,
    get_symbol_cache_info,
    set_symbol_preference,
    get_symbol_preference,
    clear_symbol_preference,
    enable_symbol_search,
    disable_symbol_search,
    is_symbol_search_enabled,
    enable_auto_symbol_resolution,
    disable_auto_symbol_resolution,
    get_symbol_resolution_config,
    get_loaded_modules_context,
    set_module_priority,
    get_module_priority,
    get_module_skip_config,
    set_module_skip_config,
    search_with_sharding,
    enable_sharding,
    disable_sharding,
    get_sharding_config,
    clear_shard_cache,
    build_symbol_index_incremental,
    _is_stdlib_module,
    _scan_module_symbols,
    _build_symbol_index,
    _search_symbol_direct,
    _search_symbol_enhanced,
    _handle_symbol_not_found,
    _build_incremental_symbol_index,
    _remove_package_symbols,
)
from .._which import which, which_all


class SymbolIndexNamespace:
    def build(self, force: bool = False, max_modules: int = 100, timeout: float = 30.0) -> None:
        _build_symbol_index(force=force, max_modules=max_modules, timeout=timeout)

    def rebuild(self) -> None:
        rebuild_symbol_index()

    def incremental(self) -> bool:
        return _build_incremental_symbol_index()

    def reset(self) -> None:
        from .._cache import clear_symbol_cache
        clear_symbol_cache()

    def clear(self) -> None:
        self.reset()

    @property
    def built(self) -> bool:
        return _config._SYMBOL_INDEX_BUILT

    @property
    def count(self) -> int:
        return len(_config._SYMBOL_CACHE)

    @property
    def is_built(self) -> bool:
        return self.built

    def __repr__(self) -> str:
        return f"<SymbolIndex: built={self.built}, symbols={self.count}>"


class SymbolConfigNamespace:
    def enable(self) -> None:
        enable_symbol_search()

    def disable(self) -> None:
        disable_symbol_search()

    @property
    def enabled(self) -> bool:
        return is_symbol_search_enabled()

    @property
    def interactive(self) -> bool:
        return get_symbol_search_config().get("interactive", True)

    @interactive.setter
    def interactive(self, value: bool) -> None:
        _config._SYMBOL_SEARCH_CONFIG["interactive"] = value

    @property
    def exact_params(self) -> bool:
        return get_symbol_search_config().get("exact_params", False)

    @exact_params.setter
    def exact_params(self, value: bool) -> None:
        _config._SYMBOL_SEARCH_CONFIG["exact_params"] = value

    @property
    def max_results(self) -> int:
        return get_symbol_search_config().get("max_results", 5)

    @max_results.setter
    def max_results(self, value: int) -> None:
        _config._SYMBOL_SEARCH_CONFIG["max_results"] = value

    @property
    def search_depth(self) -> int:
        return get_symbol_search_config().get("search_depth", 1)

    @search_depth.setter
    def search_depth(self, value: int) -> None:
        _config._SYMBOL_SEARCH_CONFIG["search_depth"] = value

    @property
    def skip_private(self) -> bool:
        return get_symbol_search_config().get("skip_private", True)

    @skip_private.setter
    def skip_private(self, value: bool) -> None:
        _config._SYMBOL_SEARCH_CONFIG["skip_private"] = value

    @property
    def skip_stdlib(self) -> bool:
        return get_symbol_search_config().get("skip_stdlib", False)

    @skip_stdlib.setter
    def skip_stdlib(self, value: bool) -> None:
        _config._SYMBOL_SEARCH_CONFIG["skip_stdlib"] = value

    @property
    def cache_enabled(self) -> bool:
        return get_symbol_search_config().get("cache_enabled", True)

    @cache_enabled.setter
    def cache_enabled(self, value: bool) -> None:
        _config._SYMBOL_SEARCH_CONFIG["cache_enabled"] = value

    @property
    def auto_resolution(self) -> bool:
        return get_symbol_resolution_config().get("auto_symbol", True)

    @auto_resolution.setter
    def auto_resolution(self, value: bool) -> None:
        if value:
            enable_auto_symbol_resolution()
        else:
            disable_auto_symbol_resolution()

    @property
    def auto_threshold(self) -> float:
        return get_symbol_resolution_config().get("auto_threshold", 0.7)

    @auto_threshold.setter
    def auto_threshold(self, value: float) -> None:
        _config._SYMBOL_RESOLUTION_CONFIG["auto_threshold"] = value

    @property
    def conflict_threshold(self) -> float:
        return get_symbol_resolution_config().get("conflict_threshold", 0.3)

    @conflict_threshold.setter
    def conflict_threshold(self, value: float) -> None:
        _config._SYMBOL_RESOLUTION_CONFIG["conflict_threshold"] = value

    @property
    def misspelling(self) -> bool:
        return get_symbol_resolution_config().get("symbol_misspelling", True)

    @misspelling.setter
    def misspelling(self, value: bool) -> None:
        _config._SYMBOL_RESOLUTION_CONFIG["symbol_misspelling"] = value

    @property
    def context_aware(self) -> bool:
        return get_symbol_resolution_config().get("context_aware", True)

    @context_aware.setter
    def context_aware(self, value: bool) -> None:
        _config._SYMBOL_RESOLUTION_CONFIG["context_aware"] = value

    @property
    def warn_on_conflict(self) -> bool:
        return get_symbol_resolution_config().get("warn_on_conflict", True)

    @warn_on_conflict.setter
    def warn_on_conflict(self, value: bool) -> None:
        _config._SYMBOL_RESOLUTION_CONFIG["warn_on_conflict"] = value

    @property
    def save_preferences(self) -> bool:
        return get_symbol_resolution_config().get("save_preferences", True)

    @save_preferences.setter
    def save_preferences(self, value: bool) -> None:
        _config._SYMBOL_RESOLUTION_CONFIG["save_preferences"] = value

    @property
    def strict(self) -> bool:
        return get_symbol_resolution_config().get("strict", False)

    @strict.setter
    def strict(self, value: bool) -> None:
        _config._SYMBOL_RESOLUTION_CONFIG["strict"] = value

    def snapshot(self) -> Dict[str, Any]:
        return {
            "search": dict(get_symbol_search_config()),
            "resolution": dict(get_symbol_resolution_config()),
        }

    def export(self, path: Optional[str] = None) -> str:
        import json
        data = self.snapshot()
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        return json.dumps(data, indent=2)

    def __repr__(self) -> str:
        return (
            f"<SymbolConfig: enabled={self.enabled}, "
            f"auto_resolution={self.auto_resolution}>"
        )


class SymbolNamespace:
    def search(
        self,
        name: str,
        symbol_type: Optional[str] = None,
        signature: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> List[Any]:
        return search_symbol(name, symbol_type, signature, max_results)

    def sharded(self, name: str, max_results: int = 5) -> List[Any]:
        return search_with_sharding(name, max_results)

    def which(
        self,
        name: str,
        module_hint: Optional[str] = None,
    ) -> Optional[Any]:
        return which(name, module_hint)

    def which_all(self, name: str) -> List[Any]:
        return which_all(name)

    def prefer(self, symbol: str, module: str) -> None:
        set_symbol_preference(symbol, module)

    def preference(self, symbol: str) -> Optional[str]:
        return get_symbol_preference(symbol)

    def clear_preference(self, symbol: str) -> bool:
        return clear_symbol_preference(symbol)

    def conflicts(self, symbol: Optional[str] = None) -> Any:
        from .._analysis._conflict import find_symbol_conflicts
        all_conflicts = find_symbol_conflicts()
        if symbol:
            return all_conflicts.get(symbol)
        return all_conflicts

    def conflict_summary(self) -> Dict[str, Any]:
        from .._analysis._conflict import get_conflicts_summary
        return get_conflicts_summary()

    def show_conflicts(self, symbol_filter: Optional[str] = None, max_results: int = 20) -> None:
        from .._analysis._conflict import show_conflicts
        show_conflicts(symbol_filter, max_results)

    @property
    def config(self) -> SymbolConfigNamespace:
        return _SYMBOL_CONFIG_NS

    @property
    def index(self) -> SymbolIndexNamespace:
        return _SYMBOL_INDEX_NS

    def cache_info(self) -> Dict[str, Any]:
        return get_symbol_cache_info()

    def _search_direct(self, name: str, symbol_type=None, signature=None, max_results=None) -> List[Any]:
        return _search_symbol_direct(name, symbol_type, signature, max_results)

    def _enhanced(self, name: str, auto: bool = True, symbol_type=None) -> Optional[Any]:
        return _search_symbol_enhanced(name, auto, symbol_type)

    def __repr__(self) -> str:
        info = get_symbol_cache_info()
        return f"<SymbolNamespace: {info.get('symbol_count', 0)} symbols, built={info.get('built', False)}>"


_SYMBOL_INDEX_NS = SymbolIndexNamespace()
_SYMBOL_CONFIG_NS = SymbolConfigNamespace()
