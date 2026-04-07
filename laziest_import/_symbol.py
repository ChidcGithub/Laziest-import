"""
Symbol search system for laziest-import.
"""

from typing import Dict, List, Optional, Set, Any, Tuple
import sys
import inspect
import importlib
import pkgutil
import time
import logging
import warnings
import threading

from ._config import (
    _DEBUG_MODE,
    is_initialized,
    _SYMBOL_SEARCH_CONFIG,
    _SYMBOL_CACHE,
    _STDLIB_SYMBOL_CACHE,
    _THIRD_PARTY_SYMBOL_CACHE,
    _SYMBOL_INDEX_BUILT,
    _STDLIB_CACHE_BUILT,
    _THIRD_PARTY_CACHE_BUILT,
    _CONFIRMED_MAPPINGS,
    _MODULE_PRIORITY,
    _SYMBOL_PREFERENCES,
    _SYMBOL_RESOLUTION_CONFIG,
    _CACHE_STATS,
    _TRACKED_PACKAGES,
    _CACHE_CONFIG,
    _INCREMENTAL_INDEX_CONFIG,
    _MODULE_SKIP_CONFIG,
    SearchResult,
    SymbolMatch,
    # Setter functions for state modification
    _set_symbol_index_built,
    _set_stdlib_cache_built,
    _set_third_party_cache_built,
)
from ._cache import (
    _load_symbol_index,
    _save_symbol_index,
    _load_tracked_packages,
    _save_tracked_packages,
    _track_package,
    _get_symbol_index_path,
)
from ._fuzzy import (
    _levenshtein_distance,
    _get_common_symbol_misspellings,
    _infer_context,
)
from ._alias import _build_known_modules_cache


def _get_signature_hint(obj: Any) -> Optional[str]:
    """Get a signature hint string for a callable object."""
    try:
        if callable(obj):
            sig = inspect.signature(obj)
            return str(sig)
    except (ValueError, TypeError):
        pass
    return None


def _is_stdlib_module(module_name: str) -> bool:
    """Check if a module is part of the standard library."""
    if hasattr(sys, 'stdlib_module_names'):
        return module_name.split('.')[0] in sys.stdlib_module_names
    
    stdlib_prefixes = {
        'abc', 'argparse', 'array', 'ast', 'asyncio', 'atexit', 'base64',
        'bisect', 'builtins', 'bz2', 'calendar', 'cgi', 'cmath', 'cmd',
        'code', 'codecs', 'collections', 'configparser', 'contextlib',
        'copy', 'csv', 'ctypes', 'dataclasses', 'datetime', 'dbm', 'decimal',
        'difflib', 'dis', 'email', 'enum', 'errno', 'fcntl', 'filecmp',
        'fileinput', 'fnmatch', 'fractions', 'ftplib', 'functools', 'gc',
        'getopt', 'getpass', 'gettext', 'glob', 'gzip', 'hashlib', 'heapq',
        'hmac', 'html', 'http', 'imaplib', 'importlib', 'inspect', 'io',
        'itertools', 'json', 'keyword', 'linecache', 'locale', 'logging',
        'lzma', 'mailbox', 'marshal', 'math', 'mimetypes', 'mmap',
        'multiprocessing', 'netrc', 'numbers', 'operator', 'optparse', 'os',
        'pathlib', 'pickle', 'platform', 'plistlib', 'poplib', 'pprint',
        'profile', 'queue', 'random', 're', 'reprlib', 'sched', 'secrets',
        'select', 'shelve', 'shlex', 'shutil', 'signal', 'site', 'smtplib',
        'socket', 'socketserver', 'sqlite3', 'ssl', 'stat', 'statistics',
        'string', 'struct', 'subprocess', 'sys', 'sysconfig', 'tarfile',
        'tempfile', 'termios', 'textwrap', 'threading', 'time', 'timeit',
        'tkinter', 'token', 'tokenize', 'trace', 'traceback', 'types',
        'typing', 'unicodedata', 'unittest', 'urllib', 'uuid', 'warnings',
        'wave', 'weakref', 'webbrowser', 'wsgiref', 'xml', 'xmlrpc',
        'zipfile', 'zipimport', 'zlib', 'zoneinfo',
    }
    return module_name.split('.')[0] in stdlib_prefixes


# Thread lock for symbol index building
_SYMBOL_INDEX_LOCK = threading.Lock()


def _scan_module_symbols(
    module_name: str,
    depth: int = 1,
    _scanned: Optional[Set[str]] = None,
    _current_depth: int = 0
) -> Dict[str, List[Tuple[str, str, Optional[str]]]]:
    """Scan a module for exported symbols (classes, functions, callables)."""
    if _scanned is None:
        _scanned = set()
    
    MAX_DEPTH = 3
    if _current_depth > MAX_DEPTH:
        return {}
    
    if module_name in _scanned:
        return {}
    _scanned.add(module_name)
    
    symbols: Dict[str, List[Tuple[str, str, Optional[str]]]] = {}
    
    if _SYMBOL_SEARCH_CONFIG["skip_stdlib"] and _is_stdlib_module(module_name):
        return symbols
    
    # Enhanced skip modules using configuration
    skip_modules = {
        'test', 'tests', 'testing', 'conftest', 'setup', 'examples',
        'docs', 'doc', 'scripts', 'tools', 'vendor', 'vendored',
        '__pycache__', '.git', '.hg', '.svn',
        'pytest', 'py.test', 'sphinx', 'mkdocs',
        'laziest_import', 'laziest-import',
    }
    
    # Additional skip patterns from configuration
    if _MODULE_SKIP_CONFIG.get("skip_test_modules", True):
        skip_modules.update(['_test', 'test_', 'tests_', '_tests'])
    
    # Check if module should be skipped
    module_lower = module_name.lower()
    if any(skip in module_lower for skip in skip_modules):
        return symbols
    
    internal_patterns = ['._', '.core.', '.linalg.linalg', '.internal.']
    if any(pattern in module_name for pattern in internal_patterns):
        return symbols
    
    if module_name.endswith('__main__'):
        return symbols
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        warnings.simplefilter("ignore", FutureWarning)
        
        try:
            module = importlib.import_module(module_name)
        except (ImportError, ModuleNotFoundError, SyntaxError, AttributeError,
                TypeError, ValueError, OSError, RecursionError, SystemExit):
            return symbols
        
        skip_private = _SYMBOL_SEARCH_CONFIG["skip_private"]
        
        try:
            public_names = getattr(module, '__all__', None)
            if public_names is None:
                public_names = [name for name in dir(module) if not name.startswith('_')]
            else:
                public_names = [n for n in public_names if isinstance(n, str)]
        except Exception:
            public_names = []
        
        # Check for large modules and optionally skip
        large_threshold = _MODULE_SKIP_CONFIG.get("large_module_threshold", 100)
        if _MODULE_SKIP_CONFIG.get("skip_large_modules", True) and len(public_names) > large_threshold:
            # For large modules, only scan __all__ if defined, otherwise skip most
            if not hasattr(module, '__all__'):
                # Filter to only include likely important symbols
                public_names = [n for n in public_names if not n.startswith('_')][:large_threshold]
        
        MAX_SYMBOLS_PER_MODULE = 100
        if len(public_names) > MAX_SYMBOLS_PER_MODULE:
            public_names = public_names[:MAX_SYMBOLS_PER_MODULE]
        
        for name in public_names:
            if skip_private and name.startswith('_'):
                continue
            
            try:
                obj = getattr(module, name)
            except (AttributeError, ImportError, TypeError, RecursionError):
                continue
            
            symbol_type = None
            signature = None
            
            try:
                if inspect.isclass(obj):
                    symbol_type = 'class'
                    try:
                        init = getattr(obj, '__init__', None)
                        if init and callable(init):
                            signature = _get_signature_hint(init)
                    except Exception:
                        pass
                elif inspect.isfunction(obj):
                    symbol_type = 'function'
                    signature = _get_signature_hint(obj)
                elif callable(obj):
                    symbol_type = 'callable'
                    signature = _get_signature_hint(obj)
            except Exception:
                continue

            if symbol_type:
                if name not in symbols:
                    symbols[name] = []
                symbols[name].append((module_name, symbol_type, signature))
    
    if depth > 0 and hasattr(module, '__path__'):
        try:
            submodule_count = 0
            MAX_SUBMODULES = 20
            for finder, submod_name, ispkg in pkgutil.iter_modules(module.__path__):
                if submodule_count >= MAX_SUBMODULES:
                    break
                full_submod_name = f"{module_name}.{submod_name}"
                try:
                    submod_symbols = _scan_module_symbols(
                        full_submod_name, depth - 1, _scanned, _current_depth + 1
                    )
                    for sym_name, locations in submod_symbols.items():
                        if sym_name not in symbols:
                            symbols[sym_name] = []
                        symbols[sym_name].extend(locations)
                    submodule_count += 1
                except Exception:
                    continue
        except Exception:
            pass
    
    return symbols


def _build_symbol_index(force: bool = False, max_modules: int = 100, timeout: float = 30.0) -> None:
    """Build the symbol index by scanning installed packages."""
    global _SYMBOL_INDEX_BUILT, _SYMBOL_CACHE, _STDLIB_SYMBOL_CACHE, _THIRD_PARTY_SYMBOL_CACHE
    global _STDLIB_CACHE_BUILT, _THIRD_PARTY_CACHE_BUILT, _CACHE_STATS, _TRACKED_PACKAGES
    
    # Skip full build during initialization but allow cache loading
    # Only skip if we're not loading from cache
    if not is_initialized() and not force:
        # Still try to load from cache even during initialization
        pass
    
    # Quick check without lock
    if _SYMBOL_INDEX_BUILT and not force:
        return
    
    if not _SYMBOL_SEARCH_CONFIG["cache_enabled"]:
        return
    
    # Use lock to prevent multiple threads from building simultaneously
    with _SYMBOL_INDEX_LOCK:
        # Double-check after acquiring lock
        if _SYMBOL_INDEX_BUILT and not force:
            return
        
        start_time = time.perf_counter()
        
        # Always load tracked packages for incremental update detection
        existing_tracked = _load_tracked_packages()
        
        # Try to load from cache first (for both force and non-force)
        stdlib_cache = _load_symbol_index("stdlib")
        third_party_cache = _load_symbol_index("third_party")
        
        if not force and (stdlib_cache or third_party_cache):
            # Load from cache
            _TRACKED_PACKAGES.clear()
            _TRACKED_PACKAGES.update(existing_tracked)
            
            if stdlib_cache:
                _STDLIB_SYMBOL_CACHE = {
                    k: [tuple(loc) for loc in v]
                    for k, v in stdlib_cache.symbols.items()
                }
                _STDLIB_CACHE_BUILT = True
                if _DEBUG_MODE:
                    logging.info(
                        f"[laziest-import] Loaded stdlib symbol index: "
                        f"{len(_STDLIB_SYMBOL_CACHE)} symbols"
                    )
            
            if third_party_cache:
                _THIRD_PARTY_SYMBOL_CACHE = {
                    k: [tuple(loc) for loc in v]
                    for k, v in third_party_cache.symbols.items()
                }
                _THIRD_PARTY_CACHE_BUILT = True
                if _DEBUG_MODE:
                    logging.info(
                        f"[laziest-import] Loaded third-party symbol index: "
                        f"{len(_THIRD_PARTY_SYMBOL_CACHE)} symbols"
                    )
            
            if _STDLIB_CACHE_BUILT or _THIRD_PARTY_CACHE_BUILT:
                _SYMBOL_CACHE.clear()
                _SYMBOL_CACHE.update(_STDLIB_SYMBOL_CACHE)
                _SYMBOL_CACHE.update(_THIRD_PARTY_SYMBOL_CACHE)
                
                # Update config module variables
                _set_symbol_index_built(True)
                
                _CACHE_STATS["symbol_hits"] += 1
                elapsed = time.perf_counter() - start_time
                _CACHE_STATS["last_build_time"] = elapsed
                
                if _DEBUG_MODE:
                    logging.info(
                        f"[laziest-import] Symbol index loaded from cache: "
                        f"{len(_SYMBOL_CACHE)} symbols in {elapsed:.3f}s"
                    )
                return
    
    _CACHE_STATS["symbol_misses"] += 1
    
    _SYMBOL_CACHE.clear()
    _STDLIB_SYMBOL_CACHE.clear()
    _THIRD_PARTY_SYMBOL_CACHE.clear()
    depth = _SYMBOL_SEARCH_CONFIG["search_depth"]
    
    known_modules = _build_known_modules_cache()
    
    if _DEBUG_MODE:
        logging.info(f"[laziest-import] Building symbol index for {len(known_modules)} modules...")
    
    priority_packages = {
        'pandas', 'numpy', 'matplotlib', 'seaborn', 'scipy', 'sklearn',
        'torch', 'tensorflow', 'keras', 'xgboost', 'lightgbm',
        'requests', 'flask', 'django', 'fastapi',
        'PIL', 'cv2', 'plotly', 'bokeh',
        'json', 'os', 'sys', 're', 'datetime', 'collections', 'itertools',
        'pathlib', 'typing', 'functools', 'contextlib', 'dataclasses',
    }
    
    sorted_modules = sorted(
        known_modules,
        key=lambda m: (0 if m.split('.')[0] in priority_packages else 1, m)
    )
    
    scanned_stdlib = 0
    scanned_third_party = 0
    timed_out = False
    
    for module_name in sorted_modules:
        if time.perf_counter() - start_time > timeout:
            timed_out = True
            if _DEBUG_MODE:
                logging.info(f"[laziest-import] Symbol index build timed out after {timeout}s")
            break
        
        if scanned_stdlib + scanned_third_party >= max_modules:
            break
            
        if any(x in module_name.lower() for x in ['test', 'tests', '_test', '__pycache__', 'conftest', 'setup']):
            continue
        
        try:
            symbols = _scan_module_symbols(module_name, depth)
            
            is_stdlib = _is_stdlib_module(module_name)
            target_cache = _STDLIB_SYMBOL_CACHE if is_stdlib else _THIRD_PARTY_SYMBOL_CACHE
            
            for sym_name, locations in symbols.items():
                if sym_name not in _SYMBOL_CACHE:
                    _SYMBOL_CACHE[sym_name] = []
                _SYMBOL_CACHE[sym_name].extend(locations)
                
                if sym_name not in target_cache:
                    target_cache[sym_name] = []
                target_cache[sym_name].extend(locations)
            
            if is_stdlib:
                scanned_stdlib += 1
            else:
                scanned_third_party += 1
                top_level = module_name.split('.')[0]
                if top_level not in _TRACKED_PACKAGES:
                    _track_package(top_level)
                    
        except Exception:
            continue
    
    # Update config module variables
    _set_symbol_index_built(True)
    _set_stdlib_cache_built(True)
    _set_third_party_cache_built(True)
    
    _save_symbol_index(_STDLIB_SYMBOL_CACHE, "stdlib", scanned_stdlib)
    _save_symbol_index(_THIRD_PARTY_SYMBOL_CACHE, "third_party", scanned_third_party)
    _save_tracked_packages()
    
    elapsed = time.perf_counter() - start_time
    _CACHE_STATS["last_build_time"] = elapsed
    _CACHE_STATS["build_count"] += 1
    
    if _DEBUG_MODE:
        timeout_msg = " (timed out)" if timed_out else ""
        logging.info(
            f"[laziest-import] Symbol index built: {len(_SYMBOL_CACHE)} symbols "
            f"(stdlib: {scanned_stdlib}, third-party: {scanned_third_party}) "
            f"in {elapsed:.2f}s{timeout_msg}"
        )


def _compare_signatures(sig1: Optional[str], sig2: Optional[str]) -> float:
    """Compare two signature strings and return a similarity score."""
    if sig1 is None or sig2 is None:
        return 0.5
    
    def extract_params(sig: str) -> Set[str]:
        try:
            inner = sig.strip('()')
            if not inner:
                return set()
            params = set()
            for part in inner.split(','):
                part = part.strip()
                if part:
                    param_name = part.split('=')[0].split(':')[0].strip()
                    if param_name and not param_name.startswith('*'):
                        params.add(param_name)
            return params
        except Exception:
            return set()
    
    params1 = extract_params(sig1)
    params2 = extract_params(sig2)
    
    if not params1 or not params2:
        return 0.5
    
    intersection = len(params1 & params2)
    union = len(params1 | params2)
    
    return intersection / union if union > 0 else 0.0


def search_symbol(
    name: str,
    symbol_type: Optional[str] = None,
    signature: Optional[str] = None,
    max_results: Optional[int] = None
) -> List[SearchResult]:
    """Search for a symbol (class/function) by name across installed packages."""
    if not _SYMBOL_SEARCH_CONFIG["enabled"]:
        return []
    
    if not _SYMBOL_INDEX_BUILT:
        _build_symbol_index()
    
    if name not in _SYMBOL_CACHE:
        name_lower = name.lower()
        matches = []
        for cached_name in _SYMBOL_CACHE.keys():
            if cached_name.lower() == name_lower:
                matches.append(cached_name)
            elif name_lower in cached_name.lower():
                matches.append(cached_name)
            elif _levenshtein_distance(name_lower, cached_name.lower()) <= 2:
                matches.append(cached_name)
        
        if not matches:
            return []
        
        all_results = []
        for match_name in matches[:3]:
            all_results.extend(_search_symbol_direct(match_name, symbol_type, signature))
        
        seen = set()
        results = []
        for r in all_results:
            key = (r.module_name, r.symbol_name)
            if key not in seen:
                seen.add(key)
                results.append(r)
        
        max_res = max_results or _SYMBOL_SEARCH_CONFIG["max_results"]
        return sorted(results, key=lambda x: -x.score)[:max_res]
    
    return _search_symbol_direct(name, symbol_type, signature, max_results)


def _search_symbol_direct(
    name: str,
    symbol_type: Optional[str] = None,
    signature: Optional[str] = None,
    max_results: Optional[int] = None
) -> List[SearchResult]:
    """Direct search for an exact symbol name in cache."""
    results = []
    
    if name not in _SYMBOL_CACHE:
        return results
    
    for module_name, sym_type, cached_sig in _SYMBOL_CACHE[name]:
        if symbol_type and sym_type != symbol_type:
            continue
        
        score = 1.0
        
        if _SYMBOL_SEARCH_CONFIG["skip_stdlib"] and _is_stdlib_module(module_name):
            score *= 0.5
        
        if signature and cached_sig:
            sig_score = _compare_signatures(signature, cached_sig)
            if _SYMBOL_SEARCH_CONFIG["exact_params"] and sig_score < 0.9:
                continue
            score *= (0.5 + 0.5 * sig_score)
        
        results.append(SearchResult(
            module_name=module_name,
            symbol_name=name,
            symbol_type=sym_type,
            signature=cached_sig,
            score=score,
        ))
    
    results.sort(key=lambda x: -x.score)
    
    max_res = max_results or _SYMBOL_SEARCH_CONFIG["max_results"]
    return results[:max_res]


def _score_symbol_match(result: SearchResult, context: Set[str], original_name: str) -> SymbolMatch:
    """Score a symbol search result with context awareness and priority."""
    confidence = result.score
    module = result.module_name.split('.')[0]
    source = 'exact'
    
    # 1. User preference (highest priority)
    if result.symbol_name in _SYMBOL_PREFERENCES:
        pref = _SYMBOL_PREFERENCES[result.symbol_name]
        pref_base = pref.split('.')[0]
        if module == pref_base:
            return SymbolMatch(
                module_name=result.module_name,
                symbol_name=result.symbol_name,
                symbol_type=result.symbol_type,
                signature=result.signature,
                confidence=1.0,
                source='user_pref',
                obj=result.obj
            )
        else:
            confidence *= 0.2
            source = 'not_preferred'
    
    # 2. Context awareness
    if _SYMBOL_RESOLUTION_CONFIG["context_aware"] and module in context:
        confidence *= 1.5
        source = 'context'
    
    # 3. Module priority
    priority = _MODULE_PRIORITY.get(module, 50)
    confidence *= (priority / 100)
    
    # 4. Exact match vs fuzzy match
    if result.symbol_name != original_name:
        distance = _levenshtein_distance(original_name.lower(), result.symbol_name.lower())
        max_dist = max(len(original_name), len(result.symbol_name)) // 3
        fuzzy_penalty = distance / max(max_dist, 1)
        confidence *= (1 - fuzzy_penalty * 0.3)
        source = 'fuzzy'
    
    # 5. Penalize stdlib
    if _SYMBOL_SEARCH_CONFIG.get("skip_stdlib") and _is_stdlib_module(result.module_name):
        confidence *= 0.5
    
    confidence = min(confidence, 1.0)
    
    return SymbolMatch(
        module_name=result.module_name,
        symbol_name=result.symbol_name,
        symbol_type=result.symbol_type,
        signature=result.signature,
        confidence=confidence,
        source=source,
        obj=result.obj
    )


def _search_symbol_enhanced(
    name: str,
    auto: bool = True,
    symbol_type: Optional[str] = None
) -> Optional[SymbolMatch]:
    """Enhanced symbol search with conflict resolution and spell correction."""
    if not _SYMBOL_RESOLUTION_CONFIG["auto_symbol"]:
        return None
    
    if not _SYMBOL_INDEX_BUILT:
        _build_symbol_index()
    
    original_name = name
    
    # 1. Check symbol misspellings first
    corrected_name = None
    if _SYMBOL_RESOLUTION_CONFIG["symbol_misspelling"]:
        misspellings = _get_common_symbol_misspellings()
        name_lower = name.lower()
        if name_lower in misspellings:
            corrected_name = misspellings[name_lower]
            if _DEBUG_MODE:
                logging.debug(
                    f"[laziest-import] Symbol misspelling corrected: '{name}' -> '{corrected_name}'"
                )
    
    search_name = corrected_name or name
    
    # 2. Search for the symbol
    results = search_symbol(search_name, symbol_type=symbol_type)
    
    # 3. If no exact match, try fuzzy search
    if not results and not corrected_name:
        name_lower = search_name.lower()
        fuzzy_matches: List[Tuple[int, str]] = []
        
        for cached_name in _SYMBOL_CACHE.keys():
            dist = _levenshtein_distance(name_lower, cached_name.lower())
            max_dist = min(3, max(len(name_lower), len(cached_name)) // 3)
            if dist <= max_dist:
                fuzzy_matches.append((dist, cached_name))
        
        fuzzy_matches.sort(key=lambda x: x[0])
        for dist, match_name in fuzzy_matches[:3]:
            match_results = search_symbol(match_name, symbol_type=symbol_type)
            results.extend(match_results)
        
        if results and _DEBUG_MODE:
            logging.debug(
                f"[laziest-import] Fuzzy symbol search found {len(results)} results for '{name}'"
            )
    
    if not results:
        return None
    
    # 4. Score all results
    context = _infer_context()
    scored_results = [_score_symbol_match(r, context, original_name) for r in results]
    
    scored_results.sort(key=lambda x: -x.confidence)
    
    best = scored_results[0]
    second = scored_results[1] if len(scored_results) > 1 else None
    
    # 5. Determine if we should auto-select
    if not auto:
        return best
    
    threshold = _SYMBOL_RESOLUTION_CONFIG["auto_threshold"]
    conflict_threshold = _SYMBOL_RESOLUTION_CONFIG["conflict_threshold"]
    
    if best.confidence >= threshold:
        if second and (best.confidence - second.confidence) < conflict_threshold:
            if _SYMBOL_RESOLUTION_CONFIG["warn_on_conflict"]:
                _warn_symbol_conflict(original_name, scored_results[:3])
            if best.source in ('user_pref', 'context'):
                return best
            return None
        return best
    
    if _SYMBOL_RESOLUTION_CONFIG["warn_on_conflict"]:
        _warn_symbol_conflict(original_name, scored_results[:3])
    
    return None


def _warn_symbol_conflict(name: str, matches: List[SymbolMatch]) -> None:
    """Warn about symbol conflict and suggest disambiguation."""
    if not matches:
        return
    
    suggestions = ", ".join(
        f"{m.module_name}.{m.symbol_name}({m.confidence:.0%})"
        for m in matches[:3]
    )
    
    examples = []
    for m in matches[:2]:
        module_alias = m.module_name.split('.')[0]
        examples.append(f"{module_alias}.{m.symbol_name}")
    
    example_str = " or ".join(examples) if examples else ""
    
    warnings.warn(
        f"[laziest-import] Symbol '{name}' found in multiple modules: {suggestions}. "
        f"Use module prefix to disambiguate, e.g., {example_str}. "
        f"Or set a preference: set_symbol_preference('{name}', '{matches[0].module_name}')",
        UserWarning,
        stacklevel=4
    )


def _is_interactive_terminal() -> bool:
    """Check if we're running in an interactive terminal."""
    import sys
    # Check if stdin is a tty (interactive terminal)
    if not sys.stdin.isatty():
        return False
    # Check if stdout is a tty
    if not sys.stdout.isatty():
        return False
    # Check if we're in a Jupyter notebook or IPython
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            # In IPython/Jupyter, input() may not work properly
            # but we can still try if it's a terminal
            return sys.stdin.isatty()
    except ImportError:
        pass
    return True


def _interactive_confirm(results: List[SearchResult], symbol_name: str) -> Optional[str]:
    """Interactively ask user to confirm which module to use.
    
    Returns None if:
    - No results
    - User cancels
    - Not in interactive environment and interactive mode is on
    """
    if not results:
        return None
    
    if not _SYMBOL_SEARCH_CONFIG["interactive"]:
        return results[0].module_name
    
    # Check if we're in an interactive terminal
    if not _is_interactive_terminal():
        # Not interactive, auto-select first result with a warning
        if _DEBUG_MODE:
            logging.debug(
                f"[laziest-import] Non-interactive environment, auto-selecting "
                f"'{results[0].module_name}' for symbol '{symbol_name}'"
            )
        return results[0].module_name
    
    print(f"\n[laziest-import] Found {len(results)} match(es) for '{symbol_name}':")
    print("-" * 60)
    
    for i, r in enumerate(results, 1):
        sig_str = f" {r.signature}" if r.signature else ""
        type_str = f"[{r.symbol_type}]"
        print(f"  {i}. {r.module_name}.{r.symbol_name} {type_str}{sig_str}")
    
    print(f"  0. Skip (do not register)")
    print("-" * 60)
    
    try:
        choice = input(f"Select [1-{len(results)}, 0 to skip] (default=1): ").strip()
        
        if not choice:
            choice = "1"
        
        if choice == "0":
            return None
        
        idx = int(choice) - 1
        if 0 <= idx < len(results):
            return results[idx].module_name
        
        print(f"Invalid choice: {choice}")
        return None
    except (ValueError, EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return None
    except OSError:
        # OSError can occur in some non-interactive environments
        if _DEBUG_MODE:
            logging.debug(
                f"[laziest-import] OSError during interactive confirm, "
                f"auto-selecting '{results[0].module_name}'"
            )
        return results[0].module_name


def _handle_symbol_not_found(name: str) -> Optional[str]:
    """Handle a symbol not found error by searching and prompting user."""
    from ._alias import register_alias
    
    if not is_initialized():
        return None
    
    if name in _CONFIRMED_MAPPINGS:
        return _CONFIRMED_MAPPINGS[name]
    
    results = search_symbol(name)
    
    if not results:
        return None
    
    selected_module = _interactive_confirm(results, name)
    
    if selected_module:
        _CONFIRMED_MAPPINGS[name] = selected_module
        register_alias(name, selected_module)
        print(f"[laziest-import] Registered alias: {name} -> {selected_module}")
        return selected_module
    
    return None


# ============== Symbol Search API ==============

def enable_symbol_search(
    interactive: bool = True,
    exact_params: bool = False,
    max_results: int = 5,
    search_depth: int = 1,
    skip_stdlib: bool = False
) -> None:
    """Enable symbol search functionality."""
    _SYMBOL_SEARCH_CONFIG["enabled"] = True
    _SYMBOL_SEARCH_CONFIG["interactive"] = interactive
    _SYMBOL_SEARCH_CONFIG["exact_params"] = exact_params
    _SYMBOL_SEARCH_CONFIG["max_results"] = max_results
    _SYMBOL_SEARCH_CONFIG["search_depth"] = search_depth
    _SYMBOL_SEARCH_CONFIG["skip_stdlib"] = skip_stdlib


def disable_symbol_search() -> None:
    """Disable symbol search functionality."""
    _SYMBOL_SEARCH_CONFIG["enabled"] = False


def is_symbol_search_enabled() -> bool:
    """Check if symbol search is enabled."""
    return _SYMBOL_SEARCH_CONFIG["enabled"]


def rebuild_symbol_index() -> None:
    """Rebuild the symbol index."""
    _SYMBOL_CACHE.clear()
    _STDLIB_SYMBOL_CACHE.clear()
    _THIRD_PARTY_SYMBOL_CACHE.clear()
    _set_symbol_index_built(False)
    _set_stdlib_cache_built(False)
    _set_third_party_cache_built(False)
    
    for cache_type in ["stdlib", "third_party", "all"]:
        cache_path = _get_symbol_index_path(cache_type)
        if cache_path.exists():
            cache_path.unlink()
    
    _build_symbol_index(force=True)


def get_symbol_search_config() -> Dict[str, Any]:
    """Get current symbol search configuration."""
    return dict(_SYMBOL_SEARCH_CONFIG)


def get_symbol_cache_info() -> Dict[str, Any]:
    """Get information about the symbol cache."""
    from ._cache import clear_symbol_cache
    import laziest_import._config as config
    
    return {
        "built": config._SYMBOL_INDEX_BUILT,
        "symbol_count": len(_SYMBOL_CACHE),
        "stdlib_symbols": len(_STDLIB_SYMBOL_CACHE),
        "third_party_symbols": len(_THIRD_PARTY_SYMBOL_CACHE),
        "stdlib_built": config._STDLIB_CACHE_BUILT,
        "third_party_built": config._THIRD_PARTY_CACHE_BUILT,
        "confirmed_mappings": len(_CONFIRMED_MAPPINGS),
        "tracked_packages": len(_TRACKED_PACKAGES),
        "cache_stats": dict(_CACHE_STATS),
        "cache_config": dict(_CACHE_CONFIG),
    }


# ============== Symbol Resolution API ==============

def set_symbol_preference(symbol: str, module: str) -> None:
    """Set a preference for symbol resolution."""
    _SYMBOL_PREFERENCES[symbol] = module
    if _DEBUG_MODE:
        logging.debug(f"[laziest-import] Set symbol preference: {symbol} -> {module}")


def get_symbol_preference(symbol: str) -> Optional[str]:
    """Get the preferred module for a symbol."""
    return _SYMBOL_PREFERENCES.get(symbol)


def clear_symbol_preference(symbol: str) -> bool:
    """Clear a symbol preference."""
    if symbol in _SYMBOL_PREFERENCES:
        del _SYMBOL_PREFERENCES[symbol]
        return True
    return False


def list_symbol_conflicts(symbol: str) -> List[Dict[str, Any]]:
    """List all modules that export a symbol."""
    if not _SYMBOL_INDEX_BUILT:
        _build_symbol_index()
    
    if symbol not in _SYMBOL_CACHE:
        return []
    
    return [
        {
            "module": loc[0],
            "type": loc[1],
            "signature": loc[2],
            "priority": _MODULE_PRIORITY.get(loc[0].split('.')[0], 50),
        }
        for loc in _SYMBOL_CACHE[symbol]
    ]


def set_module_priority(module: str, priority: int) -> None:
    """Set priority for a module (higher = more preferred)."""
    _MODULE_PRIORITY[module] = priority


def get_module_priority(module: str) -> int:
    """Get the priority for a module."""
    return _MODULE_PRIORITY.get(module, 50)


def enable_auto_symbol_resolution(
    auto_threshold: float = 0.7,
    conflict_threshold: float = 0.3,
    warn_on_conflict: bool = True
) -> None:
    """Enable automatic symbol resolution."""
    _SYMBOL_RESOLUTION_CONFIG["auto_symbol"] = True
    _SYMBOL_RESOLUTION_CONFIG["auto_threshold"] = auto_threshold
    _SYMBOL_RESOLUTION_CONFIG["conflict_threshold"] = conflict_threshold
    _SYMBOL_RESOLUTION_CONFIG["warn_on_conflict"] = warn_on_conflict


def disable_auto_symbol_resolution() -> None:
    """Disable automatic symbol resolution."""
    _SYMBOL_RESOLUTION_CONFIG["auto_symbol"] = False


def get_symbol_resolution_config() -> Dict[str, Any]:
    """Get symbol resolution configuration."""
    return dict(_SYMBOL_RESOLUTION_CONFIG)


def get_loaded_modules_context() -> Set[str]:
    """Get the set of currently loaded module names."""
    return _infer_context()


# ============== Incremental Index Build ==============

def _build_incremental_symbol_index(timeout: float = 30.0) -> bool:
    """Build symbol index incrementally, only scanning changed packages.
    
    This function is optimized for scenarios where most packages haven't changed.
    It detects which packages are new or updated and only scans those.
    
    Args:
        timeout: Maximum time to spend on incremental build
        
    Returns:
        True if incremental build was successful, False if full rebuild needed
    """
    global _SYMBOL_INDEX_BUILT, _SYMBOL_CACHE, _TRACKED_PACKAGES
    
    if not _INCREMENTAL_INDEX_CONFIG.get("enabled", True):
        return False
    
    # Load existing tracked packages first
    existing_tracked = _load_tracked_packages()
    if existing_tracked:
        _TRACKED_PACKAGES.clear()
        _TRACKED_PACKAGES.update(existing_tracked)
    
    # Check if we have existing cache
    if not _TRACKED_PACKAGES:
        if _DEBUG_MODE:
            logging.info("[laziest-import] No existing cache, need full rebuild")
        return False
    
    from ._cache import (
        _get_incremental_update_modules,
        _detect_changed_packages,
    )
    
    # Detect changes
    new_packages, updated_packages, removed_packages = _detect_changed_packages()
    
    if not new_packages and not updated_packages and not removed_packages:
        if _DEBUG_MODE:
            logging.info("[laziest-import] No package changes detected, skip incremental build")
        return True
    
    if _DEBUG_MODE:
        logging.info(
            f"[laziest-import] Incremental update: "
            f"{len(new_packages)} new, {len(updated_packages)} updated, {len(removed_packages)} removed"
        )
    
    # Check if too many changes
    total_changes = len(new_packages) + len(updated_packages) + len(removed_packages)
    if total_changes > len(_TRACKED_PACKAGES) * 0.5:  # More than 50% changed
        if _DEBUG_MODE:
            logging.info("[laziest-import] Too many changes, full rebuild recommended")
        return False
    
    start_time = time.perf_counter()
    depth = _SYMBOL_SEARCH_CONFIG["search_depth"]
    scanned_count = 0
    
    # Remove symbols from removed/updated packages
    packages_to_remove = removed_packages | updated_packages
    for pkg in packages_to_remove:
        _remove_package_symbols(pkg)
    
    # Scan new and updated packages
    packages_to_scan = new_packages | updated_packages
    known_modules = _build_known_modules_cache()
    
    for module_name in known_modules:
        if time.perf_counter() - start_time > timeout:
            if _DEBUG_MODE:
                logging.info(f"[laziest-import] Incremental build timed out after {timeout}s")
            break
        
        top_level = module_name.split('.')[0]
        if top_level not in packages_to_scan:
            continue
        
        try:
            symbols = _scan_module_symbols(module_name, depth)
            
            is_stdlib = _is_stdlib_module(module_name)
            target_cache = _STDLIB_SYMBOL_CACHE if is_stdlib else _THIRD_PARTY_SYMBOL_CACHE
            
            for sym_name, locations in symbols.items():
                if sym_name not in _SYMBOL_CACHE:
                    _SYMBOL_CACHE[sym_name] = []
                _SYMBOL_CACHE[sym_name].extend(locations)
                
                if sym_name not in target_cache:
                    target_cache[sym_name] = []
                target_cache[sym_name].extend(locations)
            
            scanned_count += 1
            
        except Exception:
            continue
    
    # Update tracked packages
    from ._cache import _track_package, _save_tracked_packages, _save_symbol_index
    for pkg in packages_to_scan:
        _track_package(pkg)
    _save_tracked_packages()
    _save_symbol_index(_STDLIB_SYMBOL_CACHE, "stdlib")
    _save_symbol_index(_THIRD_PARTY_SYMBOL_CACHE, "third_party")
    
    elapsed = time.perf_counter() - start_time
    _CACHE_STATS["last_build_time"] = elapsed
    _CACHE_STATS["build_count"] += 1
    
    if _DEBUG_MODE:
        logging.info(
            f"[laziest-import] Incremental index built: scanned {scanned_count} modules in {elapsed:.2f}s"
        )
    
    # Update config module variable
    _set_symbol_index_built(True)
    return True


def _remove_package_symbols(package_name: str) -> None:
    """Remove all symbols from a specific package from the cache."""
    global _SYMBOL_CACHE, _STDLIB_SYMBOL_CACHE, _THIRD_PARTY_SYMBOL_CACHE
    
    # Remove from main cache
    to_remove = []
    for symbol, locations in _SYMBOL_CACHE.items():
        filtered = [loc for loc in locations if not loc[0].startswith(package_name + '.') and loc[0] != package_name]
        if filtered:
            _SYMBOL_CACHE[symbol] = filtered
        else:
            to_remove.append(symbol)
    
    for symbol in to_remove:
        del _SYMBOL_CACHE[symbol]
    
    # Remove from stdlib cache
    to_remove = []
    for symbol, locations in _STDLIB_SYMBOL_CACHE.items():
        filtered = [loc for loc in locations if not loc[0].startswith(package_name + '.') and loc[0] != package_name]
        if filtered:
            _STDLIB_SYMBOL_CACHE[symbol] = filtered
        else:
            to_remove.append(symbol)
    
    for symbol in to_remove:
        del _STDLIB_SYMBOL_CACHE[symbol]
    
    # Remove from third-party cache
    to_remove = []
    for symbol, locations in _THIRD_PARTY_SYMBOL_CACHE.items():
        filtered = [loc for loc in locations if not loc[0].startswith(package_name + '.') and loc[0] != package_name]
        if filtered:
            _THIRD_PARTY_SYMBOL_CACHE[symbol] = filtered
        else:
            to_remove.append(symbol)
    
    for symbol in to_remove:
        del _THIRD_PARTY_SYMBOL_CACHE[symbol]


def build_symbol_index_incremental() -> bool:
    """Public API for incremental symbol index build.
    
    Returns:
        True if incremental build was successful, False otherwise
    """
    return _build_incremental_symbol_index()


# ============== Module Skip Configuration API ==============

def get_module_skip_config() -> Dict[str, Any]:
    """Get current module skip configuration."""
    return dict(_MODULE_SKIP_CONFIG)


def set_module_skip_config(
    skip_test_modules: Optional[bool] = None,
    skip_internal_modules: Optional[bool] = None,
    skip_large_modules: Optional[bool] = None,
    large_module_threshold: Optional[int] = None,
) -> None:
    """Configure module skip settings."""
    if skip_test_modules is not None:
        _MODULE_SKIP_CONFIG["skip_test_modules"] = skip_test_modules
    if skip_internal_modules is not None:
        _MODULE_SKIP_CONFIG["skip_internal_modules"] = skip_internal_modules
    if skip_large_modules is not None:
        _MODULE_SKIP_CONFIG["skip_large_modules"] = skip_large_modules
    if large_module_threshold is not None:
        _MODULE_SKIP_CONFIG["large_module_threshold"] = large_module_threshold
