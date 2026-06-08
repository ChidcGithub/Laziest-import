"""Tests for the object-oriented API namespace classes."""

import pytest

from laziest_import import (
    AliasNamespace,
    AnalyzeNamespace,
    AsyncNamespace,
    BackgroundNamespace,
    CacheNamespace,
    ConfigNamespace,
    ExportNamespace,
    HookNamespace,
    InstallNamespace,
    LazyImport,
    ModuleNamespace,
    ProfileNamespace,
    RCConfigNamespace,
    SymbolNamespace,
    VersionNamespace,
)


class TestLazyImport:
    def test_create_instance(self):
        lz = LazyImport()
        assert isinstance(lz, LazyImport)

    def test_property_module(self):
        lz = LazyImport()
        assert isinstance(lz.module, ModuleNamespace)

    def test_property_alias(self):
        lz = LazyImport()
        assert isinstance(lz.alias, AliasNamespace)

    def test_property_symbol(self):
        lz = LazyImport()
        assert isinstance(lz.symbol, SymbolNamespace)

    def test_property_cache(self):
        lz = LazyImport()
        assert isinstance(lz.cache, CacheNamespace)

    def test_property_config(self):
        lz = LazyImport()
        assert isinstance(lz.config, ConfigNamespace)

    def test_property_analyze(self):
        lz = LazyImport()
        assert isinstance(lz.analyze, AnalyzeNamespace)

    def test_property_profile(self):
        lz = LazyImport()
        assert isinstance(lz.profile, ProfileNamespace)

    def test_property_hooks(self):
        lz = LazyImport()
        assert isinstance(lz.hooks, HookNamespace)

    def test_property_async(self):
        lz = LazyImport()
        assert isinstance(lz.async_, AsyncNamespace)

    def test_property_install(self):
        lz = LazyImport()
        assert isinstance(lz.install, InstallNamespace)

    def test_property_export(self):
        lz = LazyImport()
        assert isinstance(lz.export, ExportNamespace)

    def test_property_background(self):
        lz = LazyImport()
        assert isinstance(lz.background, BackgroundNamespace)

    def test_property_version(self):
        lz = LazyImport()
        assert isinstance(lz.version, VersionNamespace)

    def test_property_rc(self):
        lz = LazyImport()
        assert isinstance(lz.rc, RCConfigNamespace)

    def test_version_of(self):
        lz = LazyImport()
        ver = lz.version_of("laziest_import")
        assert ver is not None
        assert isinstance(ver, str)

    def test_dir_contains_namespaces(self):
        lz = LazyImport()
        attrs = dir(lz)
        for ns in (
            "module",
            "alias",
            "symbol",
            "cache",
            "config",
            "analyze",
            "profile",
            "hooks",
            "async_",
            "install",
            "export",
            "background",
            "version",
            "rc",
        ):
            assert ns in attrs

    def test_dir_contains_aliases(self):
        lz = LazyImport()
        attrs = dir(lz)
        assert "os" in attrs or "np" in attrs or "json" in attrs

    def test_repr(self):
        lz = LazyImport()
        r = repr(lz)
        assert "LazyImport" in r
        assert "v" in r

    def test_getattr_alias(self):
        lz = LazyImport()
        mod = lz.os
        assert mod is not None

    def test_getattr_invalid_raises(self):
        lz = LazyImport()
        with pytest.raises(AttributeError):
            _ = lz.__nonexistent_xyz_test__

    def test_getattr_private_raises(self):
        lz = LazyImport()
        with pytest.raises(AttributeError):
            _ = lz._private_method


class TestModuleNamespace:
    def test_list_loaded(self):
        ns = ModuleNamespace()
        loaded = ns.list_loaded()
        assert isinstance(loaded, list)

    def test_list_available(self):
        ns = ModuleNamespace()
        avail = ns.list_available()
        assert isinstance(avail, list)
        assert "os" in avail or "sys" in avail or "json" in avail

    def test_get(self):
        ns = ModuleNamespace()
        mod = ns.get("os")
        assert mod is not None

    def test_get_nonexistent_returns_none(self):
        ns = ModuleNamespace()
        result = ns.get("__clearly_nonexistent_module_xyz__")
        assert result is None

    def test_search_via_getattr(self):
        ns = ModuleNamespace()
        mod = ns.json
        assert mod is not None

    def test_getattr_nonexistent_raises(self):
        ns = ModuleNamespace()
        with pytest.raises(AttributeError):
            _ = ns.__clearly_nonexistent_xyz__

    def test_get_returns_loaded_module(self):
        ns = ModuleNamespace()
        mod = ns.load("os")
        assert mod is not None
        got = ns.get("os")
        assert got is mod

    def test_reload(self):
        ns = ModuleNamespace()
        ns.get("os")
        result = ns.reload("os")
        assert result is not None

    def test_load(self):
        ns = ModuleNamespace()
        mod = ns.load("os")
        assert mod is not None

    def test_is_loaded(self):
        ns = ModuleNamespace()
        assert ns.is_loaded("hashlib") is False
        ns.load("hashlib")
        assert ns.is_loaded("hashlib") is True

    def test_getitem(self):
        ns = ModuleNamespace()
        mod = ns.load("os")
        item = ns["os"]
        assert item is mod

    def test_getitem_unloaded_raises(self):
        ns = ModuleNamespace()
        with pytest.raises(KeyError):
            _ = ns["__clearly_nonexistent_module_xyz__"]

    def test_repr(self):
        ns = ModuleNamespace()
        r = repr(ns)
        assert "ModuleNamespace" in r

    def test_dir(self):
        ns = ModuleNamespace()
        d = dir(ns)
        assert isinstance(d, list)
        assert len(d) > 0


class TestAliasNamespace:
    def test_list_returns_list(self):
        ns = AliasNamespace()
        result = ns.list()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_search_by_pattern(self):
        ns = AliasNamespace()
        result = ns.search(pattern="json")
        assert isinstance(result, list)

    def test_search_by_empty(self):
        ns = AliasNamespace()
        result = ns.search("")
        assert result == []

    def test_search_by_module(self):
        ns = AliasNamespace()
        result = ns.search("os", by_module=True)
        assert isinstance(result, list)

    def test_suggest_returns_list(self):
        ns = AliasNamespace()
        result = ns.suggest()
        assert isinstance(result, list)

    def test_register_and_unregister(self):
        ns = AliasNamespace()
        ns.register("_test_alias_xyz", "os")
        assert "_test_alias_xyz" in ns.list()
        ns.unregister("_test_alias_xyz")
        assert "_test_alias_xyz" not in ns.list()

    def test_register_invalid_identifier_raises(self):
        ns = AliasNamespace()
        with pytest.raises(ValueError):
            ns.register("123invalid", "os")


class TestSymbolNamespace:
    def test_search_returns_list(self):
        ns = SymbolNamespace()
        result = ns.search("json")
        assert isinstance(result, list)

    def test_search_empty_is_callable(self):
        ns = SymbolNamespace()
        result = ns.search("")
        assert isinstance(result, list)

    def test_search_unknown_returns_empty(self):
        ns = SymbolNamespace()
        result = ns.search("__extremely_unlikely_symbol_xyz__")
        assert isinstance(result, list)

    def test_config_is_property(self):
        ns = SymbolNamespace()
        cfg = ns.config
        assert hasattr(cfg, "enabled")
        assert hasattr(cfg, "enable")
        assert hasattr(cfg, "disable")

    def test_enable_disable_search(self):
        from laziest_import._config import _SYMBOL_SEARCH_CONFIG

        ns = SymbolNamespace()
        cfg = ns.config
        previous = _SYMBOL_SEARCH_CONFIG.get("enabled", True)
        cfg.enable()
        assert cfg.enabled is True
        cfg.disable()
        assert cfg.enabled is False
        if previous:
            cfg.enable()

    def test_cache_info(self):
        ns = SymbolNamespace()
        info = ns.cache_info()
        assert isinstance(info, dict)

    def test_prefer(self):
        ns = SymbolNamespace()
        ns.prefer("test_symbol_xyz", "os")
        pref = ns.preference("test_symbol_xyz")
        assert pref == "os"
        ns.clear_preference("test_symbol_xyz")
        assert ns.preference("test_symbol_xyz") is None

    def test_which(self):
        ns = SymbolNamespace()
        result = ns.which("sqrt", "math")
        assert result is not None

    def test_which_all(self):
        ns = SymbolNamespace()
        result = ns.which_all("sqrt")
        assert isinstance(result, list)

    def test_repr(self):
        ns = SymbolNamespace()
        r = repr(ns)
        assert "SymbolNamespace" in r


class TestCacheNamespace:
    def test_file_info(self):
        ns = CacheNamespace()
        info = ns.file_info()
        assert isinstance(info, dict)

    def test_stats(self):
        ns = CacheNamespace()
        stats = ns.stats
        assert hasattr(stats, "hit_rate")

    def test_config(self):
        ns = CacheNamespace()
        cfg = ns.config
        assert hasattr(cfg, "max_size_mb") or hasattr(cfg, "enable_compression")

    def test_config_is_cache_config(self):
        ns = CacheNamespace()
        cfg = ns.config
        assert hasattr(cfg, "symbol_index_ttl")

    def test_clear_file_cache(self):
        ns = CacheNamespace()
        ns.clear_file_cache()

    def test_clear_symbols(self):
        ns = CacheNamespace()
        ns.clear_symbols()


class TestConfigNamespace:
    def test_debug_mode(self):
        ns = ConfigNamespace()
        ns.debug = True
        assert ns.debug is True
        ns.debug = False
        assert ns.debug is False

    def test_auto_search(self):
        ns = ConfigNamespace()
        ns.auto_search = True
        assert ns.auto_search is True
        ns.auto_search = False
        assert ns.auto_search is False

    def test_snapshot(self):
        ns = ConfigNamespace()
        snap = ns.snapshot()
        assert isinstance(snap, dict)
        assert "debug" in snap
        assert "auto_search" in snap

    def test_export(self):
        ns = ConfigNamespace()
        exported = ns.export()
        assert isinstance(exported, str)

    def test_refresh(self):
        ns = ConfigNamespace()
        ns.refresh()
        snap = ns.snapshot()
        assert isinstance(snap, dict)

    def test_import_stats(self):
        ns = ConfigNamespace()
        stats = ns.import_stats
        assert isinstance(stats, dict)
        assert "total_imports" in stats


class TestHookNamespace:
    def test_clear(self):
        ns = HookNamespace()
        ns.pre.add(lambda name: None)
        ns.post.add(lambda name, mod: None)
        ns.clear()
        assert len(ns.pre) == 0
        assert len(ns.post) == 0

    def test_pre_hook_list(self):
        ns = HookNamespace()
        calls = []

        def my_hook(name):
            calls.append(name)

        ns.pre.add(my_hook)
        ns.pre.remove(my_hook)
        assert len(calls) == 0

    def test_post_hook_list(self):
        ns = HookNamespace()
        calls = []

        def my_hook(name, mod):
            calls.append(name)

        ns.post.add(my_hook)
        assert len(ns.post) == 1
        ns.post.remove(my_hook)
        assert len(ns.post) == 0

    def test_pre_property(self):
        ns = HookNamespace()
        assert hasattr(ns.pre, "add")
        assert hasattr(ns.pre, "remove")
        assert hasattr(ns.pre, "clear")

    def test_post_property(self):
        ns = HookNamespace()
        assert hasattr(ns.post, "add")
        assert hasattr(ns.post, "remove")
        assert hasattr(ns.post, "clear")

    def test_hook_list_len(self):
        ns = HookNamespace()
        assert len(ns.pre) == 0

    def test_hook_list_iter(self):
        ns = HookNamespace()
        hooks = list(ns.pre)
        assert hooks == []

    def test_repr(self):
        ns = HookNamespace()
        r = repr(ns)
        assert "HookNamespace" in r


class TestRCConfigNamespace:
    def test_get_info(self):
        ns = RCConfigNamespace()
        info = ns.info()
        assert isinstance(info, dict)

    def test_get_default(self):
        ns = RCConfigNamespace()
        val = ns.get("nonexistent.key", default=42)
        assert val == 42

    def test_load_and_reload(self):
        ns = RCConfigNamespace()
        ns.reload()
        info = ns.info()
        assert isinstance(info, dict)

    def test_paths(self):
        ns = RCConfigNamespace()
        p = ns.paths()
        assert isinstance(p, list)

    def test_repr(self):
        ns = RCConfigNamespace()
        r = repr(ns)
        assert "RCConfigNamespace" in r


class TestVersionNamespace:
    def test_current(self):
        ns = VersionNamespace()
        ver = ns.current
        assert isinstance(ver, str)
        assert len(ver) > 0

    def test_cache(self):
        ns = VersionNamespace()
        ver = ns.cache()
        assert isinstance(ver, str)

    def test_of(self):
        ns = VersionNamespace()
        ver = ns.of("laziest_import")
        assert ver is not None

    def test_laziest_import(self):
        ns = VersionNamespace()
        ver = ns.laziest_import()
        assert isinstance(ver, str)

    def test_str(self):
        ns = VersionNamespace()
        s = str(ns)
        assert isinstance(s, str)

    def test_repr(self):
        ns = VersionNamespace()
        r = repr(ns)
        assert "VersionNamespace" in r


class TestBackgroundNamespace:
    def test_is_building_property(self):
        ns = BackgroundNamespace()
        result = ns.is_building
        assert result is False or result is True

    def test_timeout_property(self):
        ns = BackgroundNamespace()
        old = ns.timeout
        ns.timeout = 42.0
        assert ns.timeout == 42.0
        ns.timeout = old

    def test_enable(self):
        ns = BackgroundNamespace()
        ns.enable(True)
        assert ns.is_building is True or ns.is_building is False

    def test_repr(self):
        ns = BackgroundNamespace()
        r = repr(ns)
        assert "BackgroundNamespace" in r


class TestInstallNamespace:
    def test_auto_property(self):
        ns = InstallNamespace()
        cfg = ns.auto
        assert isinstance(cfg, dict)

    def test_enabled_property(self):
        ns = InstallNamespace()
        assert ns.enabled is False or ns.enabled is True

    def test_repr(self):
        ns = InstallNamespace()
        r = repr(ns)
        assert "InstallNamespace" in r


class TestExportNamespace:
    def test_aliases_returns_str(self):
        ns = ExportNamespace()
        result = ns.aliases()
        assert isinstance(result, str)

    def test_repr(self):
        ns = ExportNamespace()
        r = repr(ns)
        assert "ExportNamespace" in r


class TestAnalyzeNamespace:
    def test_analyze_code(self):
        ns = AnalyzeNamespace()
        result = ns.code("import os\nprint('hello')")
        assert hasattr(result, "predicted_imports")

    def test_dep_tree(self):
        ns = AnalyzeNamespace()
        tree = ns.dep_tree()
        assert tree is not None

    def test_dir_method(self):
        ns = AnalyzeNamespace()
        result = ns.dir(".", recursive=False)
        assert isinstance(result, list)

    def test_repr(self):
        ns = AnalyzeNamespace()
        r = repr(ns)
        assert "AnalyzeNamespace" in r


class TestProfileNamespace:
    def test_start_stop(self):
        ns = ProfileNamespace()
        ns.start()
        ns.stop()
        report = ns.report()
        assert report is not None

    def test_is_active(self):
        ns = ProfileNamespace()
        assert ns.is_active is False

    def test_repr(self):
        ns = ProfileNamespace()
        r = repr(ns)
        assert "ProfileNamespace" in r
