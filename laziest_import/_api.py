"""
全新面向对象 API 入口 — LazyImport。

用法:
    from laziest_import import LazyImport, lz

    lz = LazyImport()

    # 模块加载
    np = lz.module.numpy
    pd = lz.module.get('pandas')

    # 配置
    lz.config.debug = True
    lz.config.auto_install.enabled = True

    # 符号搜索
    results = lz.symbol.search('DataFrame')
    loc = lz.symbol.which('sqrt')

    # 别名管理（字典式 + 方法式）
    lz.alias['my_np'] = 'numpy'
    mod = lz.alias['my_np']

    # 缓存
    lz.cache.symbols.clear()
    lz.cache.files.clear()
    stats = lz.cache.stats

    # 钩子（支持 += -= 操作符）
    lz.hooks.pre += my_pre_hook
    lz.hooks.post += my_post_hook

    # 异步
    mod = await lz.async.get('numpy')
    mods = await lz.async.fetch('numpy', 'pandas')

    # 分析
    result = lz.analyze.file('script.py')
    result = lz.analyze.code('import numpy')
    results = lz.analyze.dir('/path/to/project')

    # 性能分析
    lz.profile.start()
    lz.profile.stop()
    lz.profile.print_report()

    # 安装
    lz.install.package('torch')
    lz.install.auto.enabled = True

    # 导出
    lz.alias.export('/path/aliases.json')
    lz.config.export('/path/config.json')

    # 后台索引构建
    lz.background.start()
    lz.background.wait()

    # 版本
    print(lz.version)
    print(lz.version_of('numpy'))

    # 快照与恢复
    snap = lz.config.snapshot()
    lz.config.restore(snap)

    # 临时配置
    with lz.config.temp_config(debug=True):
        pass  # debug 在此范围内为 True，退出后恢复原值

注意:
    - LazyImport() 可以创建多个实例，它们共享同一份全局状态
    - 推荐创建单例使用: lz = LazyImport()
    - 或者使用模块级快捷函数: from laziest_import import lz
"""

from typing import (
    Any, Dict, List, Optional, Set, Tuple, Callable, Union, Iterator
)
from dataclasses import dataclass, field, asdict
from pathlib import Path
import warnings
import logging

# ─── 直接子模块导入（无循环依赖） ─────────────────────────────

from . import _config

from ._alias import (
    _ALIAS_MAP,
    _LAZY_MODULES,
    _build_known_modules_cache,
    register_alias,
    unregister_alias,
    reload_aliases,
    export_aliases,
    validate_aliases,
    _validate_alias,
    register_aliases,
)

from ._cache import (
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
    enable_background_build,
    get_preheat_config,
    enable_incremental_index,
    get_incremental_config,
    get_cache_version,
    _get_cache_dir,
    _get_cache_size,
    _cleanup_cache_if_needed,
    _check_cache_size_before_save,
    _get_symbol_index_path,
    _get_tracked_packages_path,
    _save_compressed_json,
    _load_compressed_json,
    _should_use_compression,
    _get_compressed_path,
    _save_symbol_index,
    _load_symbol_index,
    _save_tracked_packages,
    _load_tracked_packages,
    _get_package_version,
    _track_package,
    _check_package_changed,
    _calculate_file_sha,
    _get_caller_file_path,
    _get_cache_file_path,
    _load_file_cache,
    _save_file_cache,
    _init_file_cache,
    _start_background_preload,
    _record_module_load,
    _save_current_cache,
    _start_background_index_build,
    _is_background_index_building,
    _wait_for_background_index,
    FileCache,
    SymbolIndexCache,
)

from ._symbol import (
    search_symbol,
    rebuild_symbol_index,
    get_symbol_search_config,
    get_symbol_cache_info,
    set_symbol_preference,
    get_symbol_preference,
    clear_symbol_preference,
    list_symbol_conflicts,
    set_module_priority,
    get_module_priority,
    enable_symbol_search,
    disable_symbol_search,
    is_symbol_search_enabled,
    enable_auto_symbol_resolution,
    disable_auto_symbol_resolution,
    get_symbol_resolution_config,
    get_loaded_modules_context,
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
    _search_symbol_enhanced,
)

from ._public_api import (
    list_loaded,
    list_available,
    get_module,
    clear_cache,
    reset_all as _reset_all,
    get_version,
    reload_module,
    enable_auto_search,
    disable_auto_search,
    is_auto_search_enabled,
    search_module,
    search_class,
    enable_debug_mode,
    disable_debug_mode,
    is_debug_mode,
    get_import_stats,
    reset_import_stats,
    validate_aliases_importable,
)

from ._install import (
    install_package,
    enable_auto_install,
    disable_auto_install,
    is_auto_install_enabled,
    get_auto_install_config,
    set_pip_index,
    set_pip_extra_args,
    rebuild_module_cache,
)

from ._async_ops import import_async, import_multiple_async

from ._fuzzy import _search_module

from ._proxy import _get_lazy_module

from ._which import which, which_all, SymbolLocation

from ._rcconfig import (
    load_rc_config,
    get_rc_value,
    create_rc_file,
    get_rc_info,
    reload_rc_config,
    save_rc_config,
)


# ═══════════════════════════════════════════════════════════════
#  Helper: 更新符号搜索配置
# ═══════════════════════════════════════════════════════════════

def _apply_search_config(cfg: "SymbolSearchConfig") -> None:
    _config._SYMBOL_SEARCH_CONFIG.update(asdict(cfg))


def _apply_resolution_config(cfg: "SymbolResolutionConfig") -> None:
    _config._SYMBOL_RESOLUTION_CONFIG.update(asdict(cfg))


# ═══════════════════════════════════════════════════════════════
#  数据类
# ═══════════════════════════════════════════════════════════════

@dataclass
class AutoInstallConfig:
    """自动安装配置"""
    enabled: bool = False
    interactive: bool = True
    index: Optional[str] = None
    extra_args: List[str] = field(default_factory=list)
    prefer_uv: bool = False
    silent: bool = False


@dataclass
class RetryConfig:
    """重试配置"""
    enabled: bool = False
    max_retries: int = 3
    retry_delay: float = 0.5
    modules: Set[str] = field(default_factory=set)


@dataclass
class SymbolSearchConfig:
    """符号搜索配置"""
    enabled: bool = True
    interactive: bool = True
    exact_params: bool = False
    max_results: int = 5
    search_depth: int = 1
    cache_enabled: bool = True
    skip_private: bool = True
    skip_stdlib: bool = False


@dataclass
class SymbolResolutionConfig:
    """符号解析配置"""
    auto_symbol: bool = True
    auto_threshold: float = 0.7
    conflict_threshold: float = 0.3
    symbol_misspelling: bool = True
    context_aware: bool = True
    warn_on_conflict: bool = True
    save_preferences: bool = True


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    max_size_mb: int = 100
    cleanup_threshold: float = 0.8
    file_cache_enabled: bool = True
    symbol_index_enabled: bool = True
    persist_across_sessions: bool = True
    symbol_index_ttl: int = 86400
    stdlib_cache_ttl: int = 604800
    third_party_cache_ttl: int = 86400
    enable_compression: bool = False


@dataclass
class ModuleSkipConfig:
    """模块跳过配置"""
    skip_test_modules: bool = True
    skip_internal_modules: bool = True
    skip_large_modules: bool = True
    large_module_threshold: int = 100
    skip_modules_file: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
#  HookList
# ═══════════════════════════════════════════════════════════════

class HookList:
    """
    可订阅的钩子列表。

    支持 += 和 -= 运算符：
        lz.hooks.pre += my_hook
        lz.hooks.post -= my_hook
    """

    def __init__(self, hook_list: List[Callable]) -> None:
        self._hooks = hook_list

    def add(self, callback: Callable) -> None:
        """注册钩子"""
        if callback not in self._hooks:
            self._hooks.append(callback)

    def remove(self, callback: Callable) -> bool:
        """移除钩子，返回是否成功"""
        try:
            self._hooks.remove(callback)
            return True
        except ValueError:
            return False

    def clear(self) -> None:
        """清空所有钩子"""
        self._hooks.clear()

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        """触发所有注册的钩子（内部使用）"""
        for hook in list(self._hooks):
            try:
                hook(*args, **kwargs)
            except Exception:
                pass

    def __iadd__(self, callback: Callable) -> "HookList":
        self.add(callback)
        return self

    def __isub__(self, callback: Callable) -> "HookList":
        self.remove(callback)
        return self

    def __len__(self) -> int:
        return len(self._hooks)

    def __iter__(self) -> Iterator[Callable]:
        return iter(self._hooks)

    def __repr__(self) -> str:
        return f"HookList(hooks={len(self._hooks)})"


# ═══════════════════════════════════════════════════════════════
#  ModuleNamespace
# ═══════════════════════════════════════════════════════════════

class ModuleNamespace:
    """
    模块加载命名空间。

    用法:
        lz.module.numpy                    # 属性式（触发懒加载）
        lz.module.get('numpy')             # 方法式（不存在返回 None）
        lz.module.load('numpy')            # 强制加载并返回
        lz.module.reload('numpy')          # 重载
        lz.module.list_loaded()            # 已加载列表
        lz.module.list_available()         # 可用列表
        lz.module.is_loaded('numpy')       # 检查是否已加载
    """

    def get(self, name: str) -> Optional[Any]:
        """获取已加载的模块对象，不存在则返回 None"""
        return get_module(name)

    def load(self, name: str) -> Any:
        """加载并返回模块（强制触发懒加载）"""
        lm = _get_lazy_module(name)
        return lm._get_module()

    def reload(self, name: str) -> bool:
        """重载已加载的模块"""
        return reload_module(name)

    def list_loaded(self) -> List[str]:
        """列出已加载的模块别名"""
        return list_loaded()

    def list_available(self) -> List[str]:
        """列出所有可用模块别名"""
        return list_available()

    def is_loaded(self, name: str) -> bool:
        """检查模块是否已加载"""
        return name in list_loaded()

    # ---- 字典式访问 ----

    def __getitem__(self, name: str) -> Any:
        mod = get_module(name)
        if mod is None:
            raise KeyError(
                f"Module '{name}' is not loaded. "
                f"Access it via lz.module.load('{name}') or lz.module['{name}'] = <module> first."
            )
        return mod

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return _get_lazy_module(name)._get_module()
        except Exception as e:
            raise AttributeError(
                f"Cannot load module '{name}': {e}"
            ) from e

    def __dir__(self) -> List[str]:
        return sorted(set(self.list_available()))

    def __repr__(self) -> str:
        loaded = self.list_loaded()
        return (
            f"<ModuleNamespace: "
            f"{len(loaded)}/{len(self.list_available())} loaded>"
        )


# ═══════════════════════════════════════════════════════════════
#  AliasNamespace
# ═══════════════════════════════════════════════════════════════

class AliasNamespace:
    """
    别名管理命名空间，支持字典式和方法式两种 API。

    用法:
        lz.alias.register('np', 'numpy')          # 方法式
        lz.alias['my_np'] = 'numpy'                # 字典式
        mod = lz.alias['np']                       # 获取懒加载代理
        lz.alias.reload()                          # 从配置重载
        lz.alias.export('/path/aliases.json')      # 导出
    """

    # ---- 方法式 API ----

    def register(self, alias: str, module_name: str) -> None:
        """注册单个别名"""
        register_alias(alias, module_name)

    def register_many(self, aliases: Dict[str, str]) -> List[str]:
        """批量注册别名，返回成功注册的列表"""
        registered: List[str] = []
        for alias, mod in aliases.items():
            try:
                register_alias(alias, mod)
                registered.append(alias)
            except ValueError:
                pass
        return registered

    def unregister(self, alias: str) -> bool:
        """注销别名，返回是否成功"""
        return unregister_alias(alias)

    def reload(self) -> None:
        """从配置文件重载所有别名"""
        reload_aliases()

    def export(
        self,
        path: Optional[str] = None,
        include_categories: bool = True,
    ) -> str:
        """
        导出别名到 JSON 文件或返回字符串。

        Args:
            path: 输出文件路径，None 则只返回字符串
            include_categories: 是否包含分类信息

        Returns:
            JSON 字符串
        """
        return export_aliases(path, include_categories)

    def validate(
        self, aliases: Optional[Dict[str, str]] = None
    ) -> Dict[str, List[str]]:
        """
        验证别名有效性。

        Args:
            aliases: 要验证的别名映射，None 则验证当前所有别名

        Returns:
            包含 'valid', 'invalid', 'warnings' 的字典
        """
        return validate_aliases(aliases)

    def import_file(self, path: str) -> int:
        """
        从 JSON 文件导入别名。

        Args:
            path: JSON 文件路径

        Returns:
            成功导入的别名数量
        """
        import json
        from pathlib import Path as _Path

        p = _Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Alias file not found: {path}")

        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        flattened: Dict[str, str] = {}
        for k, v in data.items():
            if isinstance(v, dict):
                flattened.update(v)
            elif isinstance(v, str):
                flattened[k] = v

        registered = self.register_many(flattened)
        return len(registered)

    def search(self, pattern: str) -> List[str]:
        """
        搜索匹配指定模式的别名。

        Args:
            pattern: 搜索模式（子串匹配）

        Returns:
            匹配的别名列表
        """
        pattern_lower = pattern.lower()
        return [
            alias for alias in _ALIAS_MAP
            if pattern_lower in alias.lower()
        ]

    # ---- 字典式 API ----

    def __setitem__(self, alias: str, module_name: str) -> None:
        register_alias(alias, module_name)

    def __getitem__(self, alias: str) -> Any:
        if alias not in _ALIAS_MAP:
            raise KeyError(f"Alias '{alias}' not found. Register it first.")
        return _get_lazy_module(alias)

    def __delitem__(self, alias: str) -> None:
        if not self.unregister(alias):
            raise KeyError(f"Alias '{alias}' not found")

    def __contains__(self, alias: str) -> bool:
        return alias in _ALIAS_MAP

    def __len__(self) -> int:
        return len(_ALIAS_MAP)

    def __iter__(self) -> Iterator[str]:
        return iter(_ALIAS_MAP)

    def keys(self) -> List[str]:
        return list(_ALIAS_MAP.keys())

    def values(self) -> List[str]:
        return list(_ALIAS_MAP.values())

    def items(self) -> List[Tuple[str, str]]:
        return list(_ALIAS_MAP.items())

    def get(self, alias: str, default: Optional[str] = None) -> Optional[str]:
        return _ALIAS_MAP.get(alias, default)

    def __repr__(self) -> str:
        return f"<AliasNamespace: {len(self)} aliases>"


# ═══════════════════════════════════════════════════════════════
#  SymbolNamespace
# ═══════════════════════════════════════════════════════════════

class SymbolIndexNamespace:
    """符号索引管理子命名空间"""

    def build(self, force: bool = False, max_modules: int = 100, timeout: float = 30.0) -> None:
        """
        构建/重建符号索引。

        Args:
            force: 是否强制重建
            max_modules: 最大扫描模块数
            timeout: 超时时间（秒）
        """
        _build_symbol_index(force=force, max_modules=max_modules, timeout=timeout)

    def rebuild(self) -> None:
        """强制重建符号索引"""
        rebuild_symbol_index()

    def incremental(self) -> bool:
        """
        执行增量索引构建。

        Returns:
            是否成功
        """
        return _build_incremental_symbol_index()

    def reset(self) -> None:
        """重置符号缓存（不清除索引文件）"""
        clear_symbol_cache()

    def clear(self) -> None:
        """清除符号缓存（reset 的别名）"""
        clear_symbol_cache()

    @property
    def built(self) -> bool:
        """索引是否已构建"""
        return _config._SYMBOL_INDEX_BUILT

    @property
    def count(self) -> int:
        """已索引符号数量"""
        return len(_config._SYMBOL_CACHE)

    @property
    def is_built(self) -> bool:
        """索引是否已构建（built 的别名）"""
        return self.built

    def __repr__(self) -> str:
        return f"<SymbolIndex: built={self.built}, symbols={self.count}>"


class SymbolConfigNamespace:
    """
    符号搜索和解析配置子命名空间。

    所有修改实时同步到底层 _config 全局状态。
    """

    # ---- 开关 ----

    def enable(self) -> None:
        """启用符号搜索"""
        enable_symbol_search()

    def disable(self) -> None:
        """禁用符号搜索"""
        disable_symbol_search()

    @property
    def enabled(self) -> bool:
        """符号搜索是否启用"""
        return is_symbol_search_enabled()

    # ---- 搜索参数 ----

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

    # ---- 解析参数 ----

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

    # ---- 导出/快照 ----

    def snapshot(self) -> Dict[str, Any]:
        """获取搜索+解析配置的完整快照"""
        return {
            "search": dict(get_symbol_search_config()),
            "resolution": dict(get_symbol_resolution_config()),
        }

    def export(self, path: Optional[str] = None) -> str:
        """导出配置为 JSON"""
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
    """
    符号搜索命名空间。

    用法:
        lz.symbol.search('DataFrame')          # 搜索符号
        lz.symbol.which('sqrt')                # 查找定义位置
        lz.symbol.which_all('sqrt')            # 查找所有位置
        lz.symbol.prefer('DF', 'pandas')       # 设置偏好
        lz.symbol.preference('DF')             # 获取偏好
        lz.symbol.conflicts()                  # 获取所有冲突
        lz.symbol.index.build()                # 构建索引
        lz.symbol.index.reset()                # 重置索引
        lz.symbol.config.enabled = False       # 配置
        lz.symbol.config.sharding.enable()     # 分片搜索
    """

    # ---- 搜索 ----

    def search(
        self,
        name: str,
        symbol_type: Optional[str] = None,
        signature: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> List[Any]:
        """
        搜索符号。

        Args:
            name: 符号名称（支持模糊匹配）
            symbol_type: 类型过滤 ('class', 'function', 'callable')
            signature: 签名过滤
            max_results: 最大结果数

        Returns:
            List[SearchResult]
        """
        return search_symbol(name, symbol_type, signature, max_results)

    def sharded(self, name: str, max_results: int = 5) -> List[Any]:
        """使用分片索引搜索（大数据量场景更快）"""
        return search_with_sharding(name, max_results)

    # ---- 位置查找 ----

    def which(
        self,
        name: str,
        module_hint: Optional[str] = None,
    ) -> Optional[Any]:
        """
        查找符号定义位置（返回第一个匹配）。

        Args:
            name: 符号名称（支持 "module.symbol" 格式）
            module_hint: 可选模块提示

        Returns:
            SymbolLocation 或 None
        """
        return which(name, module_hint)

    def which_all(self, name: str) -> List[Any]:
        """
        查找符号所有定义位置。

        Args:
            name: 符号名称

        Returns:
            List[SymbolLocation]
        """
        return which_all(name)

    # ---- 偏好 ----

    def prefer(self, symbol: str, module: str) -> None:
        """为符号设置首选模块"""
        set_symbol_preference(symbol, module)

    def preference(self, symbol: str) -> Optional[str]:
        """获取符号的首选模块"""
        return get_symbol_preference(symbol)

    def clear_preference(self, symbol: str) -> bool:
        """清除符号偏好"""
        return clear_symbol_preference(symbol)

    # ---- 冲突 ----

    def conflicts(self, symbol: Optional[str] = None) -> Any:
        """
        获取符号冲突信息。

        Args:
            symbol: 如果提供，只返回该符号的冲突；否则返回所有冲突

        Returns:
            SymbolConflict (单符号) 或 Dict[str, SymbolConflict] (全部)
        """
        from .._analysis._conflict import find_symbol_conflicts
        all_conflicts = find_symbol_conflicts()
        if symbol:
            return all_conflicts.get(symbol)
        return all_conflicts

    def conflict_summary(self) -> Dict[str, Any]:
        """获取冲突概要统计"""
        from .._analysis._conflict import get_conflicts_summary
        return get_conflicts_summary()

    def show_conflicts(self, symbol_filter: Optional[str] = None, max_results: int = 20) -> None:
        """格式化打印符号冲突"""
        from .._analysis._conflict import show_conflicts
        show_conflicts(symbol_filter, max_results)

    # ---- 配置 ----

    @property
    def config(self) -> SymbolConfigNamespace:
        """搜索/解析配置"""
        return _SYMBOL_CONFIG_NS

    # ---- 索引 ----

    @property
    def index(self) -> SymbolIndexNamespace:
        """索引管理"""
        return _SYMBOL_INDEX_NS

    # ---- 缓存信息 ----

    def cache_info(self) -> Dict[str, Any]:
        """获取符号缓存信息"""
        return get_symbol_cache_info()

    # ---- 内部方法（高级用户） ----

    def _search_direct(self, name: str, symbol_type=None, signature=None, max_results=None) -> List[Any]:
        """直接搜索（不模糊匹配）"""
        return _search_symbol_direct(name, symbol_type, signature, max_results)

    def _enhanced(self, name: str, auto: bool = True, symbol_type=None) -> Optional[Any]:
        """增强搜索（含自动解析和拼写纠正）"""
        return _search_symbol_enhanced(name, auto, symbol_type)

    def __repr__(self) -> str:
        info = get_symbol_cache_info()
        return f"<SymbolNamespace: {info.get('symbol_count', 0)} symbols, built={info.get('built', False)}>"


# ═══════════════════════════════════════════════════════════════
#  CacheNamespaces
# ═══════════════════════════════════════════════════════════════

class CacheSymbolsNamespace:
    """符号缓存子命名空间"""

    def clear(self) -> None:
        """清除所有符号缓存（内存）"""
        clear_symbol_cache()

    def reset(self) -> None:
        """重置并重建索引"""
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
    """文件缓存子命名空间"""

    def clear(self, file_path: Optional[str] = None) -> int:
        """
        清除文件缓存。

        Args:
            file_path: 如果提供，只清除该文件的缓存；否则清除所有

        Returns:
            被删除的缓存文件数量
        """
        return clear_file_cache(file_path)

    def info(self) -> Dict[str, Any]:
        """获取文件缓存详细信息"""
        return get_file_cache_info()

    def force_save(self) -> bool:
        """强制保存当前文件缓存"""
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
    """
    缓存统计命名空间。

    支持属性式访问统计值。
    用法: lz.cache.stats.hit_rate, lz.cache.stats['symbol_hits'] 等。
    """

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
        """重置所有统计为零"""
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

    def keys(self) -> List[str]:
        return list(self._get_stats().keys())

    def items(self) -> List[Tuple[str, Any]]:
        return list(self._get_stats().items())

    def __repr__(self) -> str:
        s = self._get_stats()
        return f"<CacheStats: hits={s.get('total_requests', 0)}, rate={s.get('hit_rate', 0):.1%}>"


class CacheConfigNamespace:
    """缓存配置子命名空间"""

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
        """获取缓存配置快照"""
        return dict(get_cache_config())

    def export(self, path: Optional[str] = None) -> str:
        """导出为 JSON"""
        import json
        data = dict(get_cache_config())
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        return json.dumps(data, indent=2)

    def __repr__(self) -> str:
        return f"<CacheConfig: max={self.max_size_mb}MB, compression={self.compression}>"


class CacheNamespace:
    """
    缓存管理命名空间。

    用法:
        lz.cache.clear()                  # 清除所有缓存
        lz.cache.symbols.clear()          # 仅清除符号缓存
        lz.cache.files.clear()            # 仅清除文件缓存
        lz.cache.stats                    # 统计信息（属性访问）
        lz.cache.stats.reset()            # 重置统计
        lz.cache.dir                      # 缓存目录
        lz.cache.dir = '/new/path'        # 设置缓存目录
        lz.cache.compression = True       # 启用压缩
    """

    @property
    def symbols(self) -> CacheSymbolsNamespace:
        """符号缓存管理"""
        return _CACHE_SYMBOLS_NS

    @property
    def files(self) -> CacheFilesNamespace:
        """文件缓存管理"""
        return _CACHE_FILES_NS

    @property
    def stats(self) -> CacheStatsNamespace:
        """缓存统计"""
        return _CACHE_STATS_NS

    @property
    def config(self) -> CacheConfigNamespace:
        """缓存详细配置"""
        return _CACHE_CONFIG_NS

    # ---- 核心操作 ----

    def clear(self) -> None:
        """清除所有缓存（模块 + 符号 + 文件）"""
        clear_cache()

    # ---- 目录 ----

    @property
    def dir(self) -> Path:
        """缓存目录路径"""
        return get_cache_dir()

    @dir.setter
    def dir(self, value: Union[str, Path]) -> None:
        set_cache_dir(value)

    def reset_dir(self) -> None:
        """重置为默认缓存目录"""
        reset_cache_dir()

    # ---- 压缩 ----

    @property
    def compression(self) -> bool:
        return get_cache_config().get("enable_compression", False)

    @compression.setter
    def compression(self, value: bool) -> None:
        enable_cache_compression(value)

    def __repr__(self) -> str:
        return f"<CacheNamespace: dir={self.dir}>"


# ═══════════════════════════════════════════════════════════════
#  ConfigNamespace
# ═══════════════════════════════════════════════════════════════

class ConfigNamespace:
    """
    全局配置命名空间。

    所有修改实时同步到底层 _config 全局状态。

    用法:
        lz.config.debug = True
        lz.config.auto_search = False
        lz.config.auto_install.enabled = True
        lz.config.cache.max_size_mb = 500
        lz.config.symbol_search.max_results = 10
    """

    # ---- 调试 ----

    @property
    def debug(self) -> bool:
        return _config._DEBUG_MODE

    @debug.setter
    def debug(self, value: bool) -> None:
        _config._DEBUG_MODE = value

    # ---- 自动搜索 ----

    @property
    def auto_search(self) -> bool:
        return _config._AUTO_SEARCH_ENABLED

    @auto_search.setter
    def auto_search(self, value: bool) -> None:
        _config._AUTO_SEARCH_ENABLED = value

    # ---- 自动安装 ----

    @property
    def auto_install(self) -> AutoInstallConfig:
        """获取自动安装配置快照"""
        c = _config._AUTO_INSTALL_CONFIG
        return AutoInstallConfig(
            enabled=c["enabled"],
            interactive=c["interactive"],
            index=c["index"],
            extra_args=list(c["extra_args"]),
            prefer_uv=c["prefer_uv"],
            silent=c["silent"],
        )

    @auto_install.setter
    def auto_install(self, cfg: AutoInstallConfig) -> None:
        """设置自动安装配置"""
        _config._AUTO_INSTALL_CONFIG["enabled"] = cfg.enabled
        _config._AUTO_INSTALL_CONFIG["interactive"] = cfg.interactive
        _config._AUTO_INSTALL_CONFIG["index"] = cfg.index
        _config._AUTO_INSTALL_CONFIG["extra_args"] = list(cfg.extra_args)
        _config._AUTO_INSTALL_CONFIG["prefer_uv"] = cfg.prefer_uv
        _config._AUTO_INSTALL_CONFIG["silent"] = cfg.silent

    @property
    def auto_install_enabled(self) -> bool:
        return _config._AUTO_INSTALL_CONFIG["enabled"]

    @auto_install_enabled.setter
    def auto_install_enabled(self, value: bool) -> None:
        _config._AUTO_INSTALL_CONFIG["enabled"] = value

    # ---- 重试 ----

    @property
    def retry(self) -> RetryConfig:
        """获取重试配置快照"""
        c = _config._RETRY_CONFIG
        return RetryConfig(
            enabled=c["enabled"],
            max_retries=c["max_retries"],
            retry_delay=c["retry_delay"],
            modules=set(c["retry_modules"]),
        )

    @retry.setter
    def retry(self, cfg: RetryConfig) -> None:
        _config._RETRY_CONFIG["enabled"] = cfg.enabled
        _config._RETRY_CONFIG["max_retries"] = cfg.max_retries
        _config._RETRY_CONFIG["retry_delay"] = cfg.retry_delay
        _config._RETRY_CONFIG["retry_modules"] = cfg.modules

    # ---- 符号搜索配置（快捷访问） ----

    @property
    def symbol_search(self) -> SymbolSearchConfig:
        return SymbolSearchConfig(**get_symbol_search_config())

    @symbol_search.setter
    def symbol_search(self, cfg: SymbolSearchConfig) -> None:
        _apply_search_config(cfg)

    @property
    def symbol_resolution(self) -> SymbolResolutionConfig:
        return SymbolResolutionConfig(**get_symbol_resolution_config())

    @symbol_resolution.setter
    def symbol_resolution(self, cfg: SymbolResolutionConfig) -> None:
        _apply_resolution_config(cfg)

    # ---- 缓存配置（快捷访问） ----

    @property
    def cache(self) -> CacheConfig:
        return CacheConfig(**get_cache_config())

    @cache.setter
    def cache(self, cfg: CacheConfig) -> None:
        set_cache_config(
            max_cache_size_mb=cfg.max_size_mb,
            symbol_index_ttl=cfg.symbol_index_ttl,
            stdlib_cache_ttl=cfg.stdlib_cache_ttl,
            third_party_cache_ttl=cfg.third_party_cache_ttl,
            enable_compression=cfg.enable_compression,
        )

    # ---- 模块跳过配置 ----

    @property
    def module_skip(self) -> ModuleSkipConfig:
        return ModuleSkipConfig(**get_module_skip_config())

    @module_skip.setter
    def module_skip(self, cfg: ModuleSkipConfig) -> None:
        set_module_skip_config(
            skip_test_modules=cfg.skip_test_modules,
            skip_internal_modules=cfg.skip_internal_modules,
            skip_large_modules=cfg.skip_large_modules,
            large_module_threshold=cfg.large_module_threshold,
        )

    # ---- 导入统计 ----

    @property
    def import_stats(self) -> Dict[str, Any]:
        return get_import_stats()

    # ---- 导出/快照 ----

    def snapshot(self) -> Dict[str, Any]:
        """
        创建当前所有配置的完整快照。

        Returns:
            包含所有配置的字典
        """
        return {
            "debug": self.debug,
            "auto_search": self.auto_search,
            "auto_install": asdict(self.auto_install),
            "retry": asdict(self.retry),
            "symbol_search": asdict(self.symbol_search),
            "symbol_resolution": asdict(self.symbol_resolution),
            "cache": asdict(self.cache),
            "module_skip": asdict(self.module_skip),
        }

    def restore(self, snapshot: Dict[str, Any]) -> None:
        """
        从快照恢复配置。

        Args:
            snapshot: 由 snapshot() 创建的快照字典
        """
        if "debug" in snapshot:
            self.debug = snapshot["debug"]
        if "auto_search" in snapshot:
            self.auto_search = snapshot["auto_search"]
        if "auto_install" in snapshot:
            self.auto_install = AutoInstallConfig(**snapshot["auto_install"])
        if "retry" in snapshot:
            self.retry = RetryConfig(**snapshot["retry"])
        if "symbol_search" in snapshot:
            self.symbol_search = SymbolSearchConfig(**snapshot["symbol_search"])
        if "symbol_resolution" in snapshot:
            self.symbol_resolution = SymbolResolutionConfig(**snapshot["symbol_resolution"])
        if "cache" in snapshot:
            self.cache = CacheConfig(**snapshot["cache"])
        if "module_skip" in snapshot:
            self.module_skip = ModuleSkipConfig(**snapshot["module_skip"])

    def export(self, path: Optional[str] = None) -> str:
        """
        导出配置为 JSON。

        Args:
            path: 输出文件路径，None 则只返回字符串

        Returns:
            JSON 字符串（如果 path 为 None）
        """
        import json
        data = self.snapshot()
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        return json.dumps(data, indent=2)

    # ---- 上下文管理器 ----

    def temp_config(self, **kwargs: Any) -> "ConfigContext":
        """
        创建临时配置上下文，退出时自动恢复。

        用法:
            with lz.config.temp_config(debug=True, auto_search=False):
                # 在此范围内 debug=True, auto_search=False
            # 退出后恢复原值
        """
        return ConfigContext(kwargs)

    def __repr__(self) -> str:
        return f"<ConfigNamespace: debug={self.debug}, auto_search={self.auto_search}>"


class ConfigContext:
    """
    临时配置上下文管理器。

    用法:
        with lz.config.temp_config(debug=True):
            pass  # 退出后自动恢复
    """

    def __init__(self, overrides: Dict[str, Any]) -> None:
        self._overrides = overrides
        self._snap: Dict[str, Any] = {}
        self._entered = False

    def __enter__(self) -> "ConfigContext":
        from .._api import _global_config
        self._snap = _global_config.snapshot()
        self._entered = True
        for key, value in self._overrides.items():
            if hasattr(_global_config, key):
                setattr(_global_config, key, value)
        return self

    def __exit__(self, *args: Any) -> None:
        if self._entered:
            from .._api import _global_config
            _global_config.restore(self._snap)


# ═══════════════════════════════════════════════════════════════
#  AnalyzeNamespace
# ═══════════════════════════════════════════════════════════════

class AnalyzeNamespace:
    """
    代码分析命名空间。

    用法:
        result = lz.analyze.file('script.py')
        result = lz.analyze.code('import numpy')
        results = lz.analyze.dir('/path/to/project')
        tree = lz.analyze.dep_tree('.')
    """

    def file(self, file_path: str) -> Any:
        """分析 Python 文件以预测所需的导入"""
        from .._analysis._preanalyze import DependencyPreAnalyzer
        analyzer = DependencyPreAnalyzer()
        return analyzer.analyze_file(file_path)

    def code(self, source: str, file_path: str = "<string>") -> Any:
        """分析源代码以预测所需的导入"""
        from .._analysis._preanalyze import DependencyPreAnalyzer
        analyzer = DependencyPreAnalyzer()
        return analyzer.analyze_source(source, file_path)

    def dir(
        self,
        dir_path: str,
        recursive: bool = True,
        exclude: Optional[Set[str]] = None,
    ) -> List[Any]:
        """分析目录下所有 Python 文件"""
        from .._analysis._preanalyze import DependencyPreAnalyzer
        analyzer = DependencyPreAnalyzer()
        return analyzer.analyze_directory(dir_path, recursive, exclude)

    def dep_tree(
        self,
        dir_path: str = ".",
        max_depth: int = 3,
        exclude: Optional[Set[str]] = None,
    ) -> Any:
        """生成依赖树"""
        from .._analysis._dependency import dependency_tree
        return dependency_tree(dir_path, max_depth=max_depth, exclude=exclude)

    def __repr__(self) -> str:
        return "<AnalyzeNamespace>"


# ═══════════════════════════════════════════════════════════════
#  ProfileNamespace
# ═══════════════════════════════════════════════════════════════

class ProfileNamespace:
    """
    性能分析命名空间。

    用法:
        lz.profile.start()
        # ... do work ...
        lz.profile.stop()
        lz.profile.print_report()
    """

    def start(self) -> None:
        """开始性能分析"""
        from .._analysis._profiler import start_profiling
        start_profiling()

    def stop(self) -> None:
        """停止性能分析"""
        from .._analysis._profiler import stop_profiling
        stop_profiling()

    def report(self, print_report: bool = False) -> Any:
        """
        获取分析报告。

        Args:
            print_report: 如果为 True，同时打印报告

        Returns:
            ProfileReport 对象
        """
        from .._analysis._profiler import get_profile_report, print_profile_report
        if print_report:
            print_profile_report()
        return get_profile_report()

    def print_report(self) -> None:
        """打印分析报告"""
        from .._analysis._profiler import print_profile_report
        print_profile_report()

    @property
    def is_active(self) -> bool:
        """分析器是否正在运行"""
        from .._analysis._profiler import _profiler
        return _profiler.is_active()

    def __repr__(self) -> str:
        return f"<ProfileNamespace: active={self.is_active}>"


# ═══════════════════════════════════════════════════════════════
#  AsyncNamespace
# ═══════════════════════════════════════════════════════════════

class AsyncNamespace:
    """
    异步操作命名空间。

    用法:
        mod = await lz.async.get('numpy')
        mods = await lz.async.fetch('numpy', 'pandas', 'torch')
    """

    async def get(self, alias: str) -> Any:
        """异步导入单个模块"""
        return await import_async(alias)

    async def fetch(self, *aliases: str) -> Dict[str, Any]:
        """异步并行导入多个模块"""
        return await import_multiple_async(list(aliases))

    def __repr__(self) -> str:
        return "<AsyncNamespace>"


# ═══════════════════════════════════════════════════════════════
#  InstallNamespace
# ═══════════════════════════════════════════════════════════════

class InstallNamespace:
    """
    包安装命名空间。

    用法:
        lz.install.package('torch')
        lz.install.auto.enabled = True
        lz.install.rebuild_cache()
    """

    def package(
        self,
        package_name: str,
        index: Optional[str] = None,
        extra_args: Optional[List[str]] = None,
        interactive: Optional[bool] = None,
    ) -> bool:
        """
        安装包。

        Args:
            package_name: pip 包名
            index: 可选的 PyPI 镜像 URL
            extra_args: 额外的 pip 参数
            interactive: 是否交互式确认，None 表示使用配置

        Returns:
            是否安装成功
        """
        return install_package(
            package_name, index=index, extra_args=extra_args,
            interactive=interactive,
        )

    @property
    def auto(self) -> AutoInstallConfig:
        """获取当前自动安装配置"""
        return get_auto_install_config()

    @auto.setter
    def auto(self, cfg: AutoInstallConfig) -> None:
        """设置自动安装配置"""
        _config._AUTO_INSTALL_CONFIG.update(asdict(cfg))

    def enable(
        self,
        interactive: bool = True,
        index: Optional[str] = None,
        extra_args: Optional[List[str]] = None,
        prefer_uv: bool = False,
        silent: bool = False,
    ) -> None:
        """启用自动安装"""
        enable_auto_install(interactive, index, extra_args, prefer_uv, silent)

    def disable(self) -> None:
        """禁用自动安装"""
        disable_auto_install()

    @property
    def enabled(self) -> bool:
        """自动安装是否启用"""
        return is_auto_install_enabled()

    def rebuild_cache(self) -> None:
        """重建模块缓存"""
        rebuild_module_cache()

    def __repr__(self) -> str:
        return f"<InstallNamespace: auto_enabled={is_auto_install_enabled()}>"


# ═══════════════════════════════════════════════════════════════
#  ExportNamespace
# ═══════════════════════════════════════════════════════════════

class ExportNamespace:
    """导出命名空间"""

    def aliases(
        self,
        path: Optional[str] = None,
        include_categories: bool = True,
    ) -> str:
        """
        导出别名。

        Args:
            path: 输出文件路径，None 则只返回字符串
            include_categories: 是否包含分类

        Returns:
            JSON 字符串
        """
        return export_aliases(path, include_categories)

    def config(self, path: Optional[str] = None) -> str:
        """
        导出全部配置（符号搜索、解析、缓存等）。

        Args:
            path: 输出文件路径，None 则只返回字符串

        Returns:
            JSON 字符串
        """
        return _global_config.export(path)

    def __repr__(self) -> str:
        return "<ExportNamespace>"


# ═══════════════════════════════════════════════════════════════
#  BackgroundNamespace
# ═══════════════════════════════════════════════════════════════

class BackgroundNamespace:
    """
    后台索引构建命名空间。

    用法:
        lz.background.start(callback=my_callback)
        lz.background.wait(timeout=60)
        lz.background.stop()
    """

    def start(
        self,
        progress_callback: Optional[Callable[[str, float], None]] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """
        启动后台索引构建。

        Args:
            progress_callback: 进度回调，参数为 (status, progress)
            timeout: 超时时间（秒）

        Returns:
            是否成功启动（已构建或正在构建则返回 False）
        """
        from .._lazy_index import start_background_index_build
        return start_background_index_build(progress_callback, timeout)

    def stop(self) -> None:
        """停止后台构建（等待当前任务完成）"""
        from .._lazy_index import get_background_builder
        builder = get_background_builder()
        builder.stop()

    @property
    def is_building(self) -> bool:
        """是否正在构建"""
        from .._lazy_index import is_index_building
        return is_index_building()

    def wait(self, timeout: float = 30.0) -> bool:
        """
        等待后台构建完成。

        Args:
            timeout: 超时时间（秒）

        Returns:
            是否在超时前完成
        """
        from .._lazy_index import wait_for_index
        return wait_for_index(timeout)

    @property
    def timeout(self) -> float:
        """获取/设置后台构建超时时间"""
        from .._lazy_index import get_background_timeout
        return get_background_timeout()

    @timeout.setter
    def timeout(self, value: float) -> None:
        from .._lazy_index import set_background_timeout
        set_background_timeout(value)

    @property
    def preheat(self) -> Dict[str, Any]:
        """预热配置"""
        return get_preheat_config()

    def enable(self, enabled: bool = True) -> None:
        """启用/禁用后台构建"""
        enable_background_build(enabled)

    def __repr__(self) -> str:
        return f"<BackgroundNamespace: building={self.is_building}>"


# ═══════════════════════════════════════════════════════════════
#  HookNamespace
# ═══════════════════════════════════════════════════════════════

class HookNamespace:
    """
    钩子管理命名空间。

    用法:
        lz.hooks.pre += my_pre_hook     # 等价于 add_pre_import_hook
        lz.hooks.post += my_post_hook   # 等价于 add_post_import_hook
        lz.hooks.pre -= my_pre_hook     # 等价于 remove_pre_import_hook
        lz.hooks.clear()                # 等价于 clear_import_hooks
    """

    @property
    def pre(self) -> HookList:
        """预导入钩子（在模块导入前调用）"""
        return HookList(_config._PRE_IMPORT_HOOKS)

    @property
    def post(self) -> HookList:
        """后导入钩子（在模块导入后调用）"""
        return HookList(_config._POST_IMPORT_HOOKS)

    def clear(self) -> None:
        """清除所有钩子"""
        _config._PRE_IMPORT_HOOKS.clear()
        _config._POST_IMPORT_HOOKS.clear()

    def __repr__(self) -> str:
        return (
            f"<HookNamespace: pre={len(_config._PRE_IMPORT_HOOKS)}, "
            f"post={len(_config._POST_IMPORT_HOOKS)}>"
        )


# ═══════════════════════════════════════════════════════════════
#  VersionNamespace
# ═══════════════════════════════════════════════════════════════

class VersionNamespace:
    """版本信息命名空间"""

    @property
    def current(self) -> str:
        """laziest-import 版本号"""
        return _config.__version__

    def of(self, package: str) -> Optional[str]:
        """获取已安装包的版本"""
        return get_package_version(package)

    def all_packages(self) -> Dict[str, str]:
        """获取所有已安装包的版本"""
        return get_all_package_versions()

    def laziest_import(self) -> str:
        """获取 laziest-import 版本（等价于 current）"""
        return get_laziest_import_version()

    def cache(self) -> str:
        """获取缓存版本"""
        return get_cache_version()

    # 支持 str() 转换
    def __str__(self) -> str:
        return self.current

    def __repr__(self) -> str:
        return f"<VersionNamespace: v{self.current}>"


# ═══════════════════════════════════════════════════════════════
#  RCConfigNamespace
# ═══════════════════════════════════════════════════════════════

class RCConfigNamespace:
    """RC 配置文件管理命名空间"""

    def load(self, force_reload: bool = False) -> Dict[str, Any]:
        """加载 RC 配置"""
        return load_rc_config(force_reload)

    def get(self, key: str, default: Any = None) -> Any:
        """获取 RC 配置值"""
        return get_rc_value(key, default)

    def create(self, path: Optional[str] = None, template: bool = True) -> Path:
        """创建 RC 文件"""
        return create_rc_file(path, template)

    def save(self, config: Dict[str, Any], path: Optional[str] = None) -> Path:
        """保存 RC 配置"""
        return save_rc_config(config, path)

    def paths(self) -> List[str]:
        """列出所有 RC 文件路径"""
        return [str(p) for p in _LAZIESTRC_PATHS]

    @property
    def paths_list(self) -> List[str]:
        """RC 文件路径列表"""
        return self.paths()

    def reload(self) -> Dict[str, Any]:
        """强制重载 RC 配置"""
        return reload_rc_config()

    def info(self) -> Dict[str, Any]:
        """获取 RC 配置信息"""
        return get_rc_info()

    def __repr__(self) -> str:
        active = find_rc_file()
        return f"<RCConfigNamespace: active={active}>"


# ═══════════════════════════════════════════════════════════════
#  LazyImport (主类)
# ═══════════════════════════════════════════════════════════════

# 单例引用，供 ConfigContext 内部使用
_global_config: Optional["ConfigNamespace"] = None


class LazyImport:
    """
    laziest-import 的统一面向对象 API 入口。

    所有命名空间通过属性访问：

        from laziest_import import LazyImport
        lz = LazyImport()

        # 模块加载
        np = lz.module.numpy
        pd = lz.module.get('pandas')

        # 配置
        lz.config.debug = True
        lz.config.auto_install.enabled = True

        # 符号搜索
        results = lz.symbol.search('DataFrame')
        loc = lz.symbol.which('sqrt')

        # 别名管理（字典式）
        lz.alias['my_np'] = 'numpy'
        mod = lz.alias['my_np']

        # 缓存
        lz.cache.symbols.clear()
        lz.cache.files.clear()
        stats = lz.cache.stats

        # 钩子
        lz.hooks.pre += my_pre_hook
        lz.hooks.post += my_post_hook

        # 异步
        mod = await lz.async.get('numpy')
        mods = await lz.async.fetch('numpy', 'pandas')

        # 分析
        result = lz.analyze.file('script.py')
        result = lz.analyze.code('import numpy')

        # 性能分析
        with lz.config.temp_config(debug=True):
            lz.profile.start()
            # ... do work ...
            lz.profile.stop()
            lz.profile.print_report()

        # 导出
        lz.alias.export('/path/aliases.json')
        lz.config.export('/path/config.json')

        # RC 配置
        rc = lz.rc.load()
        lz.rc.create('/path/.laziestrc')

    注意:
        - LazyImport() 可以创建多个实例，它们共享同一份全局状态
        - 推荐创建单例使用: lz = LazyImport()
        - 或者使用模块级快捷函数: from laziest_import import lz
    """

    def __init__(self) -> None:
        """创建 LazyImport 实例。所有实例共享同一份 _config 全局状态。"""
        # 延迟初始化命名空间（避免循环导入）
        self._module_ns: Optional[ModuleNamespace] = None
        self._alias_ns: Optional[AliasNamespace] = None
        self._symbol_ns: Optional[SymbolNamespace] = None
        self._cache_ns: Optional[CacheNamespace] = None
        self._config_ns: Optional[ConfigNamespace] = None
        self._analyze_ns: Optional[AnalyzeNamespace] = None
        self._profile_ns: Optional[ProfileNamespace] = None
        self._hooks_ns: Optional[HookNamespace] = None
        self._async_ns: Optional[AsyncNamespace] = None
        self._install_ns: Optional[InstallNamespace] = None
        self._export_ns: Optional[ExportNamespace] = None
        self._background_ns: Optional[BackgroundNamespace] = None
        self._version_ns: Optional[VersionNamespace] = None
        self._rc_ns: Optional[RCConfigNamespace] = None

    # ─── 模块访问 ─────────────────────────────

    @property
    def module(self) -> ModuleNamespace:
        if self._module_ns is None:
            self._module_ns = ModuleNamespace()
        return self._module_ns

    # ─── 别名管理 ─────────────────────────────

    @property
    def alias(self) -> AliasNamespace:
        if self._alias_ns is None:
            self._alias_ns = AliasNamespace()
        return self._alias_ns

    # ─── 符号搜索 ─────────────────────────────

    @property
    def symbol(self) -> SymbolNamespace:
        if self._symbol_ns is None:
            self._symbol_ns = SymbolNamespace()
        return self._symbol_ns

    # ─── 缓存管理 ─────────────────────────────

    @property
    def cache(self) -> CacheNamespace:
        if self._cache_ns is None:
            self._cache_ns = CacheNamespace()
        return self._cache_ns

    # ─── 全局配置 ─────────────────────────────

    @property
    def config(self) -> ConfigNamespace:
        if self._config_ns is None:
            self._config_ns = ConfigNamespace()
        return self._config_ns

    # ─── 代码分析 ─────────────────────────────

    @property
    def analyze(self) -> AnalyzeNamespace:
        if self._analyze_ns is None:
            self._analyze_ns = AnalyzeNamespace()
        return self._analyze_ns

    # ─── 性能分析 ─────────────────────────────

    @property
    def profile(self) -> ProfileNamespace:
        if self._profile_ns is None:
            self._profile_ns = ProfileNamespace()
        return self._profile_ns

    # ─── 钩子系统 ─────────────────────────────

    @property
    def hooks(self) -> HookNamespace:
        if self._hooks_ns is None:
            self._hooks_ns = HookNamespace()
        return self._hooks_ns

    # ─── 异步操作 ─────────────────────────────

    @property
    def async_(self) -> AsyncNamespace:
        """异步操作（使用 async_ 避免与 Python 关键字 async 冲突）"""
        if self._async_ns is None:
            self._async_ns = AsyncNamespace()
        return self._async_ns

    # ─── 包安装 ─────────────────────────────

    @property
    def install(self) -> InstallNamespace:
        if self._install_ns is None:
            self._install_ns = InstallNamespace()
        return self._install_ns

    # ─── 导出 ─────────────────────────────

    @property
    def export(self) -> ExportNamespace:
        if self._export_ns is None:
            self._export_ns = ExportNamespace()
        return self._export_ns

    # ─── 后台构建 ─────────────────────────────

    @property
    def background(self) -> BackgroundNamespace:
        if self._background_ns is None:
            self._background_ns = BackgroundNamespace()
        return self._background_ns

    # ─── 版本信息 ─────────────────────────────

    @property
    def version(self) -> VersionNamespace:
        if self._version_ns is None:
            self._version_ns = VersionNamespace()
        return self._version_ns

    def version_of(self, package: str) -> Optional[str]:
        """获取已安装包的版本"""
        return get_package_version(package)

    # ─── RC 配置 ─────────────────────────────

    @property
    def rc(self) -> RCConfigNamespace:
        if self._rc_ns is None:
            self._rc_ns = RCConfigNamespace()
        return self._rc_ns

    # ─── 模块级快捷访问 ───────────────────────

    def __getattr__(self, name: str) -> Any:
        """
        支持 lz.numpy, lz.pandas 等快捷方式。
        等价于 lz.module.numpy。
        """
        if name.startswith("_") and name != "__version__":
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        # 1. 检查别名映射
        if name in _ALIAS_MAP:
            return _get_lazy_module(name)._get_module()

        # 2. 尝试自动搜索
        if _config._AUTO_SEARCH_ENABLED:
            found = _search_module(name)
            if found:
                _ALIAS_MAP[name] = found
                return _get_lazy_module(name)._get_module()

        # 3. 尝试符号自动解析
        if _config._SYMBOL_RESOLUTION_CONFIG["auto_symbol"]:
            match = _search_symbol_enhanced(name, auto=True)
            if match:
                return LazySymbol(
                    symbol_name=match.symbol_name,
                    module_name=match.module_name,
                    symbol_type=match.symbol_type,
                )

            # 尝试交互式解析
            if _config._SYMBOL_SEARCH_CONFIG["enabled"]:
                found_module = _handle_symbol_not_found(name)
                if found_module:
                    return _get_lazy_module(name)

        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'. "
            f"Try lz.module.{name} or lz.symbol.search('{name}')"
        )

    def __dir__(self) -> List[str]:
        """支持 tab 补全"""
        base = [
            "module", "alias", "symbol", "cache",
            "config", "analyze", "profile", "hooks",
            "async_", "install", "export", "background",
            "version", "rc",
        ]
        base.extend(_ALIAS_MAP.keys())
        return sorted(set(base))

    @property
    def __version__(self) -> str:
        return _config.__version__

    def __repr__(self) -> str:
        return (
            f"<LazyImport: v{_config.__version__}, "
            f"{len(list_loaded())} loaded, "
            f"{len(_ALIAS_MAP)} aliases>"
        )


# ═══════════════════════════════════════════════════════════════
#  模块级单例（供 from laziest_import import lz 使用）
# ═══════════════════════════════════════════════════════════════

#: 全局 LazyImport 单例实例
#: 用法: from laziest_import import lz; lz.module.numpy; lz.config.debug = True
lz = LazyImport()


# 需要在类定义后导入（因为 LazySymbol 引用 _search_symbol_enhanced）
from ._proxy._symbol import LazySymbol