from typing import Any, Dict, Iterator, List, Optional, Tuple

from .._alias import (
    _ALIAS_MAP,
    register_alias,
    unregister_alias,
    reload_aliases,
    export_aliases,
    validate_aliases,
)
from .._proxy import _get_lazy_module


class AliasNamespace:
    def register(self, alias: str, module_name: str) -> None:
        register_alias(alias, module_name)

    def register_many(self, aliases: Dict[str, str]) -> List[str]:
        registered: List[str] = []
        for alias, mod in aliases.items():
            try:
                register_alias(alias, mod)
                registered.append(alias)
            except ValueError:
                pass
        return registered

    def unregister(self, alias: str) -> bool:
        return unregister_alias(alias)

    def reload(self) -> None:
        reload_aliases()

    def export(
        self,
        path: Optional[str] = None,
        include_categories: bool = True,
    ) -> str:
        return export_aliases(path, include_categories)

    def validate(
        self, aliases: Optional[Dict[str, str]] = None
    ) -> Dict[str, List[str]]:
        return validate_aliases(aliases)

    def import_file(self, path: str) -> int:
        import json
        from pathlib import Path as _Path

        p = _Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Alias file not found: {path}")

        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        flattened: Dict[str, str] = {}
        for k, v in data.items():
            if isinstance(v, dict):
                flattened.update(v)
            elif isinstance(v, str):
                flattened[k] = v

        registered = self.register_many(flattened)
        return len(registered)

    def search(self, pattern: str) -> List[str]:
        pattern_lower = pattern.lower()
        return [
            alias for alias in _ALIAS_MAP
            if pattern_lower in alias.lower()
        ]

    def __setitem__(self, alias: str, module_name: str) -> None:
        register_alias(alias, module_name)

    def __getitem__(self, alias: str) -> Any:
        if alias not in _ALIAS_MAP:
            raise KeyError(f"Alias '{alias}' not found. Register it first.")
        return _get_lazy_module(alias)

    def __delitem__(self, alias: str) -> None:
        if not self.unregister(alias):
            raise KeyError(f"Alias '{alias}' not found")

    def __contains__(self, alias: str) -> bool:
        return alias in _ALIAS_MAP

    def __len__(self) -> int:
        return len(_ALIAS_MAP)

    def __iter__(self) -> Iterator[str]:
        return iter(_ALIAS_MAP)

    def keys(self) -> List[str]:
        return list(_ALIAS_MAP.keys())

    def values(self) -> List[str]:
        return list(_ALIAS_MAP.values())

    def items(self) -> List[Tuple[str, str]]:
        return list(_ALIAS_MAP.items())

    def get(self, alias: str, default: Optional[str] = None) -> Optional[str]:
        return _ALIAS_MAP.get(alias, default)

    def __repr__(self) -> str:
        return f"<AliasNamespace: {len(self)} aliases>"
