"""
Fuzzy matching and spelling correction for laziest-import.
"""

from typing import Dict, List, Optional, Set, Any, Tuple
from pathlib import Path
import sys
import json
import importlib.util
import logging
import warnings

import threading

from ._config import (
    _DEBUG_MODE,
    _AUTO_SEARCH_ENABLED,
    _ALIAS_MAP,
    _LAZY_MODULES,
    _MODULE_PRIORITY,
    _SYMBOL_PREFERENCES,
    _SYMBOL_RESOLUTION_CONFIG,
    _SYMBOL_SEARCH_CONFIG,
    _SYMBOL_INDEX_BUILT,
    _CLASS_TO_MODULE_CACHE,
    check_version_range,
    get_version_range,
)


# ============== Mapping Cache ==============
_MAPPING_CACHE: Dict[str, Any] = {}
_MAPPINGS_LOADED: bool = False
_MAPPINGS_LOCK = threading.Lock()


def _get_mappings_dir() -> Path:
    """Get the mappings directory path."""
    return Path(__file__).parent / "mappings"


def _load_mapping_file(filename: str) -> Dict[str, Any]:
    """Load a mapping JSON file, removing metadata keys.
    
    Checks version range from version.json for the 'mappings' target.
    """
    mappings_dir = _get_mappings_dir()
    file_path = mappings_dir / filename
    
    if not file_path.exists():
        if _DEBUG_MODE:
            logging.warning(f"[laziest-import] Mapping file not found: {file_path}")
        return {}
    
    # Check version range from version.json (only check once for mappings)
    min_version, max_version = get_version_range("mappings")
    if min_version is not None or max_version is not None:
        is_valid, warning_msg = check_version_range(
            min_version, max_version, file_path="mappings"
        )
        if not is_valid:
            warnings.warn(
                f"[laziest-import] {warning_msg}. Some mapping features may not work correctly.",
                UserWarning,
                stacklevel=3
            )
    
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        
        # Remove metadata keys
        result = {}
        for key, value in data.items():
            if key.startswith("_"):
                continue
            if isinstance(value, dict):
                result.update(value)
            else:
                result[key] = value
        return result
    except (json.JSONDecodeError, OSError) as e:
        if _DEBUG_MODE:
            logging.warning(f"[laziest-import] Failed to load mapping file {filename}: {e}")
        return {}


def _load_all_mappings() -> None:
    """Load all mapping files into cache."""
    global _MAPPING_CACHE, _MAPPINGS_LOADED
    
    # Quick check without lock for performance
    if _MAPPINGS_LOADED:
        return
    
    with _MAPPINGS_LOCK:
        # Double-check after acquiring lock
        if _MAPPINGS_LOADED:
            return
        
        _MAPPING_CACHE = {
            "abbreviations": _load_mapping_file("abbreviations.json"),
            "misspellings": _load_mapping_file("misspellings.json"),
            "submodules": _load_mapping_file("submodules.json"),
            "package_rename": _load_mapping_file("package_rename.json"),
            "symbol_misspellings": _load_mapping_file("symbol_misspellings.json"),
        }
        _MAPPINGS_LOADED = True


def reload_mappings() -> None:
    """Reload all mapping files from disk."""
    global _MAPPING_CACHE, _MAPPINGS_LOADED
    _MAPPINGS_LOADED = False
    _MAPPING_CACHE = {}
    _load_all_mappings()


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def _get_module_abbreviations() -> Dict[str, str]:
    """Get common module abbreviations mapping from file."""
    _load_all_mappings()
    return _MAPPING_CACHE.get("abbreviations", {})


def _get_package_rename_map() -> Dict[str, str]:
    """Get mapping of package import names to pip install names from file."""
    _load_all_mappings()
    return _MAPPING_CACHE.get("package_rename", {})


def _get_common_submodules() -> Dict[str, Tuple[str, str]]:
    """Get common submodule mappings from file."""
    _load_all_mappings()
    submodules = _MAPPING_CACHE.get("submodules", {})
    # Convert lists to tuples
    result: Dict[str, Tuple[str, str]] = {}
    for alias, value in submodules.items():
        if isinstance(value, list) and len(value) == 2:
            result[alias] = (value[0], value[1])
    return result


def _get_common_misspellings() -> Dict[str, str]:
    """Get common misspelling corrections from file."""
    _load_all_mappings()
    return _MAPPING_CACHE.get("misspellings", {})


def _get_common_symbol_misspellings() -> Dict[str, str]:
    """Get common symbol name misspelling corrections from file."""
    _load_all_mappings()
    return _MAPPING_CACHE.get("symbol_misspellings", {})


def _infer_context() -> Set[str]:
    """Infer the current context by examining loaded modules."""
    loaded = set()
    
    # Check already loaded lazy modules
    for alias, lazy_mod in _LAZY_MODULES.items():
        cached = object.__getattribute__(lazy_mod, '_cached_module')
        if cached is not None:
            module_name = object.__getattribute__(lazy_mod, '_module_name')
            base_module = module_name.split('.')[0]
            loaded.add(base_module)
    
    # Check sys.modules for already imported modules
    for mod_name in sys.modules.keys():
        if mod_name and not mod_name.startswith('_'):
            base_module = mod_name.split('.')[0]
            if base_module in _MODULE_PRIORITY or base_module in _ALIAS_MAP.values():
                loaded.add(base_module)
    
    return loaded


def _check_common_suffix_match(name: str, module: str) -> bool:
    """Check if name matches module with common suffix patterns."""
    suffixes = [
        'py', 'python', 'lib', 'library', 'api', 'client', 'sdk',
        'core', 'utils', 'tools', 'helper', 'wrapper', 'handler',
        'db', 'sql', 'io', 'cli', 'gui', 'ui', 'web', 'http',
        'async', 'sync', 'multi', 'base', 'simple', 'easy', 'fast',
        'ml', 'ai', 'dl', 'nn', 'cv', 'nlp', 'data', 'geo', 'sci',
    ]
    
    for suffix in suffixes:
        if module == f"{name}{suffix}" or module == f"{name}_{suffix}":
            return True
        if name == f"{module}{suffix}" or name == f"{module}_{suffix}":
            return True
    
    patterns = [
        lambda n, m: m == n.replace('-', '').replace('_', ''),
        lambda n, m: n == 'pillow' and m == 'pil',
        lambda n, m: n == 'pil' and m == 'pillow',
        lambda n, m: n == 'opencv' and m.startswith('cv'),
        lambda n, m: m == 'opencv' and n.startswith('cv'),
        lambda n, m: 'beautiful' in n and m == 'bs4',
        lambda n, m: n == 'bs4' and 'beautiful' in m,
        lambda n, m: n == 'pytorch' and m == 'torch',
        lambda n, m: m == 'pytorch' and n == 'torch',
        lambda n, m: n == 'tf' and m == 'tensorflow',
        lambda n, m: m == 'tf' and n == 'tensorflow',
        lambda n, m: n.startswith('sk') and m.startswith('scikit'),
        lambda n, m: m.startswith('sk') and n.startswith('scikit'),
    ]
    
    for pattern in patterns:
        try:
            if pattern(name, module):
                return True
        except Exception:
            continue
    
    return False


def _search_module(name: str) -> Optional[str]:
    """
    Search for a matching module name with enhanced fuzzy matching.
    
    Matching priority:
    1. Exact match in known modules
    2. Direct import test
    3. Abbreviation expansion
    4. Submodule mapping
    5. Common misspelling correction
    6. Package rename mapping
    7. Case-insensitive match
    8. Underscore/hyphen variants
    9. Prefix/suffix match
    10. Levenshtein distance fuzzy match
    """
    from ._alias import _build_known_modules_cache
    
    if not _AUTO_SEARCH_ENABLED:
        return None
    
    known_modules = _build_known_modules_cache()
    name_lower = name.lower()
    name_stripped = name_lower.replace('_', '').replace('-', '')
    
    # 1. Exact match
    if name in known_modules:
        return name
    
    # 2. Try direct import
    try:
        spec = importlib.util.find_spec(name)
        if spec is not None:
            return name
    except (ImportError, ModuleNotFoundError, ValueError):
        pass
    
    # 3. Check abbreviations
    abbrev_map = _get_module_abbreviations()
    if name_lower in abbrev_map:
        target = abbrev_map[name_lower]
        if target in known_modules:
            return target
        try:
            spec = importlib.util.find_spec(target)
            if spec is not None:
                return target
        except (ImportError, ModuleNotFoundError, ValueError):
            pass
    
    # 4. Check submodule mappings
    submodule_map = _get_common_submodules()
    if name in submodule_map:
        parent_module, submodule_path = submodule_map[name]
        if parent_module in known_modules:
            return submodule_path
        try:
            spec = importlib.util.find_spec(parent_module)
            if spec is not None:
                return submodule_path
        except (ImportError, ModuleNotFoundError, ValueError):
            pass
    
    # 5. Check common misspellings
    misspellings = _get_common_misspellings()
    if name_lower in misspellings:
        corrected = misspellings[name_lower]
        if corrected in known_modules:
            if _DEBUG_MODE:
                logging.debug(f"[laziest-import] Misspelling corrected: '{name}' -> '{corrected}'")
            return corrected
        try:
            spec = importlib.util.find_spec(corrected)
            if spec is not None:
                return corrected
        except (ImportError, ModuleNotFoundError, ValueError):
            pass
    
    # Collect candidates with priority scores
    candidates: List[Tuple[int, int, str]] = []
    
    for mod_name in known_modules:
        mod_lower = mod_name.lower()
        mod_stripped = mod_lower.replace('_', '').replace('-', '')
        
        # Priority 0: Case-insensitive exact match
        if mod_lower == name_lower:
            candidates.append((0, 0, mod_name))
        # Priority 1: Abbreviation match
        elif mod_lower == name_stripped or mod_stripped == name_lower:
            candidates.append((1, 0, mod_name))
        # Priority 2: Underscore/hyphen variant match
        elif mod_stripped == name_stripped and mod_stripped != mod_lower:
            candidates.append((2, 0, mod_name))
        # Priority 3: Common suffix patterns
        elif _check_common_suffix_match(name_lower, mod_lower):
            candidates.append((3, 0, mod_name))
        # Priority 4: Prefix match
        elif mod_lower.startswith(name_lower) and len(name_lower) >= 3:
            distance = len(mod_lower) - len(name_lower)
            candidates.append((4, distance, mod_name))
        # Priority 5: Suffix match
        elif mod_lower.endswith(name_lower) and len(name_lower) >= 3:
            distance = len(mod_lower) - len(name_lower)
            candidates.append((5, distance, mod_name))
        # Priority 6: Contains match
        elif name_lower in mod_lower and len(name_lower) >= 4:
            distance = mod_lower.index(name_lower)
            candidates.append((6, distance, mod_name))
        # Priority 7: Fuzzy match
        elif len(name_lower) >= 3 and len(mod_lower) >= 3:
            length_ratio = len(name_lower) / len(mod_lower) if len(mod_lower) > 0 else 0
            if 0.5 <= length_ratio <= 2.0:
                distance = _levenshtein_distance(name_lower, mod_lower)
                max_distance = min(3, max(len(name_lower), len(mod_lower)) // 3)
                if distance <= max_distance:
                    candidates.append((7, distance, mod_name))
    
    if candidates:
        candidates.sort(key=lambda x: (x[0], x[1]))
        best = candidates[0]
        
        if _DEBUG_MODE:
            logging.debug(
                f"[laziest-import] Fuzzy match: '{name}' -> '{best[2]}' "
                f"(priority={best[0]}, distance={best[1]})"
            )
        
        return best[2]
    
    return None


def _search_class_in_modules(class_name: str) -> Optional[Tuple[str, Any]]:
    """Search for a class in loaded modules."""
    import importlib
    
    # Check cache
    if class_name in _CLASS_TO_MODULE_CACHE:
        mod_name = _CLASS_TO_MODULE_CACHE[class_name]
        try:
            mod = sys.modules.get(mod_name) or importlib.import_module(mod_name)
            if hasattr(mod, class_name):
                return (mod_name, getattr(mod, class_name))
        except (ImportError, ModuleNotFoundError):
            pass
    
    # Search in loaded modules
    for mod_name, mod in list(sys.modules.items()):
        if mod is None:
            continue
        try:
            obj = getattr(mod, class_name, None)
            if obj is not None and isinstance(obj, type):
                _CLASS_TO_MODULE_CACHE[class_name] = mod_name
                return (mod_name, obj)
        except Exception:
            continue
    
    return None
