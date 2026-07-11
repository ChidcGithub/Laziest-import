"""
LazyModule class for lazy loading modules.
"""

import asyncio
import importlib
import logging
import time
from types import ModuleType
from typing import Any, Optional

from .. import _config
from .._cache import _record_module_load
from .._fuzzy import _search_module
from ._submodule import LazySubmodule


class LazyModule:
    """
    Lazy loading module proxy class.

    Imports the actual module only when attributes are accessed.
    Supports auto-search for unregistered modules and submodule lazy loading.
    """

    __slots__ = (
        "_alias",
        "_auto_searched",
        "_cached_module",
        "_module_name",
        "_submodule_cache",
    )

    def __init__(self, alias: str, module_name: str, auto_searched: bool = False):
        object.__setattr__(self, "_alias", alias)
        object.__setattr__(self, "_module_name", module_name)
        object.__setattr__(self, "_cached_module", None)
        object.__setattr__(self, "_auto_searched", auto_searched)
        object.__setattr__(self, "_submodule_cache", {})

    @staticmethod
    def _do_import_with_retry(name: str, config: Any) -> Any:
        if not config._RETRY_CONFIG["enabled"]:
            return importlib.import_module(name)

        max_retries = config._RETRY_CONFIG["max_retries"]
        retry_delay = config._RETRY_CONFIG["retry_delay"]
        retry_modules = config._RETRY_CONFIG["retry_modules"]

        if retry_modules and name.split(".", maxsplit=1)[0] not in retry_modules:
            return importlib.import_module(name)

        try:
            loop = asyncio.get_running_loop()
            in_async_context = loop is not None
        except RuntimeError:
            in_async_context = False

        if in_async_context:
            if config._DEBUG_MODE:
                logging.debug(
                    f"[laziest-import] In async context, disabling retry for '{name}' "
                    f"(sleep would block event loop)"
                )
            return importlib.import_module(name)

        last_error: Optional[ImportError] = None
        for attempt in range(max_retries + 1):
            try:
                return importlib.import_module(name)
            except ImportError as e:
                last_error = e
                if attempt < max_retries:
                    if config._DEBUG_MODE:
                        logging.info(f"Retry {attempt + 1}/{max_retries} for {name}")
                    time.sleep(retry_delay)
        raise (
            last_error
            if last_error is not None
            else ImportError(f"Failed to import {name}")
        )

    @staticmethod
    def _get_current_traced_memory() -> int:
        try:
            import tracemalloc

            if tracemalloc.is_tracing():
                return tracemalloc.get_traced_memory()[0]
        except Exception:  # noqa: S110 — tracemalloc not always available
            pass
        return 0

    def _record_import_stats(
        self, module_name: str, alias: str, elapsed: float, mem_delta: int, config: Any
    ) -> None:
        config._IMPORT_STATS.total_imports += 1
        config._IMPORT_STATS.total_time += elapsed
        config._IMPORT_STATS.module_times[module_name] = elapsed
        config._IMPORT_STATS.module_access_counts[alias] = 1

        _record_module_load(module_name)

        from .._analysis import _profiler

        if _profiler.is_active():
            _profiler.record_load(module_name, elapsed, mem_delta)

    def _auto_search_fallback(self, module_name: str, alias: str, config: Any) -> Any | None:
        if not config._AUTO_SEARCH_ENABLED:
            return None
        found_name = _search_module(module_name.split(".", maxsplit=1)[0])
        if not found_name or found_name == module_name:
            return None
        try:
            start_time = time.perf_counter()
            module = LazyModule._do_import_with_retry(found_name, config)
            object.__setattr__(self, "_module_name", found_name)
            object.__setattr__(self, "_cached_module", module)
            object.__setattr__(self, "_auto_searched", True)
            config._ALIAS_MAP[alias] = found_name

            elapsed = time.perf_counter() - start_time
            config._IMPORT_STATS.total_imports += 1
            config._IMPORT_STATS.total_time += elapsed
            config._IMPORT_STATS.module_times[found_name] = elapsed
            return module
        except ImportError:
            return None

    def _auto_install_fallback(self, module_name: str, alias: str, config: Any, start_time: float) -> Any:
        from .._install import (
            _get_pip_package_name,
            _install_package_sync,
            _interactive_install_confirm,
            rebuild_module_cache,
        )

        pip_package = _get_pip_package_name(module_name)

        should_install = True
        if config._AUTO_INSTALL_CONFIG["interactive"]:
            should_install = _interactive_install_confirm(module_name, pip_package)

        if should_install:
            success, message = _install_package_sync(
                pip_package,
                index=config._AUTO_INSTALL_CONFIG["index"],
                extra_args=config._AUTO_INSTALL_CONFIG["extra_args"],
                prefer_uv=config._AUTO_INSTALL_CONFIG["prefer_uv"],
                silent=config._AUTO_INSTALL_CONFIG["silent"],
            )
            if success:
                if config._DEBUG_MODE:
                    logging.info(f"[laziest-import] {message}")
                rebuild_module_cache()
                try:
                    module = LazyModule._do_import_with_retry(module_name, config)
                    elapsed = time.perf_counter() - start_time
                    self._record_import_stats(module_name, alias, elapsed, 0, config)
                    object.__setattr__(self, "_cached_module", module)
                    return module
                except ImportError as import_error:
                    raise ImportError(
                        f"Module '{module_name}' was installed but still cannot be imported. "
                        f"Error: {import_error}"
                    ) from import_error
        return None

    @staticmethod
    def _run_hooks(hooks: list, module_name: str, config: Any, module: Any = None) -> None:
        for hook in hooks:
            try:
                if module is None:
                    hook(module_name)
                else:
                    hook(module_name, module)
            except Exception as e:
                if config._DEBUG_MODE:
                    logging.warning(f"Import hook failed for {module_name}: {e}")

    def _get_module(self) -> Any:
        c = _config

        cached = object.__getattribute__(self, "_cached_module")
        if cached is not None:
            alias = object.__getattribute__(self, "_alias")
            c._IMPORT_STATS.module_access_counts[alias] = (
                c._IMPORT_STATS.module_access_counts.get(alias, 0) + 1
            )
            c._CACHE_STATS["module_hits"] += 1
            return cached

        c._CACHE_STATS["module_misses"] += 1

        module_name = object.__getattribute__(self, "_module_name")
        alias = object.__getattribute__(self, "_alias")

        importing_modules = _config.get_importing_modules()
        if module_name in importing_modules:
            return importlib.import_module(module_name)

        importing_modules.add(module_name)

        try:
            LazyModule._run_hooks(c._PRE_IMPORT_HOOKS, module_name, c)

            start_time = time.perf_counter()
            mem_before = LazyModule._get_current_traced_memory()

            try:
                module = LazyModule._do_import_with_retry(module_name, c)
                elapsed = time.perf_counter() - start_time
                mem_delta = max(0, LazyModule._get_current_traced_memory() - mem_before)

                self._record_import_stats(module_name, alias, elapsed, mem_delta, c)
                object.__setattr__(self, "_cached_module", module)
                LazyModule._run_hooks(c._POST_IMPORT_HOOKS, module_name, c, module)

                if c._DEBUG_MODE:
                    logging.info(
                        f"[laziest-import] Loaded module '{module_name}' in {elapsed * 1000:.2f}ms"
                    )

                return module
            except ImportError as e:
                result = self._auto_search_fallback(module_name, alias, c)
                if result is not None:
                    return result
                result = self._auto_install_fallback(module_name, alias, c, start_time)
                if result is not None:
                    return result
                raise ImportError(
                    f"Cannot import module '{module_name}' (alias '{alias}'). "
                    f"Please ensure the module is installed: pip install {module_name.split('.')[0]}"
                ) from e
        finally:
            importing_modules.discard(module_name)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            allowed_dunder = {
                "__name__",
                "__file__",
                "__path__",
                "__package__",
                "__loader__",
                "__spec__",
                "__doc__",
                "__version__",
            }
            if name not in allowed_dunder:
                raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        module = self._get_module()
        attr = getattr(module, name)

        if isinstance(attr, ModuleType):
            submodule_cache = object.__getattribute__(self, "_submodule_cache")
            # Use full_name as cache key to avoid conflicts between different parent modules
            full_name = f"{object.__getattribute__(self, '_module_name')}.{name}"
            if full_name not in submodule_cache:
                submodule_cache[full_name] = LazySubmodule(full_name, self, name)
            return submodule_cache[full_name]

        return attr

    def __dir__(self) -> list[str]:
        module = self._get_module()
        return dir(module)

    def __repr__(self) -> str:
        module_name = object.__getattribute__(self, "_module_name")
        cached = object.__getattribute__(self, "_cached_module")
        if cached is not None:
            return f"<LazyModule '{module_name}' (loaded)>"
        return f"<LazyModule '{module_name}' (not loaded)>"

    def __call__(self, *args, **kwargs) -> Any:
        module = self._get_module()
        if callable(module):
            return module(*args, **kwargs)
        module_name = object.__getattribute__(self, "_module_name")
        raise TypeError(f"Module '{module_name}' ({type(module).__name__}) is not callable")
