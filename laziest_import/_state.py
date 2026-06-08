"""
State diagnostics for laziest-import.

This module provides the AppState class which is a read-only property-based
view of laziest_import._config module globals. The actual state lives
exclusively in _config.py.
"""

import sys
from typing import Any, Dict, Optional, Set


def _config():
    return sys.modules["laziest_import._config"]


class AppState:
    """Diagnostic property-based bridge to laziest_import._config globals."""

    @classmethod
    def _cfg(cls):
        return sys.modules["laziest_import._config"]

    # ── init state ────────────────────────────────────
    @property
    def initializing(self) -> bool:
        return self._cfg()._INITIALIZING

    @property
    def initialized(self) -> bool:
        return self._cfg()._INITIALIZED

    @property
    def init_failed(self) -> bool:
        return self._cfg()._INIT_FAILED

    @property
    def init_error(self) -> Optional[str]:
        return self._cfg()._INIT_ERROR

    # ── core config ──────────────────────────────────
    @property
    def auto_search_enabled(self) -> bool:
        return self._cfg()._AUTO_SEARCH_ENABLED

    @property
    def debug_mode(self) -> bool:
        return self._cfg()._DEBUG_MODE

    @property
    def file_cache_enabled(self) -> bool:
        return self._cfg()._FILE_CACHE_ENABLED

    # ── caches ───────────────────────────────────────
    @property
    def known_modules_cache(self) -> Optional[set[str]]:
        return self._cfg()._KNOWN_MODULES_CACHE

    @property
    def known_modules_cache_time(self) -> float:
        return self._cfg()._KNOWN_MODULES_CACHE_TIME

    @property
    def known_modules_cache_ttl(self) -> float:
        return self._cfg()._KNOWN_MODULES_CACHE_TTL

    @property
    def known_modules_class_map(self) -> dict[str, str]:
        return self._cfg()._CLASS_TO_MODULE_CACHE

    @property
    def alias_map(self) -> dict[str, str]:
        return self._cfg()._ALIAS_MAP

    @property
    def lazy_modules(self) -> dict[str, Any]:
        return self._cfg()._LAZY_MODULES

    @property
    def negative_cache(self) -> dict[str, float]:
        return self._cfg()._NEGATIVE_CACHE

    @property
    def symbol_cache(self):
        return self._cfg()._SYMBOL_CACHE

    @property
    def stdlib_symbol_cache(self):
        return self._cfg()._STDLIB_SYMBOL_CACHE

    @property
    def third_party_symbol_cache(self):
        return self._cfg()._THIRD_PARTY_SYMBOL_CACHE

    @property
    def symbol_index_built(self) -> bool:
        return self._cfg()._SYMBOL_INDEX_BUILT

    @property
    def stdlib_cache_built(self) -> bool:
        return self._cfg()._STDLIB_CACHE_BUILT

    @property
    def third_party_cache_built(self) -> bool:
        return self._cfg()._THIRD_PARTY_CACHE_BUILT

    @property
    def symbol_preferences(self):
        return self._cfg()._SYMBOL_PREFERENCES

    @property
    def symbol_resolution_config(self):
        return self._cfg()._SYMBOL_RESOLUTION_CONFIG

    @property
    def symbol_search_config(self):
        return self._cfg()._SYMBOL_SEARCH_CONFIG

    @property
    def confirmed_mappings(self) -> dict[str, str]:
        return self._cfg()._CONFIRMED_MAPPINGS

    @property
    def module_priority(self) -> dict[str, int]:
        return self._cfg()._MODULE_PRIORITY

    # ── config dicts ──────────────────────────────────
    @property
    def import_stats(self):
        return self._cfg()._IMPORT_STATS

    @property
    def cache_stats(self) -> dict[str, Any]:
        return self._cfg()._CACHE_STATS

    @property
    def retry_config(self) -> dict[str, Any]:
        return self._cfg()._RETRY_CONFIG

    @property
    def auto_install_config(self) -> dict[str, Any]:
        return self._cfg()._AUTO_INSTALL_CONFIG

    @property
    def cache_config(self) -> dict[str, Any]:
        return self._cfg()._CACHE_CONFIG

    @property
    def incremental_index_config(self) -> dict[str, Any]:
        return self._cfg()._INCREMENTAL_INDEX_CONFIG

    @property
    def module_skip_config(self) -> dict[str, Any]:
        return self._cfg()._MODULE_SKIP_CONFIG

    @property
    def preheat_config(self) -> dict[str, Any]:
        return self._cfg()._PREHEAT_CONFIG

    # ── background & tracking ────────────────────────
    @property
    def background_index_building(self) -> bool:
        return self._cfg()._BACKGROUND_INDEX_BUILDING

    @property
    def background_index_thread(self) -> Optional[Any]:
        return self._cfg()._BACKGROUND_INDEX_THREAD

    @property
    def tracked_packages(self) -> dict[str, dict[str, Any]]:
        return self._cfg()._TRACKED_PACKAGES

    # ── hooks ─────────────────────────────────────────
    @property
    def pre_import_hooks(self) -> list:
        return self._cfg()._PRE_IMPORT_HOOKS

    @property
    def post_import_hooks(self) -> list:
        return self._cfg()._POST_IMPORT_HOOKS

    # ── reserved names ────────────────────────────────
    @property
    def reserved_names(self) -> set[str]:
        return self._cfg()._RESERVED_NAMES

    # ── import context ────────────────────────────────
    @property
    def import_context(self):
        return self._cfg()._IMPORT_CONTEXT

    # ── helpers ────────────────────────────────────────
    def reset_all(self) -> None:
        self._cfg().reset_all()

    def get_init_state(self) -> dict[str, Any]:
        return self._cfg().get_init_state()


appstate = AppState()
