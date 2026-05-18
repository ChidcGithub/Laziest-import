"""
State setters for laziest-import.

These functions MUST be accessed through laziest_import._config
(not imported directly), because they operate on _config module globals.
"""

import sys
from pathlib import Path
import json
from typing import Dict, Set


def _config():
    """Return the laziest_import._config module at call time."""
    return sys.modules["laziest_import._config"]


def _set_symbol_index_built(value: bool) -> None:
    c = _config(); c._SYMBOL_INDEX_BUILT = value


def _set_stdlib_cache_built(value: bool) -> None:
    c = _config(); c._STDLIB_CACHE_BUILT = value


def _set_third_party_cache_built(value: bool) -> None:
    c = _config(); c._THIRD_PARTY_CACHE_BUILT = value


def _set_background_index_building(value: bool) -> None:
    c = _config(); c._BACKGROUND_INDEX_BUILDING = value


def reset_all() -> None:
    """Reset all state to defaults (useful for testing)."""
    c = _config()

    c._ALIAS_MAP.clear()
    c._LAZY_MODULES.clear()
    c._NEGATIVE_CACHE.clear()
    c._SYMBOL_CACHE.clear()
    c._STDLIB_SYMBOL_CACHE.clear()
    c._THIRD_PARTY_SYMBOL_CACHE.clear()
    c._CONFIRMED_MAPPINGS.clear()
    c._TRACKED_PACKAGES.clear()
    c._PRE_IMPORT_HOOKS.clear()
    c._POST_IMPORT_HOOKS.clear()

    c._SYMBOL_INDEX_BUILT = False
    c._STDLIB_CACHE_BUILT = False
    c._THIRD_PARTY_CACHE_BUILT = False
    c._BACKGROUND_INDEX_BUILDING = False

    if "laziest_import._lazy_index" in sys.modules:
        sys.modules.pop("laziest_import._lazy_index")

    c._IMPORT_STATS.total_imports = 0
    c._IMPORT_STATS.total_time = 0.0
    c._IMPORT_STATS.module_times.clear()
    c._IMPORT_STATS.module_access_counts.clear()

    c._CACHE_STATS["symbol_hits"] = 0
    c._CACHE_STATS["symbol_misses"] = 0
    c._CACHE_STATS["module_hits"] = 0
    c._CACHE_STATS["module_misses"] = 0
    c._CACHE_STATS["last_build_time"] = 0.0
    c._CACHE_STATS["build_count"] = 0


def _load_priorities_from_file() -> Dict[str, int]:
    """Load module priorities from JSON file."""
    priorities_file = Path(__file__).parent / "mappings" / "priorities.json"
    if not priorities_file.exists():
        return {}
    try:
        with open(priorities_file, encoding="utf-8") as f:
            data = json.load(f)
        result: Dict[str, int] = {}
        for key, value in data.items():
            if key.startswith("_"):
                continue
            if isinstance(value, dict):
                result.update(value)
        return result
    except (json.JSONDecodeError, OSError):
        return {}


def get_importing_modules() -> Set[str]:
    """Get the set of modules currently being imported (thread-local)."""
    c = _config()
    ctx = c._IMPORT_CONTEXT
    if not hasattr(ctx, "__importing"):
        with c._IMPORT_CONTEXT_LOCK:
            if not hasattr(ctx, "__importing"):
                ctx.__importing = set()  # type: ignore
    return ctx.__importing  # type: ignore