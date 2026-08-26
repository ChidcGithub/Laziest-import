"""Tests for type-stub (.pyi) based symbol indexing."""

import ast
import sys

import pytest

from laziest_import import _config
from laziest_import._stub_index import (
    _collect_stub_symbols_from_source,
    _find_stub_path,
    _format_function_signature,
    _scan_stub_symbols,
)

# ── Parsing ─────────────────────────────────────────────────


class TestParseSymbols:
    def test_functions_classes_variables(self):
        source = "def sqrt(x: float) -> float: ...\nclass ndarray: ...\nversion: str\n"
        symbols = _collect_stub_symbols_from_source(source, "m")
        assert "sqrt" in symbols and symbols["sqrt"][0][1] == "function"
        assert "ndarray" in symbols and symbols["ndarray"][0][1] == "class"
        assert "version" in symbols and symbols["version"][0][1] == "variable"

    def test_signature_extraction(self):
        source = "def connect(host: str, port: int = 5432, *args: str, timeout: float = 1.0, **kwargs: bool) -> bool: ...\n"
        symbols = _collect_stub_symbols_from_source(source, "m")
        sig = symbols["connect"][0][2]
        assert sig is not None
        assert "host: str" in sig
        assert "port: int = 5432" in sig
        assert "*args: str" in sig
        assert "timeout: float = 1.0" in sig
        assert "**kwargs: bool" in sig
        assert "-> bool" in sig

    def test_conditional_guards_descended(self):
        source = (
            "if sys.version_info >= (3, 10):\n"
            "    def new_func() -> None: ...\n"
            "else:\n"
            "    def old_func() -> None: ...\n"
            "try:\n"
            "    class Guarded: ...\n"
            "except AttributeError:\n"
            "    pass\n"
        )
        symbols = _collect_stub_symbols_from_source(source, "m")
        assert "new_func" in symbols
        assert "old_func" in symbols
        assert "Guarded" in symbols

    def test_overloads_keep_first(self):
        source = (
            "@overload\ndef parse(x: int) -> int: ...\n@overload\ndef parse(x: str) -> str: ...\n"
        )
        symbols = _collect_stub_symbols_from_source(source, "m")
        locations = symbols["parse"]
        assert len(locations) == 1

    def test_private_skipped_by_default(self):
        source = "def _hidden() -> None: ...\ndef visible() -> None: ...\n"
        symbols = _collect_stub_symbols_from_source(source, "m")
        assert "_hidden" not in symbols
        assert "visible" in symbols

    def test_class_body_not_descended(self):
        source = "class A:\n    def method(self) -> None: ...\n"
        symbols = _collect_stub_symbols_from_source(source, "m")
        assert "A" in symbols
        assert "method" not in symbols

    def test_max_symbols_cap(self):
        cap = 10
        lines = [f"def func_{i}() -> None: ..." for i in range(50)]
        symbols = _collect_stub_symbols_from_source("\n".join(lines), "m", max_symbols=cap)
        assert len(symbols) == cap

    def test_syntax_error_raises(self):
        with pytest.raises(SyntaxError):
            _collect_stub_symbols_from_source("def broken(:\n", "m")


class TestFormatSignature:
    def test_no_args(self):
        tree = ast.parse("def f(): ...")
        assert _format_function_signature(tree.body[0]) == "()"

    def test_long_signature_truncated(self):
        max_len = 160
        many = ", ".join(f"a{i}: int" for i in range(60))
        tree = ast.parse(f"def f({many}) -> None: ...")
        sig = _format_function_signature(tree.body[0])
        assert sig is not None
        assert len(sig) <= max_len


# ── Stub discovery ──────────────────────────────────────────


@pytest.fixture()
def fake_pkg(tmp_path, monkeypatch):
    """A fake installed package with stubs, on sys.path."""
    pkg = tmp_path / "stubpkg"
    sub = pkg / "sub"
    sub.mkdir(parents=True)
    (pkg / "__init__.py").write_text("def runtime_only() -> None: ...\n", encoding="utf-8")
    (pkg / "__init__.pyi").write_text(
        "def top_fn(x: int) -> str: ...\nclass TopClass: ...\n", encoding="utf-8"
    )
    (sub / "__init__.py").write_text("", encoding="utf-8")
    (sub / "__init__.pyi").write_text("def sub_fn() -> None: ...\n", encoding="utf-8")

    monkeypatch.syspath_prepend(str(tmp_path))
    yield "stubpkg"
    monkeypatch.undo()
    sys.modules.pop("stubpkg", None)
    sys.modules.pop("stubpkg.sub", None)


class TestFindStubPath:
    def test_top_level_module(self, fake_pkg):
        path = _find_stub_path(fake_pkg)
        assert path is not None
        assert path.name == "__init__.pyi"
        assert path.parent.name == "stubpkg"

    def test_submodule(self, fake_pkg):
        path = _find_stub_path("stubpkg.sub")
        assert path is not None
        assert path.name == "__init__.pyi"
        assert path.parent.name == "sub"

    def test_missing_module(self):
        assert _find_stub_path("no_such_pkg_xyz_12345") is None


# ── Zero-side-effect guarantee ──────────────────────────────


class TestNoImportSideEffect:
    def test_hostile_init_not_executed(self, tmp_path, monkeypatch):
        """The flagship property: symbols indexed even when __init__.py would crash."""
        pkg = tmp_path / "hostilepkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text(
            "raise RuntimeError('module code must never run during index build')\n",
            encoding="utf-8",
        )
        (pkg / "__init__.pyi").write_text(
            "def safe_fn(a: int, b: str = 'x') -> bool: ...\n", encoding="utf-8"
        )
        monkeypatch.syspath_prepend(str(tmp_path))
        try:
            symbols = _scan_stub_symbols("hostilepkg")
            assert "safe_fn" in symbols
            assert symbols["safe_fn"][0][1] == "function"
            assert "hostilepkg" not in sys.modules
        finally:
            monkeypatch.undo()

    def test_parent_package_not_imported_for_submodule_scan(self, tmp_path, monkeypatch):
        pkg = tmp_path / "hostileparent"
        sub = pkg / "submod"
        sub.mkdir(parents=True)
        (pkg / "__init__.py").write_text("raise RuntimeError('nope')\n", encoding="utf-8")
        # No __init__.pyi for the package — discovery must still reach the submodule
        (sub / "__init__.pyi").write_text("def deep_fn() -> None: ...\n", encoding="utf-8")
        monkeypatch.syspath_prepend(str(tmp_path))
        try:
            symbols = _scan_stub_symbols("hostileparent.submod")
            assert "deep_fn" in symbols
            assert "hostileparent" not in sys.modules
        finally:
            monkeypatch.undo()


# ── Integration with the scan pipeline ──────────────────────


class TestPipelineIntegration:
    def test_auto_prefers_stub(self, fake_pkg):
        before = _config._CACHE_STATS["stub_scanned_modules"]
        from laziest_import._symbol import _scan_module_symbols_auto

        symbols = _scan_module_symbols_auto(fake_pkg, depth=0)
        assert "top_fn" in symbols
        assert "TopClass" in symbols
        assert _config._CACHE_STATS["stub_scanned_modules"] == before + 1

    def test_disabled_falls_back_to_import(self, fake_pkg, monkeypatch):
        monkeypatch.setitem(_config._STUB_INDEX_CONFIG, "enabled", False)
        from laziest_import._symbol import _scan_module_symbols_auto

        symbols = _scan_module_symbols_auto(fake_pkg, depth=0)
        # Falls back to real import — sees runtime-defined names only,
        # proving the stub was not consulted.
        assert "runtime_only" in symbols
        assert "top_fn" not in symbols

    def test_fallback_when_no_stub(self):
        from laziest_import._symbol import _scan_module_symbols_auto

        before = _config._CACHE_STATS["stub_scanned_modules"]
        symbols = _scan_module_symbols_auto("json", depth=0)
        assert "dump" in symbols or "dumps" in symbols
        assert _config._CACHE_STATS["stub_scanned_modules"] >= before
