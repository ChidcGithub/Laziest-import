from dataclasses import asdict
from typing import Any, Dict, List, Optional

from .. import _config
from .._install import (
    install_package,
    enable_auto_install,
    disable_auto_install,
    is_auto_install_enabled,
    get_auto_install_config,
    rebuild_module_cache,
)


class InstallNamespace:
    def package(
        self,
        package_name: str,
        index: Optional[str] = None,
        extra_args: Optional[List[str]] = None,
        interactive: Optional[bool] = None,
    ) -> bool:
        return install_package(
            package_name, index=index, extra_args=extra_args,
            interactive=interactive,
        )

    @property
    def auto(self) -> Any:
        return get_auto_install_config()

    @auto.setter
    def auto(self, cfg: Any) -> None:
        _config._AUTO_INSTALL_CONFIG.update(asdict(cfg))

    def enable(
        self,
        interactive: bool = True,
        index: Optional[str] = None,
        extra_args: Optional[List[str]] = None,
        prefer_uv: bool = False,
        silent: bool = False,
    ) -> None:
        enable_auto_install(interactive, index, extra_args, prefer_uv, silent)

    def disable(self) -> None:
        disable_auto_install()

    @property
    def enabled(self) -> bool:
        return is_auto_install_enabled()

    def rebuild_cache(self) -> None:
        rebuild_module_cache()

    def __repr__(self) -> str:
        return f"<InstallNamespace: auto_enabled={is_auto_install_enabled()}>"


class ExportNamespace:
    def aliases(
        self,
        path: Optional[str] = None,
        include_categories: bool = True,
    ) -> str:
        from .._alias import export_aliases
        return export_aliases(path, include_categories)

    def config(self, path: Optional[str] = None) -> str:
        from . import _global_config
        return _global_config.export(path)

    def __repr__(self) -> str:
        return "<ExportNamespace>"
