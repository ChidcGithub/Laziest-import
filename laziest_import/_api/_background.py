from typing import Any, Callable, Optional

from .._cache import (
    enable_background_build,
    get_preheat_config,
)


class BackgroundNamespace:
    def start(
        self,
        progress_callback: Optional[Callable[[str, float], None]] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        from .._lazy_index import start_background_index_build

        return start_background_index_build(progress_callback, timeout)

    def stop(self) -> None:
        from .._lazy_index import get_background_builder

        builder = get_background_builder()
        builder.stop()

    @property
    def is_building(self) -> bool:
        from .._lazy_index import is_index_building

        return is_index_building()

    def wait(self, timeout: float = 30.0) -> bool:
        from .._lazy_index import wait_for_index

        return wait_for_index(timeout)

    @property
    def timeout(self) -> float:
        from .._lazy_index import get_background_timeout

        return get_background_timeout()

    @timeout.setter
    def timeout(self, value: float) -> None:
        from .._lazy_index import set_background_timeout

        set_background_timeout(value)

    @property
    def preheat(self) -> dict[str, Any]:
        return get_preheat_config()

    def enable(self, enabled: bool = True) -> None:
        enable_background_build(enabled)

    def __repr__(self) -> str:
        return f"<BackgroundNamespace: building={self.is_building}>"
