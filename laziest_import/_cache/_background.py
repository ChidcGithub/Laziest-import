"""
Background index building for laziest-import.
"""

from typing import Optional, Callable
import time
import logging
import threading

from .._config import (
    _DEBUG_MODE,
    _PREHEAT_CONFIG,
    _INCREMENTAL_INDEX_CONFIG,
    _SYMBOL_INDEX_BUILT,
    _set_background_index_building,
)

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
    from .._config import (
        _BACKGROUND_INDEX_BUILDING,
        _BACKGROUND_INDEX_THREAD,
        _set_background_index_building,
    )
    
    if not _PREHEAT_CONFIG.get("enabled", True):
        return False
    
    if not _PREHEAT_CONFIG.get("async_index_build", True):
        return False
    
    # Thread-safe check and set
    with _BACKGROUND_BUILD_LOCK:
        if _BACKGROUND_INDEX_BUILDING:
            return False
        
        if _SYMBOL_INDEX_BUILT:
            return False
        
        # Set building state before starting thread
        _set_background_index_building(True)
    
    def _background_build_worker():
        from .._symbol import _build_symbol_index
        
        try:
            timeout = _INCREMENTAL_INDEX_CONFIG.get("background_timeout", 60.0)
            _build_symbol_index(force=False, timeout=timeout)
            
            if callback:
                callback()
                
        except Exception as e:
            if _DEBUG_MODE:
                logging.warning(f"[laziest-import] Background index build failed: {e}")
        finally:
            with _BACKGROUND_BUILD_LOCK:
                _set_background_index_building(False)
    
    thread = threading.Thread(target=_background_build_worker, daemon=True)
    thread.start()
    return True


def _is_background_index_building() -> bool:
    """Check if background index build is in progress."""
    from .._config import _BACKGROUND_INDEX_BUILDING
    return _BACKGROUND_INDEX_BUILDING


def _wait_for_background_index(timeout: float = 30.0) -> bool:
    """Wait for background index build to complete.
    
    Args:
        timeout: Maximum time to wait in seconds
        
    Returns:
        True if build completed, False if timeout
    """
    from .._config import _BACKGROUND_INDEX_THREAD
    
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
    from .._config import _PREHEAT_CONFIG
    _PREHEAT_CONFIG["enabled"] = enabled
    _PREHEAT_CONFIG["async_index_build"] = enabled


def get_preheat_config() -> dict:
    """Get background preheat configuration."""
    from .._config import _PREHEAT_CONFIG
    return dict(_PREHEAT_CONFIG)


__all__ = [
    "_BACKGROUND_BUILD_LOCK",
    "_start_background_index_build",
    "_is_background_index_building",
    "_wait_for_background_index",
    "enable_background_build",
    "get_preheat_config",
]
