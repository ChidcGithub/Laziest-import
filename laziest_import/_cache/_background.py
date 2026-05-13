"""
Background index building for laziest-import.
"""

from typing import Optional, Callable
import time
import logging
import threading

from .. import _config


# Lock for thread-safe background build state modification
_BACKGROUND_BUILD_LOCK = threading.Lock()


# ============== Background Index Building ==============

def _start_background_index_build(callback: Optional[Callable[[], None]] = None) -> bool:
    """Start background symbol index build.

    Args:
        callback: Optional callback to run after build completes

    Returns:
        True if background build started, False if already running or disabled
    """
    c = _config

    if not c._PREHEAT_CONFIG.get("enabled", True):
        return False

    if not c._PREHEAT_CONFIG.get("async_index_build", True):
        return False

    # Thread-safe check and set
    with _BACKGROUND_BUILD_LOCK:
        if c._BACKGROUND_INDEX_BUILDING:
            return False

        if c._SYMBOL_INDEX_BUILT:
            return False

        # Set building state before starting thread
        c._set_background_index_building(True)

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
            with _BACKGROUND_BUILD_LOCK:
                c._set_background_index_building(False)

    thread = threading.Thread(target=_background_build_worker, daemon=True)
    thread.start()
    return True


def _is_background_index_building() -> bool:
    """Check if background index build is in progress."""
    return _config._BACKGROUND_INDEX_BUILDING


def _wait_for_background_index(timeout: float = 30.0) -> bool:
    """Wait for background index build to complete.

    Args:
        timeout: Maximum time to wait in seconds

    Returns:
        True if build completed, False if timeout
    """
    if not _is_background_index_building():
        return True

    start = time.time()
    while time.time() - start < timeout:
        if not _is_background_index_building():
            return True
        time.sleep(0.1)

    return False


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
    "_start_background_index_build",
    "_is_background_index_building",
    "_wait_for_background_index",
    "enable_background_build",
    "get_preheat_config",
]