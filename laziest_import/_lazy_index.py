"""
Background index building for lazy symbol indexing.
"""

import threading
import time
import logging
from typing import Optional, Callable

from ._config import _DEBUG_MODE, _SYMBOL_INDEX_BUILT, _INCREMENTAL_INDEX_CONFIG


_BACKGROUND_TIMEOUT: float = 60.0


class BackgroundIndexBuilder:
    """Background thread for building symbol index."""

    _instance: Optional["BackgroundIndexBuilder"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "BackgroundIndexBuilder":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._is_building = False
        self._progress_callback: Optional[Callable[[str, float], None]] = None
        self._initialized = True

    def start(
        self,
        build_func: Callable[[], bool],
        timeout: float = 60.0,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> None:
        """Start background index building."""
        if self._is_building:
            return

        if _SYMBOL_INDEX_BUILT:
            return

        self._stop_event.clear()
        self._is_building = True
        self._progress_callback = progress_callback

        self._thread = threading.Thread(
            target=self._build_worker,
            args=(build_func, timeout),
            daemon=True,
            name="laziest-import-index-builder",
        )
        self._thread.start()

        if _DEBUG_MODE:
            logging.info("[laziest-import] Background index building started")

    def _build_worker(self, build_func: Callable[[], bool], timeout: float) -> None:
        """Worker thread for building index."""
        start_time = time.perf_counter()

        try:
            if _DEBUG_MODE:
                logging.info("[laziest-import] Starting index build in background...")

            success = build_func()

            elapsed = time.perf_counter() - start_time

            if success:
                if _DEBUG_MODE:
                    logging.info(
                        f"[laziest-import] Background index build completed in {elapsed:.2f}s"
                    )
            else:
                if _DEBUG_MODE:
                    logging.info(
                        f"[laziest-import] Background index build failed, will retry on demand"
                    )

        except Exception as e:
            if _DEBUG_MODE:
                logging.warning(f"[laziest-import] Background index build error: {e}")
        finally:
            self._is_building = False
            self._stop_event.set()

    def stop(self) -> None:
        """Stop background building."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._is_building = False

    def is_building(self) -> bool:
        """Check if background building is in progress."""
        return self._is_building

    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """Wait for background building to complete."""
        if not self._is_building:
            return True

        return self._stop_event.wait(timeout=timeout)


def _build_index_background() -> bool:
    """Default background build function."""
    from ._symbol import _build_incremental_symbol_index

    try:
        return _build_incremental_symbol_index(timeout=30.0)
    except Exception:
        return False


_background_builder: Optional[BackgroundIndexBuilder] = None


def get_background_builder() -> BackgroundIndexBuilder:
    """Get or create the background builder singleton."""
    global _background_builder
    if _background_builder is None:
        _background_builder = BackgroundIndexBuilder()
    return _background_builder


def start_background_index_build(
    progress_callback: Optional[Callable[[str, float], None]] = None,
    timeout: Optional[float] = None,
) -> None:
    """Start background index building with default settings.

    Args:
        progress_callback: Optional callback(completed: bool, error: str)
        timeout: Optional timeout override (uses set value if not specified)
    """
    builder = get_background_builder()
    effective_timeout = timeout if timeout is not None else _BACKGROUND_TIMEOUT
    builder.start(
        _build_index_background,
        timeout=effective_timeout,
        progress_callback=progress_callback,
    )


def is_index_building() -> bool:
    """Check if index is currently being built in background."""
    builder = get_background_builder()
    return builder.is_building()


def wait_for_index(timeout: Optional[float] = None) -> bool:
    """Wait for background index build to complete."""
    builder = get_background_builder()
    return builder.wait_for_completion(timeout=timeout)


def set_background_timeout(timeout: float) -> None:
    """Set timeout for background index building.

    Args:
        timeout: Timeout in seconds (default: 60.0)
                 Set to 0 to disable timeout (wait indefinitely)

    Example:
        >>> set_background_timeout(120.0)  # 2 minute timeout
        >>> set_background_timeout(0)     # No timeout
    """
    global _BACKGROUND_TIMEOUT
    _BACKGROUND_TIMEOUT = max(0.0, timeout)


def get_background_timeout() -> float:
    """Get current background timeout setting."""
    return _BACKGROUND_TIMEOUT
