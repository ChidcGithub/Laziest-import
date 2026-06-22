"""Edge-case tests for missing modules, typo handling, and auto-install safety.

These tests simulate common user mistakes and ensure the library fails
gracefully rather than silently doing the wrong thing.
"""

import pytest


# ------------------------------------------------------------------
# Missing module
# ------------------------------------------------------------------
class TestMissingModule:
    """Missing-module behavior."""

    def test_missing_module_raises_clear_error(self):
        import laziest_import as lz

        with pytest.raises((AttributeError, ImportError, ModuleNotFoundError)) as exc_info:
            _ = lz.this_module_definitely_does_not_exist_12345
        msg = str(exc_info.value)
        assert "this_module_definitely" in msg or "12345" in msg

    def test_nonsense_name_fails_even_with_auto_search(self):
        import laziest_import as lz

        lz.config.auto_search = True
        with pytest.raises((AttributeError, ImportError, ModuleNotFoundError)):
            _ = lz.xyzxyzxyz_nonexistent_99999

    def test_negative_cache_speeds_up_repeated_misses(self):
        import time

        import laziest_import as lz

        name = "negative_cache_test_module_12345"
        t0 = time.perf_counter()
        try:
            getattr(lz, name)
        except (AttributeError, ImportError, ModuleNotFoundError):
            pass
        first = time.perf_counter() - t0

        t0 = time.perf_counter()
        try:
            getattr(lz, name)
        except (AttributeError, ImportError, ModuleNotFoundError):
            pass
        second = time.perf_counter() - t0

        assert second < first / 2


# ------------------------------------------------------------------
# Typo correction
# ------------------------------------------------------------------
class TestTypoCorrection:
    """Typo handling should be helpful but not over-aggressive."""

    def test_typo_suggests_real_module(self):
        import laziest_import as lz

        with pytest.raises(AttributeError) as exc_info:
            _ = lz.osz  # typo for os
        msg = str(exc_info.value)
        assert "osz" in msg
        # It should either suggest os or just list available names.
        assert "os" in msg.lower() or "available" in msg.lower()

    def test_unknown_typo_fails_gracefully(self):
        import laziest_import as lz

        with pytest.raises(AttributeError):
            _ = lz.zzzzzzzzzzzzzzzzzzzzzzzzzzz

    def test_failed_access_does_not_pollute_alias_map(self):
        import laziest_import as lz

        before = set(lz._ALIAS_MAP.keys())
        try:
            _ = lz.this_module_definitely_does_not_exist_12345
        except (AttributeError, ImportError, ModuleNotFoundError):
            pass
        after = set(lz._ALIAS_MAP.keys())
        assert not (after - before)

    def test_chained_access_on_missing_module_raises(self):
        import laziest_import as lz

        with pytest.raises((AttributeError, ImportError, ModuleNotFoundError)):
            _ = lz.this_module_definitely_does_not_exist_12345.something


# ------------------------------------------------------------------
# Auto install
# ------------------------------------------------------------------
class TestAutoInstallSafety:
    """Auto-install should never happen by surprise."""

    def test_auto_install_disabled_by_default(self):
        from laziest_import import lz

        assert lz.install.enabled is False

    def test_non_interactive_missing_module_handled_safely(self):
        from laziest_import import lz

        fake_pkg = "laziest_import_fake_nonexistent_pkg_12345"
        lz.install.enable(interactive=False)
        lz.config.auto_search = True
        try:
            with pytest.raises((AttributeError, ImportError, ModuleNotFoundError)):
                _ = getattr(lz, fake_pkg)
        finally:
            lz.install.disable()

    def test_interactive_install_declined_in_non_tty(self):
        from laziest_import._config import _AUTO_INSTALL_CONFIG
        from laziest_import._install import _interactive_install_confirm

        old = dict(_AUTO_INSTALL_CONFIG)
        try:
            _AUTO_INSTALL_CONFIG["interactive"] = True
            confirmed = _interactive_install_confirm("missing_mod", "missing-mod")
            assert confirmed is False
        finally:
            _AUTO_INSTALL_CONFIG.update(old)

    def test_auto_install_config_isolation(self):
        from laziest_import import lz

        lz.install.enable(interactive=False, index="https://example.com/simple")
        try:
            cfg = lz.install.auto
            assert cfg.get("index") == "https://example.com/simple"
            assert cfg.get("interactive") is False
        finally:
            lz.install.disable()
