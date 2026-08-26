"""
Background index building for laziest-import.

This module and ``_lazy_index.BackgroundIndexBuilder`` are two entry points to
the same capability. State is kept mutually visible here so callers of either
API observe the same "is a build running?" answer and never spawn duplicate
concurrent builds.
"""

import logging
import threading
from typing import Callable, Optional

from .. import _config

# Lock for thread-safe background build state modification
_BACKGROUND_BUILD_LOCK = threading.Lock()

# Set by our worker when it finishes; avoids busy-wait polling in _wait_for_background_index.
_BUILD_DONE_EVENT = threading.Event()
_BUILD_ACTIVE = False


# ============== Background Index Building ==============


def _start_background_index_build(callback: Optional[Callable[[], None]] = None) -> bool:
    """Start background symbol index build.

    Args:
        callback: Optional callback to run after build completes

    Returns:
        True if background build started, False if already running or disabled
    """
    global _BUILD_ACTIVE

    c = _config

    if not c._PREHEAT_CONFIG.get("enabled", True):
        return False

    if not c._PREHEAT_CONFIG.get("async_index_build", True):
        return False

    # Thread-safe check and set; also respect the singleton builder's state
    with _BACKGROUND_BUILD_LOCK:
        if _BUILD_ACTIVE or c._BACKGROUND_INDEX_BUILDING or c._SYMBOL_INDEX_BUILT:
            return False
        if _singleton_builder_is_building():
            return False

        # Set building state before starting thread
        _BUILD_ACTIVE = True
        c._set_background_index_building(True)
        _BUILD_DONE_EVENT.clear()

    def _background_build_worker():
        from .._symbol import _build_symbol_index

        try:
            timeout = c._INCREMENTAL_INDEX_CONFIG.get("background_timeout", 60.0)
            _build_symbol_index(force=False, timeout=timeout)

            if callback:
                callback()

        except Exception as e:
            if c._DEBUG_MODE:
                logging.warning(f"[laziest-import] Background index build failed: {e}")
        finally:
            global _BUILD_ACTIVE
            with _BACKGROUND_BUILD_LOCK:
                _BUILD_ACTIVE = False
                c._set_background_index_building(False)
            _BUILD_DONE_EVENT.set()

    thread = threading.Thread(target=_background_build_worker, daemon=True)
    thread.start()
    return True


def _singleton_builder_is_building() -> bool:
    """Check whether the _lazy_index.BackgroundIndexBuilder singleton is building."""
    try:
        from .._lazy_index import get_background_builder

        return get_background_builder().is_building()
    except Exception:
        return False


def _is_background_index_building() -> bool:
    """Check if background index build is in progress (either mechanism)."""
    if _BUILD_ACTIVE or _config._BACKGROUND_INDEX_BUILDING:
        return True
    return _singleton_builder_is_building()


def _wait_for_background_index(timeout: float = 30.0) -> bool:
    """Wait for background index build to complete.

    Args:
        timeout: Maximum time to wait in seconds

    Returns:
        True if build completed (or none was running), False on timeout
    """
    import time as _time

    deadline = _time.monotonic() + max(0.0, timeout)

    # Wait for our own worker via event (no busy-wait).
    while _BUILD_ACTIVE:
        remaining = deadline - _time.monotonic()
        if remaining <= 0:
            return not _is_background_index_building()
        if _BUILD_DONE_EVENT.wait(timeout=min(remaining, 0.5)):
            break

    # If the singleton builder owns the running build, wait on its event too.
    try:
        from .._lazy_index import get_background_builder

        builder = get_background_builder()
        if builder.is_building():
            remaining = deadline - _time.monotonic()
            if remaining <= 0:
                return False
            return builder.wait_for_completion(timeout=remaining)
    except ImportError:
        pass  # singleton module unavailable (e.g. during early init)
    except Exception as e:
        if _config._DEBUG_MODE:
            logging.debug(f"[laziest-import] Could not query singleton builder: {e}")

    return not _is_background_index_building()


def enable_background_build(enabled: bool = True) -> None:
    """Enable or disable background index building."""
    c = _config
    c._PREHEAT_CONFIG["enabled"] = enabled
    c._PREHEAT_CONFIG["async_index_build"] = enabled


def get_preheat_config() -> dict:
    """Get background preheat configuration."""
    return dict(_config._PREHEAT_CONFIG)


__all__ = [
    "_BACKGROUND_BUILD_LOCK",
    "_is_background_index_building",
    "_start_background_index_build",
    "_wait_for_background_index",
    "enable_background_build",
    "get_preheat_config",
]
