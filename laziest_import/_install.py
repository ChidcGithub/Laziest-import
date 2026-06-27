"""
Package installation functionality for laziest-import.
"""

import logging
import shutil
import subprocess
import sys
from typing import Any, Optional
from urllib.parse import urlparse

from . import _config
from ._fuzzy import _get_package_rename_map


_ALLOWED_INDEX_SCHEMES = frozenset({"https", "http"})

_BLOCKED_INSTALL_ARGS: frozenset[str] = frozenset({
    "--trusted-host",
    "--find-links",
    "--extra-index-url",
    "--no-index",
    "--require-hashes",
    "--no-build-isolation",
    "--no-clean",
    "--no-deps",
    "--no-verify",
})


def _validate_install_args(package_name: Optional[str], index: Optional[str], extra_args: Optional[list[str]]) -> None:
    if package_name and package_name.startswith(("-", "git+", "http", ".")):
        raise ValueError(f"Dangerous package name blocked: '{package_name}'")
    if index:
        parsed = urlparse(index)
        if parsed.scheme not in _ALLOWED_INDEX_SCHEMES:
            raise ValueError(
                f"Insecure index URL scheme '{parsed.scheme}'. "
                f"Only {_ALLOWED_INDEX_SCHEMES} allowed for auto-install."
            )
    if extra_args:
        for arg in extra_args:
            for blocked in _BLOCKED_INSTALL_ARGS:
                if arg.startswith(blocked):
                    raise ValueError(f"Dangerous install flag blocked: '{arg}'")


def _get_pip_package_name(module_name: str) -> str:
    """Get the pip package name for a module name."""
    rename_map = _get_package_rename_map()

    if module_name in rename_map:
        return rename_map[module_name]

    base_module = module_name.split(".", maxsplit=1)[0]
    if base_module in rename_map:
        return rename_map[base_module]

    return base_module


def _check_uv_available() -> bool:
    """Check if uv is available in the system."""
    return shutil.which("uv") is not None


def _install_package_sync(
    package_name: str,
    index: Optional[str] = None,
    extra_args: Optional[list[str]] = None,
    prefer_uv: bool = False,
    silent: bool = False,
) -> tuple[bool, str]:
    """Install a package using pip or uv."""
    _validate_install_args(package_name, index, extra_args)
    use_uv = prefer_uv and _check_uv_available()

    if use_uv:
        # _check_uv_available() already confirmed uv exists, safe to use directly
        cmd = ["uv", "pip", "install", package_name]
    else:
        cmd = [sys.executable, "-m", "pip", "install", package_name]

    if index:
        cmd.extend(["--index-url", index])

    if extra_args:
        cmd.extend(extra_args)

    if silent:
        cmd.append("-q")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=False)  # noqa: S603 — list form, trusted input

        if result.returncode == 0:
            return True, result.stdout or f"Successfully installed {package_name}"
        else:
            return False, result.stderr or f"Failed to install {package_name}"

    except subprocess.TimeoutExpired:
        return False, f"Installation of {package_name} timed out"
    except FileNotFoundError as e:
        return False, f"Package manager not found: {e}"
    except Exception as e:
        return False, f"Installation failed: {e}"


def _is_interactive_terminal() -> bool:
    """Check if we're running in an interactive terminal."""
    import sys

    if not sys.stdin.isatty():
        return False
    return sys.stdout.isatty()


def _interactive_install_confirm(module_name: str, package_name: str) -> bool:
    """Ask user for confirmation before installing a package.

    In non-interactive environments, returns False for safety.
    """
    if not _config._AUTO_INSTALL_CONFIG["interactive"]:
        if not _config._AUTO_INSTALL_CONFIG["allow_non_interactive"]:
            if _config._DEBUG_MODE:
                logging.debug(
                    f"[laziest-import] Non-interactive auto-install blocked: "
                    f"'{package_name}' requires allow_non_interactive=True"
                )
            return False
        return True

    # Check if we're in an interactive terminal
    if not _is_interactive_terminal():
        if _config._DEBUG_MODE:
            logging.debug(
                f"[laziest-import] Non-interactive environment, "
                f"auto-declining installation of '{package_name}'"
            )
        return False

    print(f"\n[laziest-import] Module '{module_name}' is not installed.")
    print(f"  Package to install: {package_name}")
    print("-" * 50)

    try:
        response = input("Install now? [Y/n]: ").strip().lower()
        return response in ("", "y", "yes")
    except (EOFError, KeyboardInterrupt):
        print("\nInstallation cancelled.")
        return False
    except OSError:
        # OSError can occur in some non-interactive environments
        if _config._DEBUG_MODE:
            logging.debug(
                "[laziest-import] OSError during install confirm, auto-declining installation"
            )
        return False


def install_package(
    package_name: str,
    index: Optional[str] = None,
    extra_args: Optional[list[str]] = None,
    interactive: Optional[bool] = None,
) -> bool:
    """
    Install a package manually.

    Args:
        package_name: Name of the package to install (pip name)
        index: Optional custom PyPI mirror URL
        extra_args: Additional arguments for pip
        interactive: Override interactive setting. None = use config.

    Returns:
        True if installation succeeded
    """
    from ._alias import _build_known_modules_cache

    if index is None:
        index = _config._AUTO_INSTALL_CONFIG["index"]
    if extra_args is None:
        extra_args = _config._AUTO_INSTALL_CONFIG["extra_args"]
    if interactive is None:
        interactive = _config._AUTO_INSTALL_CONFIG["interactive"]

    if interactive and not _interactive_install_confirm(package_name, package_name):
        return False

    success, message = _install_package_sync(
        package_name,
        index=index,
        extra_args=extra_args,
        prefer_uv=_config._AUTO_INSTALL_CONFIG["prefer_uv"],
        silent=_config._AUTO_INSTALL_CONFIG["silent"],
    )

    if success:
        if _config._DEBUG_MODE:
            logging.info(f"[laziest-import] {message}")
        # Rebuild module cache
        _build_known_modules_cache(force=True)
        return True
    else:
        logging.warning(f"[laziest-import] {message}")
        return False


def enable_auto_install(
    interactive: bool = True,
    index: Optional[str] = None,
    extra_args: Optional[list[str]] = None,
    prefer_uv: bool = False,
    silent: bool = False,
    allow_non_interactive: bool = False,
) -> None:
    """
    Enable automatic installation of missing packages.

    WARNING: This feature runs pip/uv install with arbitrary package names.
    Only enable in trusted environments.

    Args:
        interactive: When True, prompt user before installing.
        allow_non_interactive: Must be explicitly set to True when
            interactive=False, as a safety measure against silent installs.
    """
    if not interactive and not allow_non_interactive:
        raise ValueError(
            "Non-interactive auto-install is dangerous: pip/uv will be called "
            "with arbitrary package names. Set allow_non_interactive=True to "
            "acknowledge this risk."
        )
    _validate_install_args(None, index, extra_args)

    _config._AUTO_INSTALL_CONFIG["enabled"] = True
    _config._AUTO_INSTALL_CONFIG["interactive"] = interactive
    _config._AUTO_INSTALL_CONFIG["allow_non_interactive"] = allow_non_interactive
    _config._AUTO_INSTALL_CONFIG["index"] = index
    _config._AUTO_INSTALL_CONFIG["extra_args"] = extra_args or []
    _config._AUTO_INSTALL_CONFIG["prefer_uv"] = prefer_uv
    _config._AUTO_INSTALL_CONFIG["silent"] = silent


def disable_auto_install() -> None:
    """Disable automatic installation of missing packages."""
    _config._AUTO_INSTALL_CONFIG["enabled"] = False


def is_auto_install_enabled() -> bool:
    """Check if automatic installation is enabled."""
    return _config._AUTO_INSTALL_CONFIG["enabled"]


def get_auto_install_config() -> dict[str, Any]:
    """Get current auto-install configuration."""
    return dict(_config._AUTO_INSTALL_CONFIG)


def set_pip_index(url: Optional[str]) -> None:
    """Set custom PyPI mirror index URL."""
    _validate_install_args(None, url, None)
    _config._AUTO_INSTALL_CONFIG["index"] = url


def set_pip_extra_args(args: list[str]) -> None:
    """Set extra arguments for pip install."""
    _validate_install_args(None, None, args)
    _config._AUTO_INSTALL_CONFIG["extra_args"] = args


def rebuild_module_cache() -> None:
    """Rebuild the known modules cache."""
    from ._alias import _build_known_modules_cache

    _build_known_modules_cache(force=True)
