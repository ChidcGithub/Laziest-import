"""Tests for Phase 2: __init__.py slimming - lazy registry, hooks module, analysis moves."""

import importlib
from typing import Any, Callable, Dict


class TestLazyRegistry:
    """Test the function registration mechanism in _lazy_registry.py."""

    def setup_method(self) -> None:
        import laziest_import._lazy_registry as reg

        reg.clear_resolved()

    def test_register_and_resolve(self):
        from laziest_import._lazy_registry import register, resolve, has

        register("__version__", "laziest_import._config")
        assert has("__version__")

        result = resolve("__version__")
        from laziest_import._config import __version__

        assert result == __version__

    def test_resolve_caches(self):
        from laziest_import._lazy_registry import register, resolve, _RESOLVED

        register("__version__", "laziest_import._config")
        resolve("__version__")
        assert "__version__" in _RESOLVED
        # Resolve again - should use cache
        a = resolve("__version__")
        b = resolve("__version__")
        assert a is b

    def test_resolve_twice_returns_same(self):
        from laziest_import._lazy_registry import register, resolve

        register("__version__", "laziest_import._config")
        a = resolve("__version__")
        b = resolve("__version__")
        assert a is b

    def test_has_returns_false_for_unregistered(self):
        from laziest_import._lazy_registry import has, clear_resolved

        clear_resolved()
        assert not has("__nonexistent_function_xyz__")

    def test_resolve_unregistered_raises(self):
        from laziest_import._lazy_registry import resolve
        from laziest_import._lazy_registry import clear_resolved

        clear_resolved()
        try:
            resolve("__nonexistent_function_xyz__")
            assert False, "Expected KeyError"
        except KeyError:
            pass

    def test_register_does_not_overwrite(self):
        from laziest_import._lazy_registry import register, resolve

        register("__version__", "laziest_import._config")
        register("__version__", "laziest_import._hooks")
        result = resolve("__version__")
        from laziest_import._config import __version__

        assert result == __version__

    def test_clear_resolved(self):
        from laziest_import._lazy_registry import register, resolve, clear_resolved, _RESOLVED

        register("__version__", "laziest_import._config")
        resolve("__version__")
        assert "__version__" in _RESOLVED
        clear_resolved()
        assert "__version__" not in _RESOLVED


class TestHooksModule:
    """Test the new _hooks.py module."""

    def _count_hooks(self) -> int:
        from laziest_import._config import _PRE_IMPORT_HOOKS, _POST_IMPORT_HOOKS

        return len(_PRE_IMPORT_HOOKS), len(_POST_IMPORT_HOOKS)

    def test_module_level_add_pre_hook(self):
        from laziest_import._hooks import add_pre_import_hook, clear_import_hooks

        clear_import_hooks()
        pre_before, post_before = self._count_hooks()
        assert pre_before == 0

        def my_hook(name: str) -> None:
            pass

        add_pre_import_hook(my_hook)
        pre_after, _ = self._count_hooks()
        assert pre_after == 1

        clear_import_hooks()

    def test_module_level_add_post_hook(self):
        from laziest_import._hooks import add_post_import_hook, clear_import_hooks

        clear_import_hooks()
        _, post_before = self._count_hooks()
        assert post_before == 0

        def my_hook(name: str, module: Any) -> None:
            pass

        add_post_import_hook(my_hook)
        _, post_after = self._count_hooks()
        assert post_after == 1

        clear_import_hooks()

    def test_remove_pre_hook(self):
        from laziest_import._hooks import (
            add_pre_import_hook,
            remove_pre_import_hook,
            clear_import_hooks,
        )

        clear_import_hooks()

        def my_hook(name: str) -> None:
            pass

        add_pre_import_hook(my_hook)
        assert remove_pre_import_hook(my_hook) is True
        pre_after, _ = self._count_hooks()
        assert pre_after == 0

    def test_remove_post_hook(self):
        from laziest_import._hooks import (
            add_post_import_hook,
            remove_post_import_hook,
            clear_import_hooks,
        )

        clear_import_hooks()

        def my_hook(name: str, module: Any) -> None:
            pass

        add_post_import_hook(my_hook)
        assert remove_post_import_hook(my_hook) is True
        _, post_after = self._count_hooks()
        assert post_after == 0

    def test_remove_nonexistent_hook(self):
        from laziest_import._hooks import remove_pre_import_hook, remove_post_import_hook

        def my_hook(name: str) -> None:
            pass

        assert remove_pre_import_hook(my_hook) is False
        assert remove_post_import_hook(my_hook) is False

    def test_clear_import_hooks(self):
        from laziest_import._hooks import (
            add_pre_import_hook,
            add_post_import_hook,
            clear_import_hooks,
        )

        clear_import_hooks()

        def pre(name: str) -> None:
            pass

        def post(name: str, mod: Any) -> None:
            pass

        add_pre_import_hook(pre)
        add_post_import_hook(post)
        clear_import_hooks()

        pre_count, post_count = self._count_hooks()
        assert pre_count == 0
        assert post_count == 0

    def test_hooks_accessible_via_module(self):
        from laziest_import import lz

        assert hasattr(lz.hooks, "pre")
        assert hasattr(lz.hooks, "post")
        assert callable(lz.hooks.clear)

        def dummy(name: str) -> None:
            pass

        pre = lz.hooks.pre
        pre += dummy
        pre -= dummy
        post = lz.hooks.post
        post += dummy
        post -= dummy


class TestAnalysisFunctions:
    """Test that analysis convenience functions work from new location."""

    def test_analyze_file_importable(self):
        from laziest_import._analysis import analyze_file

        assert callable(analyze_file)

    def test_analyze_source_importable(self):
        from laziest_import._analysis import analyze_source

        assert callable(analyze_source)

    def test_analyze_directory_importable(self):
        from laziest_import._analysis import analyze_directory

        assert callable(analyze_directory)

    def test_analyze_source_returns_result(self):
        from laziest_import import lz

        result = lz.analyze.code("import numpy\nnp.array([1, 2, 3])")
        assert result is not None
        assert hasattr(result, "file_path")
        assert hasattr(result, "predicted_imports")


class TestLazyFunctionRegistration:
    """Test that lazy functions are properly registered during _do_initialize."""

    def test_symbol_functions_registered(self):
        from laziest_import._lazy_registry import has

        assert has("search_symbol")
        assert has("enable_symbol_search")
        assert has("rebuild_symbol_index")
        assert has("which")
        assert has("which_all")
        assert has("help")

    def test_bg_functions_registered(self):
        from laziest_import._lazy_registry import has

        assert has("start_background_index_build")
        assert has("is_index_building")
        assert has("wait_for_index")

    def test_rc_functions_registered(self):
        from laziest_import._lazy_registry import has

        assert has("load_rc_config")
        assert has("get_rc_value")
        assert has("create_rc_file")

    def test_introspect_functions_registered(self):
        from laziest_import._lazy_registry import has

        assert has("list_module_symbols")
        assert has("get_module_info")
        assert has("search_in_module")

    def test_lazy_resolve_and_cache(self):
        from laziest_import._lazy_registry import resolve, _RESOLVED

        assert "search_symbol" not in _RESOLVED
        fn = resolve("search_symbol")
        assert callable(fn)
        assert "search_symbol" in _RESOLVED


class TestInitGetattr:
    """Test that __getattr__ resolution still works correctly."""

    def test_lazy_function_via_getattr(self):
        import laziest_import

        fn = laziest_import.__getattr__("search_symbol")
        assert callable(fn)

    def test_alias_via_getattr(self):
        import laziest_import

        mod = laziest_import.__getattr__("numpy")
        assert mod is not None

    def test_help_via_getattr(self):
        import laziest_import

        fn = laziest_import.__getattr__("help")
        assert callable(fn)

    def test_negative_cache_works(self):
        import laziest_import
        from laziest_import._config import _NEGATIVE_CACHE, _NEGATIVE_CACHE_TTL

        import time

        _NEGATIVE_CACHE.clear()
        try:
            laziest_import.__getattr__("__clearly_nonexistent_xyz__")
        except AttributeError:
            pass
        assert "__clearly_nonexistent_xyz__" in _NEGATIVE_CACHE
        assert isinstance(_NEGATIVE_CACHE["__clearly_nonexistent_xyz__"], float)
        # Respects TTL (not expired yet)
        assert time.time() - _NEGATIVE_CACHE["__clearly_nonexistent_xyz__"] < _NEGATIVE_CACHE_TTL
        # Still blocks re-access within TTL
        try:
            laziest_import.__getattr__("__clearly_nonexistent_xyz__")
        except AttributeError:
            pass
        else:
            assert False, "Expected AttributeError within TTL"

    def test_reserved_names_rejected(self):
        import laziest_import
        from laziest_import._config import _RESERVED_NAMES

        reserved = next(iter(_RESERVED_NAMES))
        try:
            laziest_import.__getattr__(reserved)
            assert False, "Expected AttributeError"
        except AttributeError:
            pass
