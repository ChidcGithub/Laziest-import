"""
User-level configuration file support (.laziestrc).
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from ._config import _DEBUG_MODE


_LAZIESTRC_PATHS = [
    Path.home() / ".laziestrc",
    Path.home() / ".config" / "laziest-import" / "config.json",
    Path.cwd() / ".laziestrc",
    Path.cwd() / ".laziestrc.json",
]

_CONFIG_CACHE: Optional[Dict[str, Any]] = None


def find_rc_file() -> Optional[Path]:
    """Find the first existing .laziestrc file."""
    for path in _LAZIESTRC_PATHS:
        if path.exists():
            return path
    return None


def load_rc_config(force_reload: bool = False) -> Dict[str, Any]:
    """
    Load configuration from .laziestrc files.

    Looks for config in this order:
    1. ~/.laziestrc
    2. ~/.config/laziest-import/config.json
    3. ./.laziestrc (current directory)
    4. ./.laziestrc.json (current directory)

    Returns:
        Dictionary with configuration values
    """
    global _CONFIG_CACHE

    if _CONFIG_CACHE is not None and not force_reload:
        return _CONFIG_CACHE

    config: Dict[str, Any] = {}

    # Load from environment variables first (highest priority)
    config.update(_load_from_env())

    # Load from files (later files override earlier ones)
    for path in _LAZIESTRC_PATHS:
        if path.exists():
            try:
                file_config = _load_file(path)
                if file_config:
                    _deep_update(config, file_config)
            except Exception as e:
                if _DEBUG_MODE:
                    import logging

                    logging.warning(
                        f"[laziest-import] Failed to load config from {path}: {e}"
                    )

    _CONFIG_CACHE = config
    return config


def _load_file(path: Path) -> Dict[str, Any]:
    """Load config from a single file."""
    try:
        if path.suffix == ".json" or path.name == ".laziestrc":
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except json.JSONDecodeError:
        # Try as JSON lines or simple key=value
        return _load_simple_config(path)
    return {}


def _load_simple_config(path: Path) -> Dict[str, Any]:
    """Load simple config format (key: value lines)."""
    config = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    key, value = line.split(":", 1)
                    config[key.strip()] = _parse_value(value.strip())
    except Exception:
        pass
    return config


def _load_from_env() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    config = {}

    env_prefix = "LAZIEST_"

    for key, value in os.environ.items():
        if key.startswith(env_prefix):
            config_key = key[len(env_prefix) :].lower()
            config[config_key] = _parse_value(value)

    return config


def _parse_value(value: str) -> Any:
    """Parse string value to appropriate type."""
    # Boolean
    if value.lower() in ("true", "yes", "1", "on"):
        return True
    if value.lower() in ("false", "no", "0", "off"):
        return False

    # Number
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        pass

    # JSON-like list/dict
    if value.startswith("[") and value.endswith("]"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass

    if value.startswith("{") and value.endswith("}"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass

    # String
    return value


def _deep_update(base: Dict, update: Dict) -> None:
    """Deep update base dict with update dict."""
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_update(base[key], value)
        else:
            base[key] = value


def get_rc_value(key: str, default: Any = None) -> Any:
    """Get a specific config value."""
    config = load_rc_config()
    keys = key.split(".")

    value = config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default

    return value


def create_rc_file(path: Optional[Union[str, Path]] = None, template: bool = True) -> Path:
    """
    Create a new .laziestrc file.

    Args:
        path: Path to create (defaults to ~/.laziestrc), can be str or Path
        template: If True, creates with default template

    Returns:
        Path to created file
    """
    if path is None:
        path = Path.home() / ".laziestrc"
    elif isinstance(path, str):
        path = Path(path)

    if path.exists():
        raise FileExistsError(f"Config file already exists: {path}")

    if template:
        config = _get_default_config_template()
    else:
        config = {}

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    # Clear cache to reload
    global _CONFIG_CACHE
    _CONFIG_CACHE = None

    return path


def _get_default_config_template() -> Dict[str, Any]:
    """Get default configuration template."""
    return {
        "aliases": {
            "np": "numpy",
            "pd": "pandas",
            "plt": "matplotlib.pyplot",
            "tf": "tensorflow",
            "torch": "torch",
        },
        "symbol_search": {
            "enabled": True,
            "max_results": 5,
            "interactive": False,
        },
        "auto_install": {
            "enabled": False,
            "interactive": True,
        },
        "cache": {
            "enable_compression": False,
            "max_size_mb": 100,
        },
        "debug": False,
    }


def save_rc_config(config: Dict[str, Any], path: Optional[Path] = None) -> Path:
    """
    Save configuration to .laziestrc file.

    Args:
        config: Configuration dictionary to save
        path: Path to save to (defaults to ~/.laziestrc)

    Returns:
        Path to saved file
    """
    if path is None:
        path = Path.home() / ".laziestrc"

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    # Update cache
    global _CONFIG_CACHE
    _CONFIG_CACHE = config

    return path


def list_rc_paths() -> List[Path]:
    """List all possible .laziestrc file paths."""
    return list(_LAZIESTRC_PATHS)


def reload_rc_config() -> Dict[str, Any]:
    """Force reload configuration from files."""
    return load_rc_config(force_reload=True)


def get_rc_info() -> Dict[str, Any]:
    """Get information about RC configuration."""
    return {
        "paths_checked": [str(p) for p in _LAZIESTRC_PATHS],
        "active_path": str(find_rc_file()) if find_rc_file() else None,
        "loaded": _CONFIG_CACHE is not None,
        "config": load_rc_config() if _CONFIG_CACHE is None else _CONFIG_CACHE,
    }
