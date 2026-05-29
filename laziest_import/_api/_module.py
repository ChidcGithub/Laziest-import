import importlib
from typing import Any, List, Optional

from .._config import _ALIAS_MAP, _LAZY_MODULES
from .._proxy import _get_lazy_module


def list_loaded() -> List[str]:
    return [
        alias
        for alias, lm in _LAZY_MODULES.items()
        if object.__getattribute__(lm, "_cached_module") is not None
    ]


def list_available() -> List[str]:
    return list(_ALIAS_MAP.keys())


def get_module(name: str) -> Optional[Any]:
    if name in _LAZY_MODULES:
        return _LAZY_MODULES[name]._get_module()
    return None


def reload_module(name: str) -> bool:
    if name not in _LAZY_MODULES:
        return False
    lm = _LAZY_MODULES[name]
    cached = object.__getattribute__(lm, "_cached_module")
    if cached is not None:
        try:
            importlib.reload(cached)
            return True
        except Exception:
            return False
    return False


class ModuleNamespace:
    def get(self, name: str) -> Optional[Any]:
        return get_module(name)

    def load(self, name: str) -> Any:
        lm = _get_lazy_module(name)
        return lm._get_module()

    def reload(self, name: str) -> bool:
        return reload_module(name)

    def list_loaded(self) -> List[str]:
        return list_loaded()

    def list_available(self) -> List[str]:
        return list_available()

    def is_loaded(self, name: str) -> bool:
        return name in list_loaded()

    def __getitem__(self, name: str) -> Any:
        mod = get_module(name)
        if mod is None:
            raise KeyError(
                f"Module '{name}' is not loaded. "
                f"Access it via lz.module.load('{name}') or assign first."
            )
        return mod

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return _get_lazy_module(name)._get_module()
        except Exception as e:
            raise AttributeError(f"Cannot load module '{name}': {e}") from e

    def __dir__(self) -> List[str]:
        return sorted(set(self.list_available()))

    def __repr__(self) -> str:
        loaded = self.list_loaded()
        return f"<ModuleNamespace: {len(loaded)}/{len(self.list_available())} loaded>"
