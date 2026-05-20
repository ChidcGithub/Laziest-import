from typing import Any, Dict, Iterator, List, Optional, Tuple

from .._alias import (
    _ALIAS_MAP,
    _ALIAS_META,
    register_alias,
    unregister_alias,
    reload_aliases,
    export_aliases,
    validate_aliases,
    get_alias_category,
    get_alias_meta,
    _build_known_modules_cache,
)
from .._proxy import _get_lazy_module


class AliasNamespace:
    def register(
        self, alias: str, module_name: str, category: Optional[str] = None
    ) -> None:
        register_alias(alias, module_name, category=category)

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
        with_meta: bool = False,
    ) -> str:
        return export_aliases(path, include_categories, with_meta)

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
            if k == '_meta':
                continue
            if isinstance(v, dict):
                flattened.update(v)
            elif isinstance(v, str):
                flattened[k] = v

        registered = self.register_many(flattened)
        return len(registered)

    def search(
        self, pattern: str, by_module: bool = False
    ) -> List[str]:
        if not pattern:
            return []
        pattern_lower = pattern.lower()
        results: List[str] = []
        for alias, module in _ALIAS_MAP.items():
            if pattern_lower in alias.lower():
                results.append(alias)
            elif by_module and pattern_lower in module.lower():
                results.append(alias)
        return results

    def list(
        self, category: Optional[str] = None
    ) -> List[str]:
        if category is None:
            return sorted(_ALIAS_MAP.keys())

        category_lower = category.lower()
        result: List[str] = []
        for alias in _ALIAS_MAP:
            cat = get_alias_category(alias)
            if cat is not None and cat.lower() == category_lower:
                result.append(alias)

        if not result:
            compat_map = {
                "ml": ["machine_learning", "deep_learning", "tensorflow_keras"],
                "ds": ["data_science"],
                "data-science": ["data_science"],
                "data_science": ["data_science"],
                "web": ["web_frameworks", "web_scraping_http"],
                "db": ["database"],
                "database": ["database"],
                "nlp": ["nlp"],
                "viz": ["visualization"],
                "vis": ["visualization"],
                "test": ["testing"],
                "gui": ["gui"],
                "cli": ["cli"],
                "security": ["security_crypto"],
                "crypto": ["security_crypto"],
                "async": ["async_concurrency"],
                "cloud": ["cloud_services"],
                "image": ["image_processing"],
                "img": ["image_processing"],
            }
            if category_lower in compat_map:
                for compat_cat in compat_map[category_lower]:
                    for alias in _ALIAS_MAP:
                        cat = get_alias_category(alias)
                        if cat is not None and cat.lower() == compat_cat.lower():
                            if alias not in result:
                                result.append(alias)

        return sorted(result)

    def suggest(
        self,
        package: Optional[str] = None,
        installed: bool = False,
        pattern: Optional[str] = None,
    ) -> List[str]:
        if package is not None:
            return self._suggest_for_package(package)
        if installed:
            return self._suggest_installed()
        if pattern is not None:
            return self._suggest_by_pattern(pattern)
        return sorted(_ALIAS_MAP.keys())

    def _suggest_for_package(self, package: str) -> List[str]:
        pkg_lower = package.lower()
        seen: Dict[str, int] = {}

        for alias, module in _ALIAS_MAP.items():
            mod_base = module.split(".")[0].lower()
            alias_lower = alias.lower()

            if alias in seen:
                continue

            priority = None
            if mod_base == pkg_lower:
                priority = 0
            elif alias_lower == pkg_lower:
                priority = 1
            elif pkg_lower in mod_base or mod_base in pkg_lower:
                priority = 2

            if priority is not None and alias not in seen:
                seen[alias] = priority

        return sorted(seen.keys(), key=lambda a: seen[a])

    def _suggest_installed(self) -> List[str]:
        known = _build_known_modules_cache()
        suggestions: List[str] = []

        for alias, module in _ALIAS_MAP.items():
            mod_base = module.split(".")[0]
            if mod_base in known:
                suggestions.append(alias)

        return sorted(suggestions)

    def _suggest_by_pattern(self, pattern: str) -> List[str]:
        pat_lower = pattern.lower()
        results: List[str] = []
        for alias, module in _ALIAS_MAP.items():
            if pat_lower in alias.lower() or pat_lower in module.lower():
                results.append(alias)
        return sorted(results)

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

    def get(
        self, alias: str, default: Optional[str] = None
    ) -> Optional[str]:
        return _ALIAS_MAP.get(alias, default)

    def __repr__(self) -> str:
        return f"<AliasNamespace: {len(self)} aliases>"
