from typing import Any, Dict, Optional

from .. import _config
from .._cache import (
    get_package_version,
    get_all_package_versions,
    get_laziest_import_version,
    get_cache_version,
)


def get_version(alias: str) -> Optional[str]:
    from .._config import _LAZY_MODULES
    if alias in _LAZY_MODULES:
        module = _LAZY_MODULES[alias]._get_module()
        return getattr(module, "__version__", None)
    return None


class VersionNamespace:
    @property
    def current(self) -> str:
        return _config.__version__

    def of(self, package: str) -> Optional[str]:
        return get_package_version(package)

    def all_packages(self) -> Dict[str, str]:
        return get_all_package_versions()

    def laziest_import(self) -> str:
        return get_laziest_import_version()

    def cache(self) -> str:
        return get_cache_version()

    def __str__(self) -> str:
        return self.current

    def __repr__(self) -> str:
        return f"<VersionNamespace: v{self.current}>"
