"""Persistence module for user preferences."""

from typing import Dict
from pathlib import Path
import time
import json
import logging

from .._config import _DEBUG_MODE, _SYMBOL_PREFERENCES


_PREFERENCES_FILE = Path.home() / ".laziest_import" / "preferences.json"


def _ensure_preferences_dir() -> None:
    """Ensure preferences directory exists."""
    _PREFERENCES_FILE.parent.mkdir(parents=True, exist_ok=True)


def save_preferences() -> bool:
    """
    Save current symbol preferences to file.
    
    Returns:
        True if saved successfully
    """
    try:
        _ensure_preferences_dir()
        
        data = {
            "symbol_preferences": dict(_SYMBOL_PREFERENCES),
            "timestamp": time.time(),
            "version": "1.0"
        }
        
        with open(_PREFERENCES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        if _DEBUG_MODE:
            logging.info(f"[laziest-import] Saved preferences to {_PREFERENCES_FILE}")
        
        return True
    except Exception as e:
        if _DEBUG_MODE:
            logging.warning(f"[laziest-import] Failed to save preferences: {e}")
        return False


def load_preferences() -> Dict[str, str]:
    """
    Load symbol preferences from file.
    
    Returns:
        Dictionary of symbol -> module preferences
    """
    try:
        if not _PREFERENCES_FILE.exists():
            return {}
        
        with open(_PREFERENCES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get("symbol_preferences", {})
    except Exception as e:
        if _DEBUG_MODE:
            logging.warning(f"[laziest-import] Failed to load preferences: {e}")
        return {}


def apply_preferences() -> None:
    """Apply loaded preferences to current session."""
    prefs = load_preferences()
    for symbol, module in prefs.items():
        _SYMBOL_PREFERENCES[symbol] = module


def clear_preferences() -> bool:
    """Clear saved preferences."""
    try:
        if _PREFERENCES_FILE.exists():
            _PREFERENCES_FILE.unlink()
        return True
    except Exception:
        return False


def get_preferences_path() -> Path:
    """Get the path to the preferences file."""
    return _PREFERENCES_FILE
