"""
Package installation functionality for laziest-import.
"""

from typing import Dict, List, Optional, Any, Tuple
import sys
import logging
import subprocess
import shutil

from ._config import (
    _DEBUG_MODE,
    _AUTO_INSTALL_CONFIG,
)
from ._fuzzy import _get_package_rename_map


def _get_pip_package_name(module_name: str) -> str:
    """Get the pip package name for a module name."""
    rename_map = _get_package_rename_map()
    
    if module_name in rename_map:
        return rename_map[module_name]
    
    base_module = module_name.split('.')[0]
    if base_module in rename_map:
        return rename_map[base_module]
    
    return base_module


def _check_uv_available() -> bool:
    """Check if uv is available in the system."""
    return shutil.which('uv') is not None


def _install_package_sync(
    package_name: str,
    index: Optional[str] = None,
    extra_args: Optional[List[str]] = None,
    prefer_uv: bool = False,
    silent: bool = False
) -> Tuple[bool, str]:
    """Install a package using pip or uv."""
    use_uv = prefer_uv and _check_uv_available()
    
    if use_uv:
        uv_path = shutil.which('uv')
        if uv_path is None:
            use_uv = False
            cmd = [sys.executable, '-m', 'pip', 'install', package_name]
        else:
            cmd = [uv_path, 'pip', 'install', package_name]
    else:
        cmd = [sys.executable, '-m', 'pip', 'install', package_name]
    
    if index:
        cmd.extend(['--index-url', index])
    
    if extra_args:
        cmd.extend(extra_args)
    
    if silent:
        cmd.append('-q')
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
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
    if not sys.stdout.isatty():
        return False
    return True


def _interactive_install_confirm(module_name: str, package_name: str) -> bool:
    """Ask user for confirmation before installing a package.
    
    In non-interactive environments, returns False for safety.
    """
    if not _AUTO_INSTALL_CONFIG["interactive"]:
        return True
    
    # Check if we're in an interactive terminal
    if not _is_interactive_terminal():
        if _DEBUG_MODE:
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
        return response in ('', 'y', 'yes')
    except (EOFError, KeyboardInterrupt):
        print("\nInstallation cancelled.")
        return False
    except OSError:
        # OSError can occur in some non-interactive environments
        if _DEBUG_MODE:
            logging.debug(
                f"[laziest-import] OSError during install confirm, "
                f"auto-declining installation"
            )
        return False


def install_package(
    package_name: str,
    index: Optional[str] = None,
    extra_args: Optional[List[str]] = None,
    interactive: Optional[bool] = None
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
        index = _AUTO_INSTALL_CONFIG["index"]
    if extra_args is None:
        extra_args = _AUTO_INSTALL_CONFIG["extra_args"]
    if interactive is None:
        interactive = _AUTO_INSTALL_CONFIG["interactive"]
    
    if interactive:
        if not _interactive_install_confirm(package_name, package_name):
            return False
    
    success, message = _install_package_sync(
        package_name,
        index=index,
        extra_args=extra_args,
        prefer_uv=_AUTO_INSTALL_CONFIG["prefer_uv"],
        silent=_AUTO_INSTALL_CONFIG["silent"]
    )
    
    if success:
        if _DEBUG_MODE:
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
    extra_args: Optional[List[str]] = None,
    prefer_uv: bool = False,
    silent: bool = False
) -> None:
    """
    Enable automatic installation of missing packages.
    
    WARNING: This feature installs packages automatically. Use with caution
    in production environments.
    """
    global _AUTO_INSTALL_CONFIG
    
    _AUTO_INSTALL_CONFIG["enabled"] = True
    _AUTO_INSTALL_CONFIG["interactive"] = interactive
    _AUTO_INSTALL_CONFIG["index"] = index
    _AUTO_INSTALL_CONFIG["extra_args"] = extra_args or []
    _AUTO_INSTALL_CONFIG["prefer_uv"] = prefer_uv
    _AUTO_INSTALL_CONFIG["silent"] = silent


def disable_auto_install() -> None:
    """Disable automatic installation of missing packages."""
    _AUTO_INSTALL_CONFIG["enabled"] = False


def is_auto_install_enabled() -> bool:
    """Check if automatic installation is enabled."""
    return _AUTO_INSTALL_CONFIG["enabled"]


def get_auto_install_config() -> Dict[str, Any]:
    """Get current auto-install configuration."""
    return dict(_AUTO_INSTALL_CONFIG)


def set_pip_index(url: Optional[str]) -> None:
    """Set custom PyPI mirror index URL."""
    _AUTO_INSTALL_CONFIG["index"] = url


def set_pip_extra_args(args: List[str]) -> None:
    """Set extra arguments for pip install."""
    _AUTO_INSTALL_CONFIG["extra_args"] = args


def rebuild_module_cache() -> None:
    """Rebuild the known modules cache."""
    from ._alias import _build_known_modules_cache
    _build_known_modules_cache(force=True)
