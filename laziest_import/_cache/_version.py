"""
Version query utilities for laziest-import.
"""

from typing import Dict, Optional
import json

from .._config import get_cache_version as _get_cache_version_from_config


def get_package_version(package_name: str) -> Optional[str]:
    """Get the version of an installed package.
    
    Args:
        package_name: The name of the package (e.g., 'numpy', 'pandas')
        
    Returns:
        Version string if found, None otherwise
        
    Examples:
        >>> get_package_version('numpy')
        '1.24.0'
        >>> get_package_version('nonexistent')
        None
    """
    try:
        from importlib.metadata import version, PackageNotFoundError
        # Normalize package name (handle both my-package and my_package)
        normalized = package_name.lower().replace('_', '-')
        return version(normalized)
    except PackageNotFoundError:
        return None
    except Exception:
        return None


def get_all_package_versions() -> Dict[str, str]:
    """Get versions of all installed packages.
    
    Returns:
        Dictionary mapping package names to their versions
    """
    try:
        from importlib.metadata import distributions
        versions = {}
        for dist in distributions():
            name = dist.metadata.get("Name", "")
            ver = dist.metadata.get("Version", "")
            if name and ver:
                # Use normalized name
                import_name = name.lower().replace("-", "_")
                versions[import_name] = ver
        return versions
    except Exception:
        return {}


def get_laziest_import_version() -> str:
    """Get the version of laziest-import library itself.
    
    Priority:
    1. Read from version.json (most reliable for development)
    2. Fallback to importlib.metadata (for installed package)
    
    Returns:
        Version string
    """
    # First try to read from version.json (same source as __version__)
    try:
        import os
        version_file = os.path.join(os.path.dirname(__file__), '..', 'version.json')
        if os.path.exists(version_file):
            with open(version_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                version = data.get('_current_version')
                if version:
                    return version
    except Exception:
        pass
    
    # Fallback to importlib.metadata for installed package
    try:
        from importlib.metadata import version
        return version('laziest-import')
    except Exception:
        pass
    
    return 'unknown'


def get_cache_version() -> str:
    """Get current cache version."""
    return _get_cache_version_from_config()


__all__ = [
    "get_package_version",
    "get_all_package_versions",
    "get_laziest_import_version",
    "get_cache_version",
]
