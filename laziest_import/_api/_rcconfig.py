from pathlib import Path
from typing import Any, Optional

from .._rcconfig import (
    _LAZIESTRC_PATHS,
    create_rc_file,
    find_rc_file,
    get_rc_info,
    get_rc_value,
    load_rc_config,
    reload_rc_config,
    save_rc_config,
)


class RCConfigNamespace:
    def load(self, force_reload: bool = False) -> dict[str, Any]:
        return load_rc_config(force_reload)

    def get(self, key: str, default: Any = None) -> Any:
        return get_rc_value(key, default)

    def create(self, path: Optional[str] = None, template: bool = True) -> Path:
        return create_rc_file(path, template)

    def save(self, config: dict[str, Any], path: Optional[str] = None) -> Path:
        return save_rc_config(config, Path(path) if path else None)

    def paths(self) -> list[str]:
        return [str(p) for p in _LAZIESTRC_PATHS]

    @property
    def paths_list(self) -> list[str]:
        return self.paths()

    def reload(self) -> dict[str, Any]:
        return reload_rc_config()

    def info(self) -> dict[str, Any]:
        return get_rc_info()

    def __repr__(self) -> str:
        active = find_rc_file()
        return f"<RCConfigNamespace: active={active}>"
